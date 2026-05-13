"""Data models for ARIA."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class RawOpportunity:
    """Unscored opportunity returned from a search source."""

    id: str
    title: str
    description: str
    source_name: str
    source_url: str
    organisation: str
    raw_deadline: str = ""
    budget: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.id:
            self.id = hashlib.sha256(
                f"{self.source_name}:{self.source_url}:{self.title}".encode()
            ).hexdigest()[:16]


@dataclass
class Opportunity:
    """Scored and (optionally) enriched opportunity ready for the report."""

    # Identity
    id: str
    title: str
    organisation: str
    source_name: str
    source_url: str
    description: str

    # Classification
    category: str = "Tender"  # ToR / Tender / Speaking / Media / Award / Partnership

    # Deadline
    deadline: Optional[datetime] = None
    deadline_raw: str = ""

    # Budget
    budget: Optional[str] = None

    # Scores (1–10)
    relevance: float = 0.0
    track_record: float = 0.0
    win_probability: float = 0.0
    strategic_value: float = 0.0
    overall_score: float = 0.0

    # Enrichment (populated when overall_score >= ENRICHMENT_THRESHOLD)
    why_this_fits: Optional[str] = None
    lead_with: Optional[str] = None
    consortium_needed: Optional[str] = None
    suggested_first_move: Optional[str] = None

    @property
    def deadline_urgency(self) -> str:
        """Return colour-coded urgency indicator based on days to deadline."""
        if not self.deadline:
            return ""
        days = (self.deadline - datetime.utcnow()).days
        if days < 7:
            return "🔴"
        if days <= 21:
            return "🟡"
        return "🟢"

    @property
    def deadline_display(self) -> str:
        if self.deadline:
            return self.deadline.strftime("%d %b %Y")
        return self.deadline_raw or "Not specified"


@dataclass
class RunResult:
    run_number: int
    date: datetime
    opportunities: list[Opportunity] = field(default_factory=list)
    sources_searched: list[str] = field(default_factory=list)
    total_raw: int = 0
    total_scored: int = 0

    @property
    def priority(self) -> list[Opportunity]:
        from aria.config import ENRICHMENT_THRESHOLD
        return [o for o in self.opportunities if o.overall_score >= ENRICHMENT_THRESHOLD]

    @property
    def pipeline(self) -> list[Opportunity]:
        from aria.config import ENRICHMENT_THRESHOLD, SCORE_THRESHOLD
        return [
            o for o in self.opportunities
            if SCORE_THRESHOLD <= o.overall_score < ENRICHMENT_THRESHOLD
        ]
