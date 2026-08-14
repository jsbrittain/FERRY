"""Governance lifecycle dispatch.

Listens for SQLAlchemy after_commit events to dispatch registered
governance handlers (e.g. AI review) when an OutputSet enters governance.

This is an implementation mechanism, not the architectural model.
The architectural governance event is the creation of a new OutputSet
inside ensure_output_set() (output_set_service.py).
"""

import threading
import uuid

from sqlalchemy import event
from sqlalchemy.orm import Session as SASession

_governance_subscribers: list[callable] = []


def register_governance_handler(handler: callable) -> None:
    _governance_subscribers.append(handler)


def _dispatch(output_set_id: uuid.UUID) -> None:
    for handler in _governance_subscribers:
        threading.Thread(target=handler, args=(output_set_id,), daemon=True).start()


@event.listens_for(SASession, "after_commit")
def _dispatch_governance_events(session: SASession) -> None:
    pending = getattr(session, "_ferry_governance_events", [])
    for output_set_id in pending:
        _dispatch(output_set_id)


@event.listens_for(SASession, "after_rollback")
def _clear_governance_events(session: SASession) -> None:
    if hasattr(session, "_ferry_governance_events"):
        session._ferry_governance_events.clear()
