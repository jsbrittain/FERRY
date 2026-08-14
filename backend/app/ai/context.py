"""Context describing the resource being reviewed, supplied to AI
providers during review. Contains only non-sensitive metadata already
known to FERRY and deliberately excludes project information, user
information, execution history and dataset contents.
"""

from dataclasses import dataclass, field


@dataclass
class AIReviewContext:
    runtime: str = ""
    entrypoint: str = ""
    resource_identifiers: list[str] = field(default_factory=list)
    file_count: int = 0
    total_size: int = 0
    binary_files: list[str] = field(default_factory=list)
    analysis_type: str = "bundle"
