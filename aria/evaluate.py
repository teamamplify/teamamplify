"""Claude-powered opportunity evaluation and scoring."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import anthropic

from aria.config import (
    AMPLIFY_PROFILE,
    CLAUDE_MODEL,
    ENRICHMENT_THRESHOLD,
    SCORE_THRESHOLD,
    SCORING_WEIGHTS,
)
from aria.models import Opportunity, RawOpportunity

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None

SYSTEM_PROMPT = f"""You are an expert opportunity analyst for Amplify Impact B.V., a strategic
advisory consultancy. Your task is to evaluate whether a given opportunity is a good fit for
Amplify Impact using their FIT SCORING PROTOCOL.

AMPLIFY IMPACT PROFILE:
{AMPLIFY_PROFILE}

SCORING PROTOCOL — score each dimension 1-10:

RELEVANCE (30% weight): Does this match Amplify Impact's core expertise?
  10 = exact match to a proven service area
  5  = adjacent, stretch possible
  1  = tangential or misaligned

TRACK_RECORD (25% weight): Does Amplify Impact have a direct comparable?
  10 = nearly identical work already delivered
  5  = similar sector or method
  1  = no relevant precedent

WIN_PROBABILITY (25% weight): How competitive is Amplify Impact for this?
  10 = strong fit + likely few comparable bidders
  5  = competitive field, real chance
  1  = long shot or structurally disadvantaged

STRATEGIC_VALUE (20% weight): Beyond revenue, what does this unlock?
  10 = opens new market, builds flagship case study, major visibility
  5  = solid revenue, modest profile
  1  = routine, no strategic upside

THRESHOLD: Only surface opportunities with weighted overall score >= 6.0.

EXCLUSION RULES — immediately set all scores to 0 if:
- Pure auditing, accounting, or legal compliance work
- Pure private sector commercial work with no social impact dimension
- Highly technical IT implementation (not strategy/AI governance)
- Deadline has already passed

Respond ONLY with valid JSON. No prose before or after the JSON block."""

EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
        "relevance": {"type": "number", "minimum": 0, "maximum": 10},
        "track_record": {"type": "number", "minimum": 0, "maximum": 10},
        "win_probability": {"type": "number", "minimum": 0, "maximum": 10},
        "strategic_value": {"type": "number", "minimum": 0, "maximum": 10},
        "category": {
            "type": "string",
            "enum": ["ToR", "Tender", "Speaking", "Media", "Award", "Partnership", "Other"],
        },
        "deadline_parsed": {"type": ["string", "null"]},
        "why_this_fits": {"type": ["string", "null"]},
        "lead_with": {"type": ["string", "null"]},
        "consortium_needed": {"type": ["string", "null"]},
        "suggested_first_move": {"type": ["string", "null"]},
        "exclude_reason": {"type": ["string", "null"]},
    },
    "required": [
        "relevance", "track_record", "win_probability", "strategic_value",
        "category", "deadline_parsed", "exclude_reason",
    ],
}


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def _build_prompt(opp: RawOpportunity) -> str:
    return f"""Evaluate this opportunity for Amplify Impact B.V.:

TITLE: {opp.title}
ORGANISATION: {opp.organisation or "Not specified"}
SOURCE: {opp.source_name}
URL: {opp.source_url}
DEADLINE: {opp.raw_deadline or "Not specified"}
BUDGET: {opp.budget or "Not specified"}

DESCRIPTION:
{opp.description[:1500] if opp.description else "No description available."}

