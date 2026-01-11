import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_register_tab_has_fields(goto_app, page):
    goto_app("/")
    page.get_by_role("tab", name="Register").click()

    panel = page.get_by_role("tabpanel").locator(":visible").first

    expect(panel.locator("input[placeholder='Your name']:visible").first).to_be_visible(timeout=10000)
    expect(panel.locator("input[placeholder='user@example.com']:visible").first).to_be_visible(timeout=10000)
    expect(panel.locator("input[placeholder='Create a password']:visible").first).to_be_visible(timeout=10000)

    expect(panel.get_by_role("button", name="CREATE ACCOUNT").first).to_be_visible(timeout=10000)