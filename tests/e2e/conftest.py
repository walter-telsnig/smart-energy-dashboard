import os
import subprocess
import time
import requests
import pytest

UI_PORT = int(os.getenv("UI_PORT", "8501"))
BASE_URL = os.getenv("UI_BASE_URL", f"http://127.0.0.1:{UI_PORT}")
STREAMLIT_APP = os.getenv("STREAMLIT_APP", "ui/app.py")


def _wait_until_up(url: str, timeout_s: int = 30) -> None:
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code in (200, 302):
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Streamlit not reachable at {url} after {timeout_s}s")


@pytest.fixture(scope="session", autouse=True)
def streamlit_server():
    """
    Starts Streamlit once per test session.
    """
    cmd = [
        "python",
        "-m",
        "streamlit",
        "run",
        STREAMLIT_APP,
        "--server.headless=true",
        f"--server.port={UI_PORT}",
        "--server.address=127.0.0.1",
    ]

    # Start streamlit in background
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_until_up(BASE_URL, timeout_s=45)
        yield
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()


@pytest.fixture(scope="session")
def base_url() -> str:
    return BASE_URL


@pytest.fixture()
def goto_app(page, base_url: str):
    def _goto(path: str = "/"):
        page.goto(base_url + path, wait_until="domcontentloaded")
        page.wait_for_timeout(400)
    return _goto
