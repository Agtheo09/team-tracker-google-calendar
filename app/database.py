from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                event_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_id TEXT NOT NULL,
                calendar_id TEXT NOT NULL,
                google_event_id TEXT NOT NULL,
                payload_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def get_google_event_id(self, event_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT google_event_id FROM sync_state WHERE event_id = ?", (event_id,)
        ).fetchone()
        return row[0] if row else None

    def upsert(
        self,
        *,
        event_id: str,
        source: str,
        source_id: str,
        calendar_id: str,
        google_event_id: str,
        payload_hash: str,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO sync_state(event_id, source, source_id, calendar_id, google_event_id, payload_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                google_event_id=excluded.google_event_id,
                payload_hash=excluded.payload_hash,
                updated_at=CURRENT_TIMESTAMP
            """,
            (event_id, source, source_id, calendar_id, google_event_id, payload_hash),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
