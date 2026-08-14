import logging

from app.ai import get_ai_provider
from app.ai.base import ProviderStatus

logger = logging.getLogger("ferry.ai.status")


def check_ai_status() -> ProviderStatus:
    provider = get_ai_provider()
    status = provider.check_status()
    if not status.ready:
        logger.info("AI not ready: %s", status.reason)
    return status
