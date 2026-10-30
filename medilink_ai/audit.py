"""Tamper-evident audit trail: AI_REQUEST -> AI_OUTPUT -> HUMAN_ACTION, hash-chained."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import threading
import time
import uuid


class AuditLog:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.lock = threading.Lock()
        self.db.execute("""CREATE TABLE IF NOT EXISTS audit(
            seq INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT, ts REAL, kind TEXT,
            user_id TEXT, patient_id TEXT, payload TEXT, prev_hash TEXT, hash TEXT)""")
        self.db.commit()

    @staticmethod
    def new_request_id() -> str:
        return uuid.uuid4().hex[:12]

    def _last_hash(self) -> str:
        row = self.db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        return row[0] if row else "GENESIS"

    def write(self, request_id: str, kind: str, user_id: str, patient_id: str | None, payload: dict) -> None:
        with self.lock:
            prev, ts, body = self._last_hash(), time.time(), json.dumps(payload, sort_keys=True)
            digest = hashlib.sha256(f"{prev}|{request_id}|{ts}|{kind}|{user_id}|{patient_id}|{body}".encode()).hexdigest()
            self.db.execute("INSERT INTO audit(request_id,ts,kind,user_id,patient_id,payload,prev_hash,hash) "
                            "VALUES(?,?,?,?,?,?,?,?)", (request_id, ts, kind, user_id, patient_id, body, prev, digest))
            self.db.commit()

    def write_output(self, request_id: str, user_id: str, patient_id: str | None, output: str) -> None:
        """Audit that output existed without copying clinical text into a second store."""
        self.write(request_id, "AI_OUTPUT", user_id, patient_id, {
            "sha256": hashlib.sha256(output.encode("utf-8")).hexdigest(),
            "characters": len(output),
        })

    def get_request(self, request_id: str):
        row = self.db.execute("SELECT user_id, patient_id FROM audit WHERE request_id=? AND kind='AI_REQUEST'",
                              (request_id,)).fetchone()
        return {"user_id": row[0], "patient_id": row[1]} if row else None

    def verify_chain(self) -> bool:
        prev = "GENESIS"
        for rid, ts, kind, uid, pid, body, p, h in self.db.execute(
                "SELECT request_id,ts,kind,user_id,patient_id,payload,prev_hash,hash FROM audit ORDER BY seq"):
            expect = hashlib.sha256(f"{prev}|{rid}|{ts}|{kind}|{uid}|{pid}|{body}".encode()).hexdigest()
            if p != prev or h != expect:
                return False
            prev = h
        return True
