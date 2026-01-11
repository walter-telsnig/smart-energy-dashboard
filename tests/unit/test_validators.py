from ui.utils.validators import (
    is_valid_email,
    emails_match,
    passwords_match,
    is_strong_password,
)

def test_is_valid_email_ok():
    assert is_valid_email("user@example.com")
    assert is_valid_email("USER@Example.com")

def test_is_valid_email_bad():
    assert not is_valid_email("userexample.com")
    assert not is_valid_email("user@")
    assert not is_valid_email("")

def test_emails_match():
    assert emails_match("a@b.com", "A@B.COM")
    assert not emails_match("a@b.com", "c@d.com")

def test_passwords_match():
    assert passwords_match("abc", "abc")
    assert not passwords_match("abc", "abcd")

def test_is_strong_password():
    assert is_strong_password("abcd1234")
    assert is_strong_password("A1b2c3d4")
    assert not is_strong_password("short1")
    assert not is_strong_password("onlyletters")
    assert not is_strong_password("12345678")