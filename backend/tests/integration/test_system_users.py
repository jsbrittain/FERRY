"""Integration tests for system user seeding."""

from app.models.audit_event import SYSTEM_USER_ID, WORKER_USER_ID
from app.models.user import User, UserRole
from app.services.auth_framework_seeder import seed_auth_framework


class TestSystemUserSeeding:
    def test_system_users_created(self, db_session):
        seed_auth_framework(db_session)

        system_user = db_session.query(User).filter(User.id == SYSTEM_USER_ID).first()
        assert system_user is not None
        assert system_user.display_name == "System"
        assert system_user.password_hash == ""
        assert system_user.role == UserRole.MAINTAINER

        worker_user = db_session.query(User).filter(User.id == WORKER_USER_ID).first()
        assert worker_user is not None
        assert worker_user.display_name == "Execution Worker"
        assert worker_user.password_hash == ""
        assert worker_user.role == UserRole.MAINTAINER

    def test_system_users_have_no_capabilities(self, db_session):
        seed_auth_framework(db_session)

        system_user = db_session.query(User).filter(User.id == SYSTEM_USER_ID).first()
        assert system_user is not None
        assert system_user.advanced_capabilities == []

        worker_user = db_session.query(User).filter(User.id == WORKER_USER_ID).first()
        assert worker_user is not None
        assert worker_user.advanced_capabilities == []

    def test_seeding_is_idempotent(self, db_session):
        seed_auth_framework(db_session)
        seed_auth_framework(db_session)
        seed_auth_framework(db_session)

        count = (
            db_session.query(User)
            .filter(User.id.in_([SYSTEM_USER_ID, WORKER_USER_ID]))
            .count()
        )
        assert count == 2

    def test_system_users_cannot_authenticate(self, db_session, client):
        seed_auth_framework(db_session)

        emails = ["system@ferry.internal", "execution_worker@ferry.internal"]
        for email in emails:
            response = client.post(
                "/api/auth/login",
                json={"email": email, "password": ""},
            )
            assert response.status_code == 401, f"Expected 401 for {email}"
