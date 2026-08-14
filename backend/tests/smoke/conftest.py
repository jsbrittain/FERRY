import httpx
import pytest


@pytest.fixture(autouse=True, scope="session")
def require_stack():
    try:
        r = httpx.get(
            "https://localhost/api/health",
            verify=False,
            timeout=5,
        )
        if r.status_code != 200:
            pytest.skip("FERRY stack is not running")
    except Exception:
        pytest.skip("FERRY stack is not running")
