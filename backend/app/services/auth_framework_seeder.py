import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.audit_event import SYSTEM_USER_ID, WORKER_USER_ID
from app.models.capability import ALL_CAPABILITIES, Capability, CapabilityRecord
from app.models.role import RoleRecord
from app.models.role_capability import RoleCapability
from app.models.user import User, UserRole, set_role_capability_map

# Role templates: the canonical capabilities for each institutional persona.
# Roles are additive — users may hold multiple roles.
# These are the sole source of truth for role-derived capabilities.
_ROLE_CAPABILITY_MAP: dict[UserRole, set[str]] = {
    UserRole.RESEARCHER: {
        Capability.BUNDLE_CREATE,
        Capability.BUNDLE_SUBMIT,
        Capability.EXECUTION_RUN,
        Capability.VALIDATION_RUN,
    },
    UserRole.MODERATOR: {
        Capability.BUNDLE_REVIEW,
        Capability.OUTPUT_REVIEW,
        Capability.OUTPUT_RELEASE,
    },
    UserRole.MAINTAINER: {
        Capability.PROJECT_MANAGE,
        Capability.PROJECT_MEMBERS_MANAGE,
        Capability.PROJECT_RESOURCES_MANAGE,
        Capability.ENVIRONMENT_MANAGE,
        Capability.DATA_MANAGE,
        Capability.USER_READ,
        Capability.EXECUTION_CANCEL,
    },
    UserRole.ADMIN: {
        Capability.USER_MANAGE,
        Capability.USER_READ,
        Capability.TERMS_MANAGE,
        Capability.SETTINGS_MANAGE,
        Capability.EXECUTION_CANCEL,
        Capability.EXECUTION_READ,
        Capability.AUDIT_READ,
        Capability.ENVIRONMENT_MANAGE,
        Capability.DATA_MANAGE,
    },
}


def seed_auth_framework(db: Session) -> None:
    """Idempotently seed capabilities, roles, role-capability mappings,
    register the role template map for runtime derivation, and seed system users."""
    set_role_capability_map(_ROLE_CAPABILITY_MAP)
    _seed_capabilities(db)
    _seed_roles(db)
    _seed_role_capabilities(db)
    _seed_system_users(db)
    db.commit()


def _seed_capabilities(db: Session) -> None:
    existing = {r.name for r in db.query(CapabilityRecord).all()}
    for cap_name in ALL_CAPABILITIES:
        if cap_name not in existing:
            db.add(CapabilityRecord(name=cap_name))


def _seed_roles(db: Session) -> None:
    existing = {r.name for r in db.query(RoleRecord).all()}
    for role in UserRole:
        if role.value not in existing:
            db.add(RoleRecord(name=role.value))


def _seed_role_capabilities(db: Session) -> None:
    roles = {r.name: r for r in db.query(RoleRecord).all()}
    existing = {
        (rc.role_id, rc.capability_name) for rc in db.query(RoleCapability).all()
    }
    for user_role, capabilities in _ROLE_CAPABILITY_MAP.items():
        role_record = roles.get(user_role.value)
        if role_record is None:
            continue
        for cap_name in capabilities:
            if (role_record.id, cap_name) not in existing:
                db.add(RoleCapability(role_id=role_record.id, capability_name=cap_name))


def cleanup_role_derived_capabilities(db: Session, user: User) -> None:
    """Remove user_capabilities rows that are covered by the user's
    current role templates. After cleanup, user_capabilities contains
    only explicitly granted advanced permissions (e.g. build.customize).

    Role-derived capabilities are computed at runtime — they do not
    need to be stored in user_capabilities."""
    role_caps: set[str] = set()
    for assignment in user.role_assignments:
        role_enum = _try_parse_role_enum(assignment.role.name)
        if role_enum is not None:
            role_caps.update(_ROLE_CAPABILITY_MAP.get(role_enum, set()))

    for cap_name in role_caps:
        db.execute(
            text(
                "DELETE FROM user_capabilities "
                "WHERE user_id = :uid AND capability_name = :cap"
            ),
            {"uid": user.id, "cap": cap_name},
        )


def _try_parse_role_enum(name: str) -> UserRole | None:
    try:
        return UserRole(name)
    except ValueError:
        return None


_SYSTEM_USERS: list[tuple[uuid.UUID, str, str]] = [
    (SYSTEM_USER_ID, "system@ferry.internal", "System"),
    (WORKER_USER_ID, "execution_worker@ferry.internal", "Execution Worker"),
]


def _seed_system_users(db: Session) -> None:
    """Idempotently seed system user accounts for autonomous platform components.
    System users use well-known UUIDs, have no password (cannot log in),
    and carry no capabilities. They exist solely as accountable actors
    referenced by Audit Events.

    A role value is required by the schema; MAINTAINER is used as the
    closest semantic match to a platform operator. They are never assigned
    role_assignments and never acquire capabilities."""
    for user_id, email, display_name in _SYSTEM_USERS:
        existing = db.query(User).filter(User.id == user_id).first()
        if existing is not None:
            continue
        user = User(
            id=user_id,
            email=email,
            display_name=display_name,
            password_hash="",
            role=UserRole.MAINTAINER,
        )
        db.add(user)
