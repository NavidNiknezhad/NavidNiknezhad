from __future__ import annotations

import email
import imaplib
import re
from datetime import datetime
from email.message import Message
from html import unescape
from typing import List

from .models import JobPosting

RECOMMENDATION_SUBJECT_PATTERN = re.compile(
    r"(recommended\s+job|you\s+may\s+be\s+a\s+great\s+fit|strong\s+applicant)",
    re.IGNORECASE,
)
URL_PATTERN = re.compile(r"https?://[^\s)\]>\"']+")


class EmailIngestionError(RuntimeError):
    pass


def _extract_text_from_message(message: Message) -> str:
    if message.is_multipart():
        parts = []
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type in {"text/plain", "text/html"}:
                payload = part.get_payload(decode=True)
                if payload:
                    parts.append(payload.decode(errors="ignore"))
        content = "\n".join(parts)
    else:
        payload = message.get_payload(decode=True)
        content = payload.decode(errors="ignore") if payload else ""
    content = re.sub(r"<[^>]+>", " ", content)
    return unescape(re.sub(r"\s+", " ", content)).strip()


def _extract_first_url(content: str) -> str:
    match = URL_PATTERN.search(content)
    return match.group(0) if match else ""


def _extract_company(subject: str, content: str) -> str:
    patterns = [
        re.compile(r"at\s+([A-Z][A-Za-z0-9&\-\s]{1,50})"),
        re.compile(r"Company[:\-]\s*([A-Za-z0-9&\-\s]{2,60})", re.IGNORECASE),
    ]
    for pattern in patterns:
        for source in (subject, content):
            match = pattern.search(source)
            if match:
                return match.group(1).strip()
    return "Unknown Company"


def fetch_recommended_jobs(
    imap_host: str,
    username: str,
    password: str,
    folder: str = "INBOX",
    limit: int = 30,
) -> List[JobPosting]:
    if not username or not password:
        raise EmailIngestionError("Missing IMAP credentials.")

    postings: List[JobPosting] = []
    mail = imaplib.IMAP4_SSL(imap_host)
    try:
        mail.login(username, password)
        mail.select(folder)
        status, data = mail.search(None, "ALL")
        if status != "OK":
            raise EmailIngestionError("Failed to search inbox.")

        ids = data[0].split()[-limit:]
        for email_id in reversed(ids):
            status, fetched = mail.fetch(email_id, "(RFC822)")
            if status != "OK" or not fetched or not fetched[0]:
                continue

            raw_email = fetched[0][1]
            message = email.message_from_bytes(raw_email)
            subject = message.get("Subject", "")
            if not RECOMMENDATION_SUBJECT_PATTERN.search(subject):
                continue

            content = _extract_text_from_message(message)
            apply_url = _extract_first_url(content)
            title = subject[:120] if subject else "Recommended role"
            postings.append(
                JobPosting(
                    source_email_id=email_id.decode(),
                    company=_extract_company(subject, content),
                    title=title,
                    location="Unknown",
                    apply_url=apply_url,
                    description=content,
                    discovered_at=datetime.utcnow(),
                )
            )
    finally:
        try:
            mail.logout()
        except Exception:
            pass

    return postings
