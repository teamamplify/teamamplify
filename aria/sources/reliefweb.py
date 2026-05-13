"""ReliefWeb API source — international development ToRs and consultancies."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import List

from aria.config import ENGLISH_KEYWORDS, MAX_RESULTS_PER_SOURCE, SEARCH_LOOKBACK_DAYS
from aria.models import RawOpportunity
from aria.sources.base import post

logger = logging.getLogger(__name__)

API_URL = "https://api.reliefweb.int/v1/jobs"
APP_NAME = "aria-amplify-impact"


def search(lookback_days: int = SEARCH_LOOKBACK_DAYS) -> List[RawOpportunity]:
    cutoff = (datetime.utcnow() - timedelta(days=lookback_days)).strftime(
        "%Y-%m-%dT00:00:00+00:00"
    )
    opportunities: dict[str, RawOpportunity] = {}

    # Search a focused set of high-yield terms
    search_terms = [
        "strategy consultancy impact",
        "gender finance advisory",
        "theory of change evaluation",
        "organisational development governance",
        "monitoring evaluation social",
        "capacity building training",
        "advocacy policy influence",
    ]

    for term in search_terms:
        try:
            resp = post(
                API_URL,
                json={
                    "appname": APP_NAME,
                    "filter": {
                        "operator": "AND",
                        "conditions": [
                            {
                                "field": "career_categories.name",
                                "value": ["Consultancy"],
                                "operator": "OR",
                            },
                            {
                                "field": "date.created",
                                "value": {"from": cutoff},
                            },
                        ],
                    },
                    "query": {"value": term, "fields": ["title", "body"]},
                    "fields": {
                        "include": [
                            "title",
                            "body",
                            "date",
                            "url",
                            "source",
                            "deadline",
                            "status",
                        ]
                    },
                    "limit": MAX_RESULTS_PER_SOURCE,
                    "sort": ["date.created:desc"],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("ReliefWeb search failed for %r: %s", term, exc)
            continue

        for item in data.get("data", []):
            f = item.get("fields", {})
            opp_id = f"reliefweb-{item['id']}"
            if opp_id in opportunities:
                continue

            sources = f.get("source") or []
            org = sources[0].get("name", "") if sources else ""

            deadline_val = f.get("deadline")
            if isinstance(deadline_val, dict):
                raw_deadline = deadline_val.get("date", "")
            else:
                raw_deadline = str(deadline_val) if deadline_val else ""

            url = f.get("url", f"https://reliefweb.int/job/{item['id']}")

            opportunities[opp_id] = RawOpportunity(
                id=opp_id,
                title=f.get("title", ""),
                description=(f.get("body") or "")[:2000],
                source_name="ReliefWeb",
                source_url=url,
                organisation=org,
                raw_deadline=raw_deadline,
                budget=None,
            )

    logger.info("ReliefWeb: %d opportunities found", len(opportunities))
    return list(opportunities.values())