Return a JSON object with these exact fields:
{{
  "relevance": <1-10>,
  "track_record": <1-10>,
  "win_probability": <1-10>,
  "strategic_value": <1-10>,
  "category": "<ToR|Tender|Speaking|Media|Award|Partnership|Other>",
  "deadline_parsed": "<ISO date string YYYY-MM-DD or null>",
  "why_this_fits": "<2-3 sentences specific to Amplify's track record — only if overall weighted score >= 8, else null>",
  "lead_with": "<which specific past client/work to foreground — only if score >= 8, else null>",
  "consortium_needed": "<Yes/No and what type — only if score >= 8, else null>",
  "suggested_first_move": "<specific actionable next step — only if score >= 8, else null>",
  "exclude_reason": "<reason to exclude if this fails the exclusion rules, else null>"
}}"""


def _weighted_score(scores: dict) -> float:
    return sum(
        scores[dim] * weight for dim, weight in SCORING_WEIGHTS.items()
    )


def _parse_deadline(deadline_str: str | None) -> Optional[datetime]:
    if not deadline_str:
        return None
    try:
        from dateutil import parser as dateparser
        return dateparser.parse(deadline_str, fuzzy=True)
    except Exception:
        return None


def evaluate_opportunity(raw: RawOpportunity) -> Optional[Opportunity]:
    """
    Score a single opportunity using Claude.
    Returns None if the opportunity should be excluded (score < threshold or fails rules).
    """
    try:
        client = _get_client()
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(raw)}],
        )
        raw_json = response.content[0].text.strip()

        # Strip markdown code fences if present
        if raw_json.startswith("```"):
            raw_json = raw_json.split("```")[1]
            if raw_json.startswith("json"):
                raw_json = raw_json[4:]
        raw_json = raw_json.strip()

        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        logger.error("JSON parse error for %r: %s", raw.title, exc)
        return None
    except Exception as exc:
        logger.error("Claude evaluation failed for %r: %s", raw.title, exc)
        return None

    # Check exclusion
    if data.get("exclude_reason"):
        logger.debug("Excluded %r: %s", raw.title, data["exclude_reason"])
        return None

    scores = {
        "relevance": float(data.get("relevance", 0)),
        "track_record": float(data.get("track_record", 0)),
        "win_probability": float(data.get("win_probability", 0)),
        "strategic_value": float(data.get("strategic_value", 0)),
    }
    overall = _weighted_score(scores)

    if overall < SCORE_THRESHOLD:
        logger.debug("Below threshold (%.1f) — skipping %r", overall, raw.title)
        return None

    deadline_parsed = _parse_deadline(data.get("deadline_parsed") or raw.raw_deadline)

    # Exclude if deadline has already passed
    if deadline_parsed and deadline_parsed < datetime.utcnow():
        logger.debug("Past deadline — skipping %r", raw.title)
        return None

    opp = Opportunity(
        id=raw.id,
        title=raw.title,
        organisation=raw.organisation,
        source_name=raw.source_name,
        source_url=raw.source_url,
        description=raw.description,
        category=data.get("category", "Tender"),
        deadline=deadline_parsed,
        deadline_raw=raw.raw_deadline,
        budget=raw.budget,
        relevance=scores["relevance"],
        track_record=scores["track_record"],
        win_probability=scores["win_probability"],
        strategic_value=scores["strategic_value"],
        overall_score=round(overall, 1),
    )

    # Enrich if score >= threshold
    if overall >= ENRICHMENT_THRESHOLD:
        opp.why_this_fits = data.get("why_this_fits")
        opp.lead_with = data.get("lead_with")
        opp.consortium_needed = data.get("consortium_needed")
        opp.suggested_first_move = data.get("suggested_first_move")

    return opp


def evaluate_all(raw_opportunities: List[RawOpportunity]) -> List[Opportunity]:
    """Evaluate all raw opportunities; return only those that pass the threshold."""
    scored: List[Opportunity] = []
    total = len(raw_opportunities)

    for i, raw in enumerate(raw_opportunities, 1):
        logger.info("Evaluating %d/%d: %s", i, total, raw.title[:60])
        result = evaluate_opportunity(raw)
        if result:
            scored.append(result)
            logger.info(
                "  → Score %.1f (%s)",
                result.overall_score,
                result.category,
            )

    scored.sort(key=lambda o: o.overall_score, reverse=True)
    logger.info(
        "Evaluation complete: %d/%d opportunities qualify", len(scored), total
    )
    return scored
