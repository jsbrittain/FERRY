import uuid
from unittest.mock import MagicMock

from app.models.audit_event import SYSTEM_USER_ID, WORKER_USER_ID
from app.models.user import User, UserRole
from app.services.auth_framework_seeder import _seed_system_users


class TestSystemUserUUIDs:
    def test_system_user_id_is_fixed(self):
        assert SYSTEM_USER_ID == uuid.UUID("00000000-0000-0000-0000-000000000001")

    def test_worker_user_id_is_fixed(self):
        assert WORKER_USER_ID == uuid.UUID("00000000-0000-0000-0000-000000000002")

    def test_uuids_are_distinct(self):
        assert SYSTEM_USER_ID != WORKER_USER_ID


class TestSeedSystemUsers:
    def test_creates_system_users(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        assert db.add.call_count == 2

        users = [call[0][0] for call in db.add.call_args_list]
        user_ids = {u.id for u in users}
        assert SYSTEM_USER_ID in user_ids
        assert WORKER_USER_ID in user_ids

    def test_system_user_has_no_password(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users = [call[0][0] for call in db.add.call_args_list]
        for u in users:
            assert u.password_hash == ""

    def test_system_user_has_maintainer_role(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users = [call[0][0] for call in db.add.call_args_list]
        for u in users:
            assert u.role == UserRole.MAINTAINER

    def test_system_user_has_no_capabilities(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users = [call[0][0] for call in db.add.call_args_list]
        for u in users:
            assert u.advanced_capabilities == []

    def test_system_user_uses_well_known_id(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users = [call[0][0] for call in db.add.call_args_list]
        added_ids = {u.id for u in users}
        assert added_ids == {SYSTEM_USER_ID, WORKER_USER_ID}

    def test_idempotent_does_not_create_duplicates(self):
        db = MagicMock()
        # Simulate both users already existing
        existing_user = MagicMock(spec=User)
        existing_user.id = SYSTEM_USER_ID
        db.query.return_value.filter.return_value.first.side_effect = [
            existing_user,
            existing_user,
        ]

        _seed_system_users(db)

        db.add.assert_not_called()

    def test_system_user_email_unique(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users = [call[0][0] for call in db.add.call_args_list]
        emails = {u.email for u in users}
        assert len(emails) == 2  # unique
        assert "system@ferry.internal" in emails
        assert "execution_worker@ferry.internal" in emails

    def test_system_user_display_name(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        _seed_system_users(db)

        users_by_id = {u.id: u for call in db.add.call_args_list for u in [call[0][0]]}
        assert users_by_id[SYSTEM_USER_ID].display_name == "System"
        assert users_by_id[WORKER_USER_ID].display_name == "Execution Worker"
