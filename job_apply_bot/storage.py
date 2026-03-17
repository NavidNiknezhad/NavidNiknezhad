from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import ApplicationPacket


SCHEMA = """
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email_id TEXT NOT NULL UNIQUE,
    company TEXT NOT NULL,
    title TEXT NOT NULL,
    apply_url TEXT,
    resume_path TEXT NOT NULL,
    score REAL NOT NULL,
    cover_letter_path TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def init_db(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(SCHEMA)
        conn.commit()


def already_processed(db_path: Path, email_id: str) -> bool:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM applications WHERE email_id = ? LIMIT 1", (email_id,)
        ).fetchone()
    return row is not None


def store_application(db_path: Path, packet: ApplicationPacket, cover_letter_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO applications (email_id, company, title, apply_url, resume_path, score, cover_letter_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                packet.posting.source_email_id,
                packet.posting.company,
                packet.posting.title,
                packet.posting.apply_url,
                packet.resume_path,
                packet.score,
                str(cover_letter_path),
            ),
        )
        conn.commit()
