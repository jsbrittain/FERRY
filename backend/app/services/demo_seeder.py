from sqlalchemy.orm import Session

from app.models.analysis_bundle import (
    AnalysisBundle,
    AnalysisBundleDataResource,
)
from app.models.data_resource import DataResource
from app.models.execution_environment import ExecutionEnvironment
from app.models.project import Project
from app.models.project_data_resource import ProjectResourceAllocation
from app.models.project_membership import ProjectMembership
from app.models.user import User
from app.services.terms_service import (
    DEFAULT_PLATFORM_TERMS_CONTENT,
    DEFAULT_PLATFORM_TERMS_TITLE,
    DEFAULT_PLATFORM_TERMS_VERSION,
    get_current_platform_terms,
    publish_platform_terms,
)
from app.workflow.bundle import approve_bundle, submit_bundle

DEMO_PROJECT_NAME = "Demonstration Analysis"
DEMO_BUNDLE_NAME = "Demonstration Summary"
DEMO_RESOURCE_IDENTIFIER = "demo-surveillance"
DEMO_OUTPUT_FILENAME = "summary.csv"


def seed_demo_workspace(db: Session) -> dict:
    admin = db.query(User).filter(User.email == "admin@ferry.local").first()
    if admin is None:
        return {
            "status": "error",
            "message": "Admin user not found. Run seed-admin first.",
        }

    existing = (
        db.query(Project)
        .filter(Project.name == DEMO_PROJECT_NAME, Project.owner_id == admin.id)
        .first()
    )
    if existing is not None:
        return {
            "status": "skipped",
            "message": (f"Demo workspace already exists (project_id={existing.id})"),
        }

    platform_terms = get_current_platform_terms(db)
    if platform_terms is None:
        publish_platform_terms(
            db,
            published_by=admin,
            title=DEFAULT_PLATFORM_TERMS_TITLE,
            content=DEFAULT_PLATFORM_TERMS_CONTENT,
            version=DEFAULT_PLATFORM_TERMS_VERSION,
        )

    project = Project(
        name=DEMO_PROJECT_NAME,
        description=("Demonstration analysis for FERRY canonical workflow."),
        owner_id=admin.id,
    )
    db.add(project)
    db.flush()

    membership = ProjectMembership(
        project_id=project.id,
        user_id=admin.id,
        created_by_id=admin.id,
    )
    db.add(membership)

    resource = (
        db.query(DataResource)
        .filter(DataResource.identifier == DEMO_RESOURCE_IDENTIFIER)
        .first()
    )
    if resource:
        allocation = ProjectResourceAllocation(
            project_id=project.id,
            data_resource_id=resource.id,
            created_by_id=admin.id,
        )
        db.add(allocation)

    env = (
        db.query(ExecutionEnvironment)
        .filter(ExecutionEnvironment.image_reference.isnot(None))
        .filter(ExecutionEnvironment.image_reference != "")
        .order_by(ExecutionEnvironment.created_at)
        .first()
    )
    if env is None:
        env = (
            db.query(ExecutionEnvironment)
            .filter(ExecutionEnvironment.runtime.contains("python"))
            .first()
        )

    bundle = AnalysisBundle(
        project_id=project.id,
        created_by_id=admin.id,
        execution_environment_id=env.id if env else None,
        name=DEMO_BUNDLE_NAME,
        source_path="demo",
        version="1.0.0",
        entrypoint="run.py",
        description=(
            "Computes summary statistics from the demonstration surveillance dataset."
        ),
        outputs=[DEMO_OUTPUT_FILENAME],
        parameters={},
    )
    db.add(bundle)
    db.flush()

    if resource:
        join = AnalysisBundleDataResource(
            analysis_bundle_id=bundle.id,
            data_resource_id=resource.id,
        )
        db.add(join)

    submit_bundle(db, bundle)
    approve_bundle(db, bundle)
    db.commit()

    return {
        "status": "created",
        "project_id": str(project.id),
        "bundle_id": str(bundle.id),
    }
