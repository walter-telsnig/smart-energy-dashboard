from __future__ import annotations

from email.utils import parseaddr


def is_valid_email(email: str) -> bool:

    email = (email or "").strip()

    # parseaddr returns ("name", "addr"); addr is empty if it can't parse
    _, addr = parseaddr(email)
    if not addr or addr != email:
        return False

    # basic sanity checks
    if " " in addr:
        return False
    if addr.count("@") != 1:
        return False

    local, domain = addr.split("@", 1)
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False

    return True


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

