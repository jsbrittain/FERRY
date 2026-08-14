import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal

logger = logging.getLogger("ferry")

router = APIRouter()


@router.get("/health")
def health():
    db_ok = False
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:
        logger.warning("Health check — database unreachable: %s", exc)
    finally:
        db.close()

    redis_ok = False
    try:
        import redis as redis_lib

        r = redis_lib.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            db=settings.redis_db,
            socket_connect_timeout=3,
        )
        r.ping()
        r.close()
        redis_ok = True
    except Exception as exc:
        logger.warning("Health check — redis unreachable: %s", exc)

    all_ok = db_ok and redis_ok
    return {
        "status": "ok" if all_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "redis": "connected" if redis_ok else "disconnected",
    }
