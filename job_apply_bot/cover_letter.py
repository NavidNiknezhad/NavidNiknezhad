from __future__ import annotations

from pathlib import Path
from string import Template

from .models import JobPosting


def render_cover_letter(
    template_path: Path,
    posting: JobPosting,
    candidate_name: str,
    candidate_summary: str,
) -> str:
    raw_template = template_path.read_text(encoding="utf-8")
    template = Template(raw_template)
    return template.substitute(
        candidate_name=candidate_name,
        company=posting.company,
        role=posting.title,
        location=posting.location,
        job_url=posting.apply_url or "N/A",
        candidate_summary=candidate_summary,
    )
