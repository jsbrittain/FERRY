import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.services.audit_service import query_audit_events


class TestQueryAuditEvents:
    def _make_mock_row(self, **overrides):
        row = MagicMock()
        row.id = overrides.get("id", uuid.uuid4())
        row.event_type = overrides.get("event_type", "project.created")
        row.actor_id = overrides.get("actor_id", uuid.uuid4())
        row.actor_display_name = overrides.get("actor_display_name", "Alice")
        row.actor_email = overrides.get("actor_email", "alice@example.com")
        row.project_id = overrides.get("project_id", uuid.uuid4())
        row.resource_type = overrides.get("resource_type", "project")
        row.resource_id = overrides.get("resource_id", uuid.uuid4())
        row.event_metadata = overrides.get("event_metadata", {})
        row.occurred_at = overrides.get("occurred_at", datetime.now(timezone.utc))
        return row

    def _setup_base_mock(self, db, count=0):
        query = db.query.return_value
        joined = query.join.return_value
        joined.filter.return_value = joined
        joined.count.return_value = count
        chained = joined.order_by.return_value.offset.return_value.limit.return_value
        chained.all.return_value = []
        return joined, chained

    def test_default_query(self):
        db = MagicMock()
        joined, chained = self._setup_base_mock(db, count=1)
        chained.all.return_value = [self._make_mock_row()]

        items, total = query_audit_events(db)

        assert total == 1
        assert len(items) == 1
        assert items[0]["event_type"] == "project.created"

    def test_filter_by_project_id(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(db, project_id=uuid.uuid4())
        db.query.return_value.join.return_value.filter.assert_called()

    def test_filter_by_event_type(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(db, event_type="bundle.approved")
        db.query.return_value.join.return_value.filter.assert_called()

    def test_filter_by_actor_id(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(db, actor_id=uuid.uuid4())
        db.query.return_value.join.return_value.filter.assert_called()

    def test_filter_by_resource_type_and_id(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(
            db, resource_type="analysis_bundle", resource_id=uuid.uuid4()
        )
        db.query.return_value.join.return_value.filter.assert_called()

    def test_filter_by_date_range(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(
            db,
            date_from=datetime(2026, 1, 1, tzinfo=timezone.utc),
            date_to=datetime(2026, 6, 30, tzinfo=timezone.utc),
        )
        db.query.return_value.join.return_value.filter.assert_called()

    def test_pagination(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(db, limit=10, offset=20)

        order_mock = db.query.return_value.join.return_value.order_by.return_value
        order_mock.offset.assert_called_with(20)
        order_mock.offset.return_value.limit.assert_called_with(10)

    def test_ascending_order(self):
        db = MagicMock()
        self._setup_base_mock(db)
        query_audit_events(db, order="asc")
        db.query.return_value.join.return_value.order_by.assert_called()

    def test_returns_all_fields(self):
        row_id = uuid.uuid4()
        actor_id = uuid.uuid4()
        project_id = uuid.uuid4()
        resource_id = uuid.uuid4()
        occurred = datetime(2026, 7, 8, 12, 0, 0, tzinfo=timezone.utc)

        db = MagicMock()
        joined, chained = self._setup_base_mock(db, count=1)
        chained.all.return_value = [
            self._make_mock_row(
                id=row_id,
                event_type="execution.completed",
                actor_id=actor_id,
                actor_display_name="Worker",
                actor_email="worker@ferry.internal",
                project_id=project_id,
                resource_type="execution_request",
                resource_id=resource_id,
                event_metadata={"output_count": 3},
                occurred_at=occurred,
            )
        ]

        items, total = query_audit_events(db)

        assert total == 1
        item = items[0]
        assert item["id"] == row_id
        assert item["event_type"] == "execution.completed"
        assert item["actor_id"] == actor_id
        assert item["actor_display_name"] == "Worker"
        assert item["actor_email"] == "worker@ferry.internal"
        assert item["project_id"] == project_id
        assert item["resource_type"] == "execution_request"
        assert item["resource_id"] == resource_id
        assert item["event_metadata"] == {"output_count": 3}
        assert item["occurred_at"] == occurred
