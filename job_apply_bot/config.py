from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    imap_host: str
    imap_username: str
    imap_password: str
    email_folder: str
    output_dir: Path
    database_path: Path
    min_match_score: float


def load_settings() -> Settings:
    base_dir = Path(os.getenv("JOB_BOT_BASE_DIR", ".")).resolve()
    output_dir = base_dir / os.getenv("JOB_BOT_OUTPUT_DIR", "generated_packets")
    database_path = base_dir / os.getenv("JOB_BOT_DB", "job_apply_bot.sqlite3")

    return Settings(
        imap_host=os.getenv("JOB_BOT_IMAP_HOST", "imap.gmail.com"),
        imap_username=os.getenv("JOB_BOT_IMAP_USERNAME", ""),
        imap_password=os.getenv("JOB_BOT_IMAP_PASSWORD", ""),
        email_folder=os.getenv("JOB_BOT_EMAIL_FOLDER", "INBOX"),
        output_dir=output_dir,
        database_path=database_path,
        min_match_score=float(os.getenv("JOB_BOT_MIN_MATCH_SCORE", "0.30")),
    )
