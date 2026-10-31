from __future__ import annotations

import hashlib
import hmac
import os


class AuditHashingError(Exception):
    pass


def _get_hashing_key() -> bytes:
    key = os.getenv("MEDILINK_AUDIT_HMAC_KEY")
    if not key:
        raise AuditHashingError("MEDILINK_AUDIT_HMAC_KEY is not configured.")
    if len(key) < 32:
        raise AuditHashingError("The audit HMAC key must contain at least 32 characters.")
    return key.encode("utf-8")


def hash_audit_reference(value: str | None, *, reference_type: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    message = f"{reference_type.upper()}:{normalized}".encode("utf-8")
    return hmac.new(_get_hashing_key(), message, hashlib.sha256).hexdigest()


def sha256_fingerprint(value: str | bytes | None) -> str | None:
    if value is None:
        return None
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
