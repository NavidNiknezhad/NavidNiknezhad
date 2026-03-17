from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .config import load_settings
from .cover_letter import render_cover_letter
from .email_ingest import EmailIngestionError, fetch_recommended_jobs
from .matcher import match_posting_to_resumes
from .models import ApplicationPacket
from .resume_selector import load_resume_profiles
from .storage import already_processed, init_db, store_application


def build_packets(resume_manifest: Path, cover_letter_template: Path) -> int:
    settings = load_settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    init_db(settings.database_path)

    resumes = load_resume_profiles(resume_manifest)
    postings = fetch_recommended_jobs(
        imap_host=settings.imap_host,
        username=settings.imap_username,
        password=settings.imap_password,
        folder=settings.email_folder,
    )

    shortlist_path = settings.output_dir / "daily_shortlist.csv"
    created = 0

    with shortlist_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "email_id",
                "company",
                "title",
                "apply_url",
                "match_score",
                "resume_key",
                "resume_path",
                "cover_letter_path",
            ],
        )
        writer.writeheader()

        for posting in postings:
            if already_processed(settings.database_path, posting.source_email_id):
                continue

            match = match_posting_to_resumes(posting, resumes)
            if match.score < settings.min_match_score:
                continue

            resume = next(r for r in resumes if r.key == match.resume_key)
            cover_letter = render_cover_letter(
                cover_letter_template,
                posting=posting,
                candidate_name="Your Name",
                candidate_summary=(
                    "I ship production software quickly and have strong alignment with "
                    + ", ".join(match.matched_keywords[:8])
                ),
            )
            packet_dir = settings.output_dir / f"{posting.source_email_id}_{resume.key}"
            packet_dir.mkdir(parents=True, exist_ok=True)
            cover_letter_path = packet_dir / "cover_letter.md"
            cover_letter_path.write_text(cover_letter, encoding="utf-8")

            packet = ApplicationPacket(
                posting=posting,
                resume_path=resume.file_path,
                cover_letter=cover_letter,
                score=match.score,
            )

            store_application(settings.database_path, packet, cover_letter_path)

            writer.writerow(
                {
                    "email_id": posting.source_email_id,
                    "company": posting.company,
                    "title": posting.title,
                    "apply_url": posting.apply_url,
                    "match_score": f"{match.score:.2f}",
                    "resume_key": resume.key,
                    "resume_path": resume.file_path,
                    "cover_letter_path": str(cover_letter_path),
                }
            )
            created += 1

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Daily job-application packet builder")
    parser.add_argument(
        "--resume-manifest",
        type=Path,
        default=Path("resume_manifest.example.json"),
        help="JSON file describing resume variants and keywords",
    )
    parser.add_argument(
        "--cover-letter-template",
        type=Path,
        default=Path("job_apply_bot/templates/cover_letter.template.md"),
        help="Template used to generate tailored cover letters",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        count = build_packets(args.resume_manifest, args.cover_letter_template)
    except EmailIngestionError as exc:
        print(f"[error] {exc}")
        return 1

    print(f"Built {count} application packet(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
