"""Local inference clients. The gateway refuses any endpoint that is not on the hospital network."""
from __future__ import annotations
import ipaddress
import re
from typing import Protocol
from urllib.parse import urlparse

import httpx


class EgressBlocked(Exception):
    pass


class ModelUnavailableError(Exception):
    """The configured on-premise inference runtime cannot be reached."""
    pass


def assert_local_endpoint(url: str, allowed_hosts: tuple = ()) -> None:
    """Hard rule: no mandatory external AI API. Only loopback, private IPs or allow-listed hosts."""
    host = urlparse(url).hostname or ""
    if host in allowed_hosts or host == "localhost":
        return
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        raise EgressBlocked(f"Host '{host}' is not allow-listed; refusing to send PHI-derived context.")
    if not (ip.is_loopback or ip.is_private):
        raise EgressBlocked(f"Host '{host}' is a public address; refusing.")


class LLM(Protocol):
    name: str

    def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str: ...


class OpenAICompatLLM:
    def __init__(self, base_url: str, model: str, allowed_hosts: tuple = (), timeout: float = 120.0):
        assert_local_endpoint(base_url, allowed_hosts)
        self.base_url, self.model, self.timeout = base_url.rstrip("/"), model, timeout
        self.name = model

    def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str:
        try:
            r = httpx.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model": self.model,
                    "temperature": temperature,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, TypeError, ValueError, IndexError) as exc:
            raise ModelUnavailableError("The local AI model is unavailable.") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailableError("The local AI model returned an empty response.")
        return content


class OllamaLLM:
    """Client for Ollama's local native chat API.

    No remote endpoint can be used: the constructor applies the same private
    network restriction as every other inference adapter.
    """
    def __init__(
        self,
        base_url: str,
        model: str,
        allowed_hosts: tuple = (),
        timeout: float = 120.0,
        keep_alive: str = "10m",
        num_ctx: int = 1024,
        num_predict: int = 512,
        num_thread: int = 4,
    ):
        assert_local_endpoint(base_url, allowed_hosts)
        self.base_url, self.model, self.timeout = base_url.rstrip("/"), model, timeout
        self.keep_alive, self.num_ctx = keep_alive, num_ctx
        self.num_predict, self.num_thread = num_predict, num_thread
        self.name = model

    def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str:
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "keep_alive": self.keep_alive,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": self.num_ctx,
                        "num_predict": self.num_predict,
                        "num_thread": self.num_thread,
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["message"]["content"]
            if payload.get("done") is not True:
                raise ValueError("Ollama did not complete the response")
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise ModelUnavailableError("The local Ollama model is unavailable.") from exc
        if not isinstance(content, str) or not content.strip():
            raise ModelUnavailableError("The local Ollama model returned an empty response.")
        return content


class MockLLM:
    """Deterministic, extractive stand-in for tests and for running without a GPU."""
    name = "mock-extractive"

    def generate(self, system: str, prompt: str, temperature: float = 0.1) -> str:
        if "SOURCES:" in prompt:
            lines = re.findall(r"^\[(S\d+)\] (.+)$", prompt, flags=re.M)
            return "SUMMARY\n" + "\n".join(f"- {text} [{sid}]" for sid, text in lines)
        if "TRANSCRIPT:" in prompt:
            transcript = prompt.split("TRANSCRIPT:", 1)[1].strip()
            sections = ["Chief Complaint", "History of Present Illness", "Past Medical History",
                        "Medication History", "Allergies", "Examination", "Assessment", "Plan"]
            body = {s: "Not documented in dictation." for s in sections}
            body["History of Present Illness"] = transcript
            return "\n\n".join(f"{s}\n{t}" for s, t in body.items())
        # Knowledge prompts use the same extractive fallback in both the
        # legacy JSON path and the current authorized-evidence path. Keeping
        # this deterministic makes local testing useful without Ollama.
        if "AUTHORIZED EVIDENCE:" in prompt or "DOCUMENTS:" in prompt:
            docs = re.findall(
                r"^\[(D\d+)\]\s+(.+?)\s+\|\s+(.*?)(?=^\[D\d+\]|\Z)",
                prompt,
                flags=re.M | re.S,
            )
            if docs:
                did, reference, text = docs[0]
                # Evidence paragraphs may retain Markdown headings. Do not
                # mistake a heading for the answer when exercising the local
                # deterministic model.
                body = re.sub(r"(?m)^\s*#+\s*[^\n]*\n?", "", text).strip()
                sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", body) if part.strip()]
                answer = " ".join(sentences[:2]).rstrip(".") or body
                return f"According to {reference}: {answer}. [{did}]"
        return "No output."
