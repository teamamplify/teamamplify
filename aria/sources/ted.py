"""TED (Tenders Electronic Daily) EU procurement API source."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from aria.config import MAX_RESULTS_PER_SOURCE, RELEVANT_CPV_CODES, SEARCH_LOOKBACK_DAYS
from aria.models import RawOpportunity
from aria.sources.base import post

logger = logging.getLogger(__name__)

API_URL = "https://api.ted.europa.eu/v3/notices/search"


def search(lookback_days: int = SEARCH_LOOKBACK_DAYS) -> List[RawOpportunity]:
    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y%m%d")
    opportunities: dict[str, RawOpportunity] = {}

    # Search with high-signal CPV codes for consulting services
    priority_cpvs = [
        "79400000",  # Business and management consultancy
        "79411000",  # General management consultancy
        "79315000",  # Social research services
        "85300000",  # Social work and related services
        "80500000",  # Training services
    ]

    for cpv in priority_cpvs:
        try:
            resp = post(
                API_URL,
                json={
                    "query": f"cpv={cpv}",
                    "pageSize": MAX_RESULTS_PER_SOURCE,
                    "page": 1,
                    "scope": "ACTIVE",
                    "sortField": "publicationDate",
                    "sortOrder": "DESC",
                    "fields": [
                        "noticeNumber",
                        "title",
                        "contracting-body.officialName",
                        "publicationDate",
                        "deadline",
                        "estimatedTotalValue",
                        "description",
                        "noticeUrl",
                        "cpvCodes",
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("TED search failed for CPV %s: %s", cpv, exc)
            continue

        for notice in data.get("notices", []) or data.get("results", []):
            notice_id = notice.get("noticeNumber") or notice.get("id", "")
            opp_id = f"ted-{notice_id}"
            if opp_id in opportunities or not notice_id:
                continue

            title = _extract_text(notice.get("title"))
            if not title:
                continue

            org = _extract_text(
                notice.get("contracting-body", {}).get("officialName")
                or notice.get("contractingBody", {}).get("officialName")
            )

            description = _extract_text(notice.get("description")) or ""
            budget = _extract_budget(notice)
            deadline_raw = notice.get("deadline", "") or ""
            notice_url = (
                notice.get("noticeUrl")
                or f"https://ted.europa.eu/udl?uri=TED:NOTICE:{notice_id}:TEXT:EN:HTML"
            )

            opportunities[opp_id] = RawOpportunity(
                id=opp_id,
                title=title,
                description=description[:2000],
                source_name="TED (EU Tenders)",
                source_url=notice_url,
                organisation=org or "",
                raw_deadline=str(deadline_raw),
                budget=budget,
            )

    logger.info("TED EU: %d opportunities found", len(opportunities))
    return list(opportunities.values())


def _extract_text(value) -> str:
    """TED returns multilingual objects — prefer English or first available."""
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("ENG") or value.get("NLD") or next(iter(value.values()), "")
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


def _extract_budget(notice: dict) -> str | None:
    val = notice.get("estimatedTotalValue") or notice.get("value")
    if not val:
        return None
    if isinstance(val, dict):
        amount = val.get("amount") or val.get("value")
        currency = val.get("currency", "EUR")
        if amount:
            return f"{currency} {amount:,.0f}"
    if isinstance(val, (int, float)):
        return f"EUR {val:,.0f}"
    return str(val)
