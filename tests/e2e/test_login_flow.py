import pytest
pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect


@pytest.mark.e2e
def test_login_page_renders_and_has_tabs(goto_app, page):
    goto_app("/")

    expect(page.get_by_text("Sign In to Smart Energy")).to_be_visible(timeout=15000)
    expect(page.get_by_role("tab", name="Login")).to_be_visible()
    expect(page.get_by_role("tab", name="Register")).to_be_visible()


@pytest.mark.e2e
def test_login_tab_has_inputs_and_buttons(goto_app, page):
    goto_app("/")

    page.get_by_role("tab", name="Login").click()

    # visible-only inputs (Streamlit keeps hidden tab in DOM)
    email = page.locator("input[placeholder='user@example.com']:visible").first
    pw = page.locator("input[placeholder='password']:visible").first

    expect(email).to_be_visible(timeout=10000)
    expect(pw).to_be_visible(timeout=10000)

    email.fill("someone@example.com")
    pw.fill("password123")

    # Buttons inside the visible Login panel
    panel = page.get_by_role("tabpanel").locator(":visible").first
    expect(panel.get_by_role("button", name="LOGIN").first).to_be_visible()
    expect(panel.get_by_role("button", name="Forgot password?").first).to_be_visible()


@pytest.mark.e2e
def test_forgot_password_expander_opens(goto_app, page):
    goto_app("/")
    page.get_by_role("tab", name="Login").click()

    panel = page.get_by_role("tabpanel").locator(":visible").first
    panel.get_by_role("button", name="Forgot password?").first.click()

    expect(page.get_by_text("Reset your password")).to_be_visible(timeout=10000)
    expect(page.get_by_text("Send reset link")).to_be_visible(timeout=10000)
