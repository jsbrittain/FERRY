import sys
from pathlib import Path

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.data_resource import DataResource
from app.models.user import UserRole
from app.services.ai_status_service import check_ai_status
from app.services.demo_seeder import seed_demo_workspace
from app.services.manifest_loader import load_resource_directory
from app.services.resource_registration import register_from_manifest
from app.services.terms_service import seed_terms
from app.services.user_service import (
    create_user,
    get_or_create_admin,
    get_or_create_user,
)


def seed_admin():
    db = SessionLocal()
    try:
        user = get_or_create_admin(db)
        print(f"seed-admin: Created/verified admin user: {user.email} (id={user.id})")
    except Exception as e:
        print(f"seed-admin: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def seed_terms_cmd():
    db = SessionLocal()
    try:
        result = seed_terms(db)
        if result["status"] == "skipped":
            print(f"seed-terms: {result['message']}")
        elif result["status"] == "error":
            print(f"seed-terms: ERROR — {result['message']}")
            sys.exit(1)
        else:
            print(f"seed-terms: Published platform terms (version={result['version']})")
    except Exception as e:
        print(f"seed-terms: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def create_researcher():
    if len(sys.argv) < 4:
        print(
            "Usage: ferry create-user <email> <name> "
            "[--password PASSWORD] [--roles researcher,moderator,...]"
        )
        sys.exit(1)

    email = sys.argv[2]
    name = sys.argv[3]
    password = "password"
    roles = [UserRole.RESEARCHER]

    i = 4
    while i < len(sys.argv):
        if sys.argv[i] == "--password" and i + 1 < len(sys.argv):
            password = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--roles" and i + 1 < len(sys.argv):
            role_strs = sys.argv[i + 1].split(",")
            parsed = []
            for rs in role_strs:
                try:
                    parsed.append(UserRole(rs.strip()))
                except ValueError:
                    print(f"Unknown role: {rs.strip()}")
                    sys.exit(1)
            roles = parsed
            i += 2
        else:
            i += 1

    db = SessionLocal()
    try:
        user = create_user(
            db, email=email, display_name=name, password=password, roles=roles
        )
        role_names = ", ".join(r.value for r in roles)
        print(
            f"create-user: Created user with roles [{role_names}]: "
            f"{user.email} (id={user.id})"
        )
    except Exception as e:
        print(f"create-user: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def seed_maintainer():
    email = "maintainer@ferry.local"
    password = "maintainer"
    display_name = "Maintainer"

    if len(sys.argv) >= 4:
        email = sys.argv[2]
        password = sys.argv[3]
    if len(sys.argv) >= 5:
        display_name = sys.argv[4]

    db = SessionLocal()
    try:
        user = get_or_create_user(
            db,
            email=email,
            display_name=display_name,
            password=password,
            role=UserRole.MAINTAINER,
            roles=[UserRole.MAINTAINER],
        )
        print(
            f"seed-maintainer: Created/verified maintainer user: "
            f"{user.email} (id={user.id})"
        )
    except Exception as e:
        print(f"seed-maintainer: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def seed_researcher():
    email = "researcher@ferry.local"
    password = "researcher"
    display_name = "Researcher"

    db = SessionLocal()
    try:
        user = get_or_create_user(
            db,
            email=email,
            display_name=display_name,
            password=password,
            role=UserRole.RESEARCHER,
            roles=[UserRole.RESEARCHER],
        )
        print(
            f"seed-researcher: Created/verified researcher user: "
            f"{user.email} (id={user.id})"
        )
    except Exception as e:
        print(f"seed-researcher: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def seed_moderator():
    email = "moderator@ferry.local"
    password = "moderator"
    display_name = "Moderator"

    db = SessionLocal()
    try:
        user = get_or_create_user(
            db,
            email=email,
            display_name=display_name,
            password=password,
            role=UserRole.MODERATOR,
            roles=[UserRole.MODERATOR],
        )
        print(
            f"seed-moderator: Created/verified moderator user: "
            f"{user.email} (id={user.id})"
        )
    except Exception as e:
        print(f"seed-moderator: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def seed_developer():
    email = "developer@ferry.local"
    password = "developer"
    display_name = "Developer"
    roles = list(UserRole)

    db = SessionLocal()
    try:
        user = get_or_create_user(
            db,
            email=email,
            display_name=display_name,
            password=password,
            role=UserRole.DEVELOPER
            if hasattr(UserRole, "DEVELOPER")
            else UserRole.ADMIN,
            roles=roles,
        )
        role_names = ", ".join(r.value for r in roles)
        print(
            f"seed-developer: Created/verified developer user "
            f"(all roles: [{role_names}]): {user.email} (id={user.id})"
        )
    except Exception as e:
        print(f"seed-developer: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def check_ai_status_cli():
    configure_logging(settings.log_level)
    status = check_ai_status()
    if status.ready:
        print("AI is ready")
        sys.exit(0)
    else:
        print(f"AI is not ready: {status.reason}")
        sys.exit(1)


def seed_demo():
    db = SessionLocal()
    try:
        result = seed_demo_workspace(db)
        status = result["status"]
        if status == "skipped":
            print(f"seed-demo: {result['message']}")
        elif status == "error":
            print(f"seed-demo: ERROR — {result['message']}")
            sys.exit(1)
        else:
            print(
                f"seed-demo: Created demo workspace "
                f"(project_id={result['project_id']}, bundle_id={result['bundle_id']})"
            )
    except Exception as e:
        print(f"seed-demo: ERROR — {e}")
        sys.exit(1)
    finally:
        db.close()


def resource_register_all():
    db = SessionLocal()
    try:
        manifest_path = Path(settings.resource_manifest_dir)
        if not manifest_path.is_dir():
            print(
                f"ERROR: Resource manifest directory not found: {manifest_path}. "
                "Set RESOURCE_MANIFEST_DIR env var to a valid directory."
            )
            sys.exit(1)

        entries = load_resource_directory(manifest_path)
        result = register_from_manifest(db, entries)

        if result.errors:
            for err in result.errors:
                print(f"  ERROR: {err}")

        for resource in result.created:
            print(f"  created: {resource.identifier} ({resource.name})")

        for ident in result.skipped:
            print(f"  skipped: {ident} (already registered)")

        print(
            f"\nRegistered: {len(result.created)}  "
            f"Skipped: {len(result.skipped)}  "
            f"Errors: {len(result.errors)}"
        )

        if result.errors:
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


def resource_register(identifier: str):
    db = SessionLocal()
    try:
        manifest_path = Path(settings.resource_manifest_dir)
        manifest_file = manifest_path / identifier / "manifest.yaml"

        if not manifest_file.is_file():
            print(f"ERROR: Manifest not found: {manifest_file}")
            sys.exit(1)

        import yaml

        with open(manifest_file) as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            print(f"ERROR: Invalid manifest in {manifest_file}")
            sys.exit(1)

        from app.services.manifest_loader import REQUIRED_FIELDS

        missing = REQUIRED_FIELDS - set(data.keys())
        if missing:
            print(
                f"ERROR: Missing required fields {sorted(missing)} in {manifest_file}"
            )
            sys.exit(1)

        entry = {
            "identifier": data["identifier"],
            "name": data["name"],
            "alias": data["alias"],
            "provider": data["provider"],
            "endpoint": data["endpoint"],
            "description": data.get("description", ""),
            "version": data.get("version", "1.0.0"),
            "status": data.get("status", "active"),
        }

        from app.services.resource_registration import register_resource

        result = register_resource(db, entry)
        if result.created:
            db.commit()
            resource = result.created[0]
            print(f"Registered: {resource.identifier} ({resource.name})")
        elif result.skipped:
            print(f"Skipped: {identifier} (already registered)")
        if result.errors:
            for err in result.errors:
                print(f"  ERROR: {err}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()


def resource_clean():
    """Remove stale resource registrations (developer utility only).

    Compares registered resources against the manifest directory and
    removes any that no longer have a corresponding manifest on disk.
    Resources that are still referenced by projects, bundles, or terms
    are preserved by database constraints — the command reports them as
    skipped and continues.

    This is a developer utility for keeping a disposable development
    database tidy. It never runs automatically.
    """
    manifest_dir = Path(settings.resource_manifest_dir)
    if not manifest_dir.is_dir():
        print(f"ERROR: Resource manifest directory not found: {manifest_dir}")
        sys.exit(1)

    db = SessionLocal()
    removed = []
    skipped = []
    errors = []

    try:
        resources = db.query(DataResource).all()

        for resource in resources:
            manifest_path = manifest_dir / resource.identifier / "manifest.yaml"
            if manifest_path.is_file():
                continue

            try:
                db.delete(resource)
                db.commit()
                removed.append(resource.identifier)
            except IntegrityError:
                db.rollback()
                skipped.append(resource.identifier)
            except Exception as e:
                db.rollback()
                errors.append(f"{resource.identifier}: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        db.close()

    for ident in removed:
        print(f"  removed: {ident}")
    for ident in skipped:
        print(f"  skipped: {ident} (still referenced)")
    for err in errors:
        print(f"  error: {err}")

    print(f"\nRemoved: {len(removed)}  Skipped: {len(skipped)}  Errors: {len(errors)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: ferry <command>")
        print(
            "Commands: seed-admin, seed-moderator, seed-maintainer, "
            "seed-researcher, seed-developer, seed-terms, seed-demo, "
            "create-user, resource-register-all, resource-register, "
            "resource-clean"
        )
        sys.exit(1)

    command = sys.argv[1]
    if command == "seed-admin":
        seed_admin()
    elif command == "seed-maintainer":
        seed_maintainer()
    elif command == "seed-researcher":
        seed_researcher()
    elif command == "seed-moderator":
        seed_moderator()
    elif command == "seed-developer":
        seed_developer()
    elif command == "seed-terms":
        seed_terms_cmd()
    elif command == "seed-demo":
        seed_demo()
    elif command == "create-user":
        create_researcher()
    elif command == "check-ai-status":
        check_ai_status_cli()
    elif command == "resource-register-all":
        resource_register_all()
    elif command == "resource-register":
        if len(sys.argv) < 3:
            print("Usage: ferry resource-register <identifier>")
            sys.exit(1)
        resource_register(sys.argv[2])
    elif command == "resource-clean":
        resource_clean()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
