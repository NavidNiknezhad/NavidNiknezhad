from __future__ import annotations

import re
from typing import Iterable, List

from .models import JobPosting, MatchResult, ResumeProfile

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,30}")


def tokenize(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def match_posting_to_resumes(
    posting: JobPosting,
    resumes: Iterable[ResumeProfile],
) -> MatchResult:
    jd_tokens = set(tokenize(posting.description + " " + posting.title))
    best: MatchResult | None = None

    for resume in resumes:
        keywords = {k.lower() for k in resume.focus_keywords}
        matched = sorted(keywords.intersection(jd_tokens))
        score = len(matched) / max(1, len(keywords))

        candidate = MatchResult(
            posting=posting,
            resume_key=resume.key,
            score=score,
            matched_keywords=matched,
        )
        if best is None or candidate.score > best.score:
            best = candidate

    if best is None:
        raise ValueError("No resume profiles provided.")

    return best
