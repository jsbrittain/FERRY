import logging
import uuid

from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.context import AIReviewContext
from app.db.session import SessionLocal
from app.models.ai_bundle_review import AIBundleReview, AIBundleReviewStatus
from app.models.ai_output_set_review import AIOutputSetReview, AIOutputSetReviewStatus
from app.models.analysis_bundle import AnalysisBundle
from app.models.output_set import OutputSet
from app.models.platform_setting import SettingKey
from app.services.bundle_store import get_bundle_store
from app.services.output_service import OUTPUT_ROOT
from app.services.output_set_service import list_outputs_by_set
from app.services.platform_settings_service import get_setting_bool

logger = logging.getLogger("ferry.ai.review")


def request_review(bundle_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        review = (
            db.query(AIBundleReview)
            .filter(AIBundleReview.bundle_id == bundle_id)
            .first()
        )
        if review is None:
            bundle = (
                db.query(AnalysisBundle).filter(AnalysisBundle.id == bundle_id).first()
            )
            if bundle is None:
                logger.warning("request_review: bundle %s not found", bundle_id)
                return
            review = AIBundleReview(
                bundle_id=bundle_id, status=AIBundleReviewStatus.PENDING
            )
            db.add(review)
        else:
            review.status = AIBundleReviewStatus.PENDING
            review.summary = None
            review.assessment = None
            review.assessment_confidence = None
            review.reviewer_notes = None
        db.commit()
        logger.info("request_review: bundle %s set to PENDING", bundle_id)
    except Exception:
        logger.exception("request_review: error for bundle %s", bundle_id)
        db.rollback()
    finally:
        db.close()


def perform_review(bundle_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        review = (
            db.query(AIBundleReview)
            .filter(AIBundleReview.bundle_id == bundle_id)
            .first()
        )
        if review is None:
            logger.warning("perform_review: no review record for bundle %s", bundle_id)
            return

        ai_enabled = get_setting_bool(db, SettingKey.AI_REVIEW_ENABLED)
        if not ai_enabled:
            logger.info(
                "perform_review: AI review disabled by policy for bundle %s", bundle_id
            )
            review.status = AIBundleReviewStatus.UNAVAILABLE
            db.commit()
            return

        provider = get_ai_provider()

        bundle = db.query(AnalysisBundle).filter(AnalysisBundle.id == bundle_id).first()
        context = AIReviewContext(
            runtime=(
                bundle.execution_environment.runtime
                if bundle and bundle.execution_environment
                else ""
            ),
            entrypoint=bundle.entrypoint if bundle else "",
            resource_identifiers=(
                sorted(dr.identifier for dr in bundle.data_resources) if bundle else []
            ),
        )

        analysis_dir = get_bundle_store().get_path(bundle_id)
        result = provider.review(analysis_dir, context=context)

        if result.is_unavailable:
            review.status = AIBundleReviewStatus.UNAVAILABLE
            logger.warning(
                "perform_review: provider unavailable for bundle %s: %s",
                bundle_id,
                result.errors,
            )
        else:
            review.summary = result.summary
            review.assessment = result.assessment
            review.assessment_confidence = result.assessment_confidence
            review.reviewer_notes = result.reviewer_notes
            review.status = AIBundleReviewStatus.COMPLETED
            logger.info("perform_review: bundle %s completed", bundle_id)

        db.commit()
    except Exception:
        logger.exception("perform_review: error for bundle %s", bundle_id)
        try:
            review = (
                db.query(AIBundleReview)
                .filter(AIBundleReview.bundle_id == bundle_id)
                .first()
            )
            if review is not None:
                review.status = AIBundleReviewStatus.FAILED
                db.commit()
        except Exception:
            logger.exception(
                "perform_review: failed to set FAILED status for bundle %s", bundle_id
            )
            db.rollback()
    finally:
        db.close()


def request_and_perform_review(bundle_id: uuid.UUID) -> None:
    try:
        request_review(bundle_id)
        perform_review(bundle_id)
    except Exception:
        logger.exception(
            "request_and_perform_review: unhandled error for bundle %s", bundle_id
        )


def get_review(db: Session, bundle_id: uuid.UUID) -> AIBundleReview | None:
    return (
        db.query(AIBundleReview).filter(AIBundleReview.bundle_id == bundle_id).first()
    )


def request_output_set_review(output_set_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        review = (
            db.query(AIOutputSetReview)
            .filter(AIOutputSetReview.output_set_id == output_set_id)
            .first()
        )
        if review is None:
            output_set = (
                db.query(OutputSet).filter(OutputSet.id == output_set_id).first()
            )
            if output_set is None:
                logger.warning(
                    "request_output_set_review: output set %s not found", output_set_id
                )
                return
            review = AIOutputSetReview(
                output_set_id=output_set_id, status=AIOutputSetReviewStatus.PENDING
            )
            db.add(review)
        else:
            review.status = AIOutputSetReviewStatus.PENDING
            review.summary = None
            review.assessment = None
            review.assessment_confidence = None
            review.reviewer_notes = None
        db.commit()
        logger.info(
            "request_output_set_review: output set %s set to PENDING", output_set_id
        )
    except Exception:
        logger.exception(
            "request_output_set_review: error for output set %s", output_set_id
        )
        db.rollback()
    finally:
        db.close()


def perform_output_set_review(output_set_id: uuid.UUID) -> None:
    db = SessionLocal()
    try:
        review = (
            db.query(AIOutputSetReview)
            .filter(AIOutputSetReview.output_set_id == output_set_id)
            .first()
        )
        if review is None:
            logger.warning(
                "perform_output_set_review: no review record for output set %s",
                output_set_id,
            )
            return

        ai_enabled = get_setting_bool(db, SettingKey.AI_REVIEW_ENABLED)
        if not ai_enabled:
            logger.info(
                "perform_output_set_review: AI review disabled for output set %s",
                output_set_id,
            )
            review.status = AIOutputSetReviewStatus.UNAVAILABLE
            db.commit()
            return

        provider = get_ai_provider()

        output_set = db.query(OutputSet).filter(OutputSet.id == output_set_id).first()
        execution_request = output_set.execution_request if output_set else None
        outputs = list_outputs_by_set(db, output_set_id) if output_set else []
        output_dir = (
            OUTPUT_ROOT / str(execution_request.id) if execution_request else None
        )

        context = AIReviewContext(
            runtime=(
                execution_request.analysis_bundle.execution_environment.runtime
                if execution_request
                and execution_request.analysis_bundle
                and execution_request.analysis_bundle.execution_environment
                else ""
            ),
            entrypoint="",
            resource_identifiers=[],
            file_count=len(outputs),
            total_size=sum(o.size for o in outputs),
            binary_files=[
                o.filename for o in outputs if _is_binary_filename(o.filename)
            ],
            analysis_type="output_set",
        )

        if output_dir is None or not output_dir.is_dir():
            logger.warning(
                "perform_output_set_review: output directory not found for %s",
                output_set_id,
            )
            review.status = AIOutputSetReviewStatus.UNAVAILABLE
            db.commit()
            return

        result = provider.review(output_dir, context=context)

        if result.is_unavailable:
            review.status = AIOutputSetReviewStatus.UNAVAILABLE
            logger.warning(
                "perform_output_set_review: provider unavailable for output set %s: %s",
                output_set_id,
                result.errors,
            )
        else:
            review.summary = result.summary
            review.assessment = result.assessment
            review.assessment_confidence = result.assessment_confidence
            review.reviewer_notes = result.reviewer_notes
            review.status = AIOutputSetReviewStatus.COMPLETED
            logger.info(
                "perform_output_set_review: output set %s completed", output_set_id
            )

        db.commit()
    except Exception:
        logger.exception(
            "perform_output_set_review: error for output set %s", output_set_id
        )
        try:
            review = (
                db.query(AIOutputSetReview)
                .filter(AIOutputSetReview.output_set_id == output_set_id)
                .first()
            )
            if review is not None:
                review.status = AIOutputSetReviewStatus.FAILED
                db.commit()
        except Exception:
            logger.exception(
                "perform_output_set_review: failed to set FAILED status "
                "for output set %s",
                output_set_id,
            )
            db.rollback()
    finally:
        db.close()


def request_and_perform_output_set_review(output_set_id: uuid.UUID) -> None:
    try:
        request_output_set_review(output_set_id)
        perform_output_set_review(output_set_id)
    except Exception:
        logger.exception(
            "request_and_perform_output_set_review: unhandled error for output set %s",
            output_set_id,
        )


def get_output_set_review(
    db: Session, output_set_id: uuid.UUID
) -> AIOutputSetReview | None:
    return (
        db.query(AIOutputSetReview)
        .filter(AIOutputSetReview.output_set_id == output_set_id)
        .first()
    )


def _is_binary_filename(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    text_extensions = {
        "py",
        "r",
        "sh",
        "js",
        "ipynb",
        "txt",
        "md",
        "csv",
        "json",
        "yaml",
        "yml",
        "xml",
        "html",
        "htm",
        "cfg",
        "conf",
        "ini",
        "env",
        "log",
        "tsv",
        "rst",
        "toml",
        "css",
        "ts",
        "tsx",
        "jsx",
        "sql",
    }
    return ext not in text_extensions
