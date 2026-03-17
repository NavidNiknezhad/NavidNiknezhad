from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass(slots=True)
class ResumeProfile:
    key: str
    file_path: str
    focus_keywords: List[str]


@dataclass(slots=True)
class JobPosting:
    source_email_id: str
    company: str
    title: str
    location: str
    apply_url: str
    description: str
    discovered_at: datetime


@dataclass(slots=True)
class MatchResult:
    posting: JobPosting
    resume_key: str
    score: float
    matched_keywords: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ApplicationPacket:
    posting: JobPosting
    resume_path: str
    cover_letter: str
    score: float
