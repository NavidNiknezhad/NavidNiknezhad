from __future__ import annotations

import json
from pathlib import Path
from typing import List

from .models import ResumeProfile


def load_resume_profiles(path: Path) -> List[ResumeProfile]:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    profiles = [
        ResumeProfile(
            key=item["key"],
            file_path=item["file_path"],
            focus_keywords=item["focus_keywords"],
        )
        for item in payload["resumes"]
    ]
    return profiles
