# ui/utils/validators.py
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match((email or "").strip().lower()))


def emails_match(email1: str, email2: str) -> bool:
    return (email1 or "").strip().lower() == (email2 or "").strip().lower()


def passwords_match(pw1: str, pw2: str) -> bool:
    return (pw1 or "") == (pw2 or "")


def is_strong_password(pw: str) -> bool:
    pw = pw or ""
    if len(pw) < 8:
        return False
    has_letter = any(c.isalpha() for c in pw)
    has_digit = any(c.isdigit() for c in pw)
    return has_letter and has_digit

