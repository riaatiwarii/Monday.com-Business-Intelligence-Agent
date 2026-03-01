from __future__ import annotations

import threading


class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: dict[str, dict] = {}

    def get(self, session_id: str) -> dict | None:
        with self._lock:
            return self._store.get(session_id)

    def set(self, session_id: str, payload: dict) -> None:
        with self._lock:
            self._store[session_id] = payload

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)


session_store = SessionStore()
