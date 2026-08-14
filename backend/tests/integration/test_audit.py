"""Integration tests for the audit event model and service."""

import uuid

import pytest

from app.models.audit_event import AuditEvent, AuditEventType
from app.models.project import Project
from app.models.user import User, UserRole
from app.services.audit_service import create_audit_event


@pytest.fixture
def user(db_session):
    user = User(
        email="audit-test@ferry.local",
        display_name="Audit Test User",
        role=UserRole.RESEARCHER,
        password_hash="",
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def project(db_session, user):
    project = Project(name="Audit Test Project", owner_id=user.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


class TestAuditEventPersistence:
    def test_create_and_retrieve(self, db_session, user, project):
        event = create_audit_event(
            db_session,
            event_type=AuditEventType.BUNDLE_SUBMITTED,
            actor_id=user.id,
            project_id=project.id,
            resource_type="analysis_bundle",
            resource_id=uuid.uuid4(),
            metadata={"bundle_name": "Test"},
        )
        db_session.commit()

        saved = db_session.query(AuditEvent).filter(AuditEvent.id == event.id).first()
        assert saved is not None
        assert saved.event_type == "bundle.submitted"
        assert saved.actor_id == user.id
        assert saved.resource_type == "analysis_bundle"
        assert saved.event_metadata == {"bundle_name": "Test"}

    def test_query_by_event_type(self, db_session, user):
        event = AuditEvent(
            event_type=AuditEventType.EXECUTION_REQUESTED.value,
            actor_id=user.id,
            resource_type="execution_request",
            resource_id=uuid.uuid4(),
            event_metadata={},
        )
        db_session.add(event)
        db_session.commit()

        results = (
            db_session.query(AuditEvent)
            .filter(AuditEvent.event_type == "execution.requested")
            .all()
        )
        assert len(results) >= 1
        assert results[0].event_type == "execution.requested"

    def test_query_by_actor(self, db_session, user):
        for i in range(3):
            create_audit_event(
                db_session,
                event_type=AuditEventType.PROJECT_CREATED,
                actor_id=user.id,
                resource_type="project",
                resource_id=uuid.uuid4(),
                metadata={"project_name": f"Project {i}"},
            )
        db_session.commit()

        results = (
            db_session.query(AuditEvent).filter(AuditEvent.actor_id == user.id).all()
        )
        assert len(results) == 3

    def test_nullable_project_id(self, db_session, user):
        event = create_audit_event(
            db_session,
            event_type=AuditEventType.USER_CREATED,
            actor_id=user.id,
            resource_type="user",
            resource_id=uuid.uuid4(),
            metadata={"user_email": "new@ferry.local"},
        )
        db_session.commit()

        saved = db_session.query(AuditEvent).filter(AuditEvent.id == event.id).first()
        assert saved.project_id is None

    def test_occurred_at_is_set(self, db_session, user):
        event = AuditEvent(
            event_type=AuditEventType.OUTPUT_SET_CREATED.value,
            actor_id=user.id,
            resource_type="output_set",
            resource_id=uuid.uuid4(),
        )
        db_session.add(event)
        db_session.commit()

        assert event.occurred_at is not None
