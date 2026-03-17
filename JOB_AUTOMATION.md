# Daily Job Application Automation (MVP)

## 1) Problem Understanding
Automate a daily pipeline that:
1. scans recommendation emails,
2. identifies strong-fit jobs,
3. picks the most relevant resume variant,
4. generates a tailored cover letter,
5. outputs a reviewable shortlist before final submit.

## 2) Proposed Approach
Use a **single Python monolith** scheduled via cron (startup-friendly).
- Ingest job recommendation emails via IMAP.
- Parse JDs and score fit against keyword profiles per resume.
- Generate a tailored cover letter from a template.
- Persist processed jobs in SQLite for idempotency.
- Write daily shortlist CSV + cover-letter files for human review.

## 3) Architecture / Design

### Suggested folder structure
```txt
job_apply_bot/
  __init__.py
  main.py
  config.py
  models.py
  email_ingest.py
  matcher.py
  resume_selector.py
  cover_letter.py
  storage.py
  templates/
    cover_letter.template.md
resume_manifest.example.json
JOB_AUTOMATION.md
```

### Key interfaces
- `fetch_recommended_jobs(...) -> list[JobPosting]`
- `match_posting_to_resumes(posting, resumes) -> MatchResult`
- `render_cover_letter(template_path, posting, candidate_name, candidate_summary) -> str`
- `store_application(db_path, packet, cover_letter_path) -> None`

### Database schema
SQLite table `applications`:
- `email_id` (unique idempotency key)
- `company`, `title`, `apply_url`
- `resume_path`, `score`, `cover_letter_path`
- `created_at`

### Example API endpoints (for future web control plane)
- `POST /runs/daily` → trigger daily run
- `GET /runs/:id/shortlist` → get run output
- `POST /applications/:id/approve` → mark approved for auto-submit
- `POST /applications/:id/reject` → skip

### Infrastructure components
- cron / GitHub Actions scheduled workflow
- Python runtime
- SQLite (MVP) → Postgres at growth stage
- Secret storage via env vars (`JOB_BOT_IMAP_PASSWORD`)

### Recommended libraries
- Standard library now (`imaplib`, `email`, `sqlite3`, `argparse`)
- Optional upgrade: `mail-parser`, `rapidfuzz`, `pydantic`, `SQLAlchemy`

## 4) Implementation

### Run locally
```bash
python -m job_apply_bot.main \
  --resume-manifest resume_manifest.example.json \
  --cover-letter-template job_apply_bot/templates/cover_letter.template.md
```

### Required environment variables
- `JOB_BOT_IMAP_HOST` (default `imap.gmail.com`)
- `JOB_BOT_IMAP_USERNAME`
- `JOB_BOT_IMAP_PASSWORD`
- `JOB_BOT_EMAIL_FOLDER` (default `INBOX`)
- `JOB_BOT_MIN_MATCH_SCORE` (default `0.30`)

### Daily schedule (cron)
```cron
0 7 * * * cd /path/to/repo && /usr/bin/python3 -m job_apply_bot.main >> job_bot.log 2>&1
```

## 5) Improvements / Scaling

### Scalability risks
- IMAP polling + regex parsing degrades as inbox volume grows.
- Keyword-only matcher has quality ceiling.

### Failure points
- Email parsing failures on complex HTML.
- Provider auth breakage (2FA/app-password).
- Duplicate job links across emails.

### Security concerns
- Email credentials in env vars; store in a secrets manager.
- Potential prompt/data leakage if integrating LLM later.
- Add URL allowlist before any auto-apply action.

### Performance bottlenecks
- Linear JD keyword matching across many resume profiles.
- Single-process run for large queues.

### Operational complexity
- Cron observability is weak without structured logs/alerts.
- Need explicit human approval gate before submitting applications.

## 10x scaling upgrade path
If you need >10x scale:
- Move to modular monolith service with Postgres + Redis queue.
- Add worker pool (`RQ`/`Celery`) for parsing/scoring/generation.
- Add embeddings-based JD-to-resume matching.
- Add provider adapters (Greenhouse/Lever/Workday) behind a unified `ApplicationProvider` interface.
- Add OpenTelemetry traces + Prometheus metrics + Slack alerts.
