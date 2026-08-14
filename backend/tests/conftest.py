import os
import tempfile

os.environ.setdefault("POSTGRES_PASSWORD", "test-pw")
os.environ["POSTGRES_DB"] = "ferry_test"
os.environ.setdefault("REDIS_PASSWORD", "test-redis")
os.environ["REDIS_DB"] = "1"
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-pw")
os.environ.setdefault("AUTO_REGISTER_RESOURCES", "false")
_tmp = tempfile.gettempdir()
os.environ.setdefault("BUNDLE_STORE_DIR", f"{_tmp}/ferry-test-bundles")
os.environ.setdefault("OUTPUT_DIR", f"{_tmp}/ferry-test-outputs")
os.environ.setdefault("RELEASE_DIR", f"{_tmp}/ferry-test-releases")
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)
