"""Shared schema types and validators."""

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL_PATTERN = re.compile(
    r"^[^\s@<>()\[\]\\,;:\"]+@[^\s@<>()\[\]\\,;:\"]+\.[^\s@<>()\[\]\\,;:\"]+$"
)


def _validate_email(v: str) -> str:
    if not _EMAIL_PATTERN.match(v):
        raise ValueError("Invalid email address")
    return v


ValidEmail = Annotated[str, AfterValidator(_validate_email)]
"""A syntactically valid email address.

Syntax validation only — no DNS, MX, or reserved-TLD checks.
Accepts non-public domains (e.g. ``admin@ferry.local``).
"""
