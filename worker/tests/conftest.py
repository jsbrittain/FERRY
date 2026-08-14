"""Shared fixtures for the worker integration test suite.

All tests use the ferry_test database (same as backend integration
tests), require PostgreSQL to be running, and mock only Docker.
"""

import os
import tempfile
import uuid

# Must be set before any application imports so that Settings() picks
# up the test database and test-only configuration.
os.environ.setdefault("POSTGRES_PASSWORD", "test-pw")
os.environ["POSTGRES_DB"] = "ferry_test"
os.environ.setdefault("REDIS_PASSWORD", "test-redis")
os.environ["REDIS_DB"] = "1"
os.environ.setdefault("SECRET_KEY", "a" * 32)
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-pw")
os.environ.setdefault("AUTO_REGISTER_RESOURCES", "false")
_tmp = tempfile.gettempdir()
os.environ.setdefault("BUNDLE_STORE_DIR", f"{_tmp}/ferry-wtest-bundles")
os.environ.setdefault("OUTPUT_DIR", f"{_tmp}/ferry-wtest-outputs")
os.environ.setdefault("RELEASE_DIR", f"{_tmp}/ferry-wtest-releases")

import pytest
from sqlalchemy import text

from app.db.base import Base
from app.db.migration import ensure_migrated
from app.db.session import SessionLocal, engine
from app.models.analysis_bundle import (
    AnalysisBundle,
    AnalysisBundleBuildStatus,
    AnalysisBundleStatus,
)
from app.models.audit_event import SYSTEM_USER_ID, WORKER_USER_ID
from app.models.data_resource import DataResource
from app.models.execution_environment import ExecutionEnvironment
from app.models.execution_image import ExecutionImage
from app.models.execution_request import ExecutionRequest, ExecutionRequestStatus
from app.models.output_set import OutputSet
from app.models.project import Project
from app.models.project_membership import ProjectMembership
from app.models.user import User, UserRole
from app.services.auth_framework_seeder import seed_auth_framework


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    ensure_migrated()
    session = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        seed_auth_framework(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))
        for name in [
            "user_role",
            "analysis_bundle_status",
            "analysis_bundle_build_status",
            "build_strategy",
            "execution_request_status",
            "output_set_status",
            "build_request_status",
            "validation_request_status",
            "ai_bundle_review_status",
            "ai_output_set_review_status",
            "audit_event_type",
            "platform_setting_key",
            "capability",
        ]:
            conn.execute(text(f"DROP TYPE IF EXISTS {name} CASCADE"))


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    session = SessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    finally:
        session.close()


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        seed_auth_framework(session)
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Model fixtures
# ---------------------------------------------------------------------------

_TEST_USER_ID = uuid.uuid4()


@pytest.fixture
def worker_test_user(db_session):
    user = User(
        id=_TEST_USER_ID,
        email="worker-test@test.local",
        display_name="Worker Test",
        password_hash="",
        role=UserRole.MAINTAINER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def project(db_session, worker_test_user):
    p = Project(name="Worker Test Project", owner_id=worker_test_user.id)
    db_session.add(p)
    db_session.flush()
    db_session.add(
        ProjectMembership(
            project_id=p.id,
            user_id=worker_test_user.id,
            created_by_id=worker_test_user.id,
        )
    )
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def execution_environment(db_session):
    env = ExecutionEnvironment(
        identifier="python-3.13-test",
        name="Python 3.13 Test",
        runtime="python-3.13",
        description="Test environment",
        status="active",
        image_reference="python:3.13-slim",
    )
    db_session.add(env)
    db_session.commit()
    db_session.refresh(env)
    return env


@pytest.fixture
def execution_image(db_session, execution_environment):
    img = ExecutionImage(
        execution_environment_id=execution_environment.id,
        dependency_hash="a" * 64,
        image_reference="python:3.13-slim",
        builder_type="python",
    )
    db_session.add(img)
    db_session.commit()
    db_session.refresh(img)
    return img


@pytest.fixture
def resource(db_session):
    r = DataResource(
        identifier="test-data",
        name="Test Data",
        alias="test_data",
        provider_type="csv",
        endpoint={"path": "data.csv"},
        version="1.0.0",
        status="active",
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


@pytest.fixture
def analysis_dir(tmp_path):
    d = tmp_path / "analysis"
    d.mkdir(parents=True)
    (d / "run.py").write_text("print('hello')")
    return d
