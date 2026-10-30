"""Local hybrid knowledge search over approved hospital documents.

Keyword scoring remains the primary signal for predictable citations. A small
deterministic local embedding signal improves recall without sending policy
content outside the hospital or requiring a model download.
"""
from __future__ import annotations
import math
import re
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from .knowledge.embeddings import EmbeddingService

STOP = set("a an the of to for in on and or is are be what how do i we it this that with at by from as".split())
PRIVILEGED_ROLES = {"super_admin", "hospital_admin", "facility_admin", "tenant_admin", "administrator", "admin"}
CLINICAL_ROLES = PRIVILEGED_ROLES | {"doctor", "clinician", "nurse", "pharmacist", "laboratory", "radiologist"}


def tokenize(text: str) -> list:
    return [t for t in re.findall(r"\w+", text.lower()) if t not in STOP]


@dataclass
class Chunk:
    doc_title: str
    version: str
    text: str
    tokens: list
    allowed_roles: tuple = ("*",)
    facility_id: str = ""
    classification: str = "INTERNAL"
    source_filename: str = ""


class KnowledgeIndex:
    def __init__(self):
        self.chunks: list = []
        self.embedder = EmbeddingService()

    def load_dir(self, directory: str) -> int:
        for p in sorted(Path(directory).glob("*.md")):
            lines = p.read_text(encoding="utf-8").splitlines()
            title = lines[0].lstrip("# ").strip() if lines else p.stem
            version = next((l.split(":", 1)[1].strip() for l in lines[:5] if l.lower().startswith("version:")), "unversioned")
            metadata = {k.strip().lower(): v.strip() for line in lines[:20] if ":" in line for k, v in [line.split(":", 1)]}
            roles = tuple(role.strip().lower() for role in metadata.get("allowed_roles", "*").split(",") if role.strip()) or ("*",)
            facility_id = metadata.get("facility_id", "")
            classification = metadata.get("classification", "INTERNAL").upper()
            for para in re.split(r"\n\s*\n", "\n".join(lines[1:])):
                para = para.strip()
                if para and not para.lower().startswith("version:"):
                    self.chunks.append(Chunk(title, version, para, tokenize(para), roles, facility_id, classification, p.name))
        return len(self.chunks)

    def load_store(self, store_path: str) -> int:
        path = Path(store_path)
        if not path.exists():
            return 0
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0
        for record in records if isinstance(records, list) else []:
            metadata = record.get("metadata") or {}
            text = str(record.get("text") or "").strip()
            if not text:
                continue
            self.chunks.append(Chunk(
                metadata.get("title", "Untitled"), metadata.get("version", "unversioned"), text,
                tokenize(text), tuple(metadata.get("allowed_roles") or ["*"]),
                metadata.get("facility_id", ""), metadata.get("classification", "INTERNAL"),
                metadata.get("source_filename", ""),
            ))
        return len(self.chunks)

    def search(self, query: str, k: int = 4, role: str = "", facility_id: str | None = None):
        q, n = tokenize(query), len(self.chunks)
        if not q or not n:
            return []
        avg = sum(len(c.tokens) for c in self.chunks) / n
        df = Counter(t for c in self.chunks for t in set(c.tokens))
        scored = []
        normalized_role = role.lower()
        def permitted_classification(chunk: Chunk) -> bool:
            level = chunk.classification.upper()
            if level == "RESTRICTED":
                return normalized_role in PRIVILEGED_ROLES
            if level == "CONFIDENTIAL":
                return normalized_role in CLINICAL_ROLES
            return True

        permitted = [c for c in self.chunks if ("*" in c.allowed_roles or normalized_role in c.allowed_roles)
                     and permitted_classification(c)
                     and (not c.facility_id or c.facility_id == (facility_id or ""))]
        for c in permitted:
            tf, score = Counter(c.tokens), 0.0
            for t in q:
                if t in tf:
                    idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                    score += idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(c.tokens) / avg))
            if score > 0:
                # Keep keyword relevance dominant while allowing semantically
                # related wording to rank above an exact but weak match.
                semantic = self.embedder.similarity(query, c.text)
                scored.append((0.75 * score + 0.25 * semantic, c))
        return sorted(scored, key=lambda x: -x[0])[:k]
