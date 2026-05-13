"""TenderNed (Dutch government procurement) source."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urljoin

from aria.config import DUTCH_KEYWORDS, MAX_RESULTS_PER_SOURCE, SEARCH_LOOKBACK_DAYS
from aria.models import RawOpportunity
from aria.sources.base import get

logger = logging.getLogger(__name__)

# TenderNed public REST API
API_BASE = "https://www.tenderned.nl/tenderned-rs/api/"
SEARCH_URL = urljoin(API_BASE, "aankondigingen/zoeken")
PORTAL_URL = "https://www.tenderned.nl/aankondigingen"


def search(lookback_days: int = SEARCH_LOOKBACK_DAYS) -> List[RawOpportunity]:
    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    opportunities: dict[str, RawOpportunity] = {}

    search_terms = [
        "strategie advies",
        "impact organisatie",
        "monitoring evaluatie",
        "gender advies",
        "verandering transformatie",
        "stakeholder communicatie",
        "capaciteitsopbouw training",
        "verantwoord AI",
    ]

    for term in search_terms:
        try:
            resp = get(
                SEARCH_URL,
                params={
                    "q": term,
                    "publicatieDatumVanaf": cutoff,
                    "pageSize": MAX_RESULTS_PER_SOURCE,
                    "page": 0,
                    "sort": "publicatieDatum,desc",
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("TenderNed search failed for %r: %s", term, exc)
            continue

        items = (
            data.get("content")
            or data.get("aankondigingen")
            or data.get("results")
            or []
        )

        for item in items:
            item_id = str(item.get("id") or item.get("aankondigingId") or "")
            opp_id = f"tenderned-{item_id}"
            if not item_id or opp_id in opportunities:
                continue

            title = item.get("titel") or item.get("title") or item.get("naam") or ""
            org = (
                item.get("aanbestedendeDienst")
                or item.get("organisatie")
                or item.get("opdrachtgever")
                or ""
            )
            if isinstance(org, dict):
                org = org.get("naam") or org.get("name") or ""

            deadline_raw = (
                item.get("sluitingsDatum")
                or item.get("deadline")
                or item.get("inschrijvingsDatum")
                or ""
            )
            budget_raw = item.get("geraamdeWaarde") or item.get("budget")
            budget = f"EUR {budget_raw:,.0f}" if isinstance(budget_raw, (int, float)) else str(budget_raw) if budget_raw else None

            detail_url = (
                item.get("url")
                or item.get("link")
                or f"{PORTAL_URL}/{item_id}"
            )
            description = (
                item.get("omschrijving")
                or item.get("description")
                or item.get("samenvatting")
                or title
            )

            opportunities[opp_id] = RawOpportunity(
                id=opp_id,
                title=title,
                description=str(description)[:2000],
                source_name="TenderNed",
                source_url=detail_url,
                organisation=str(org),
                raw_deadline=str(deadline_raw),
                budget=budget,
            )

    logger.info("TenderNed: %d opportunities found", len(opportunities))
    return list(opportunities.values())
