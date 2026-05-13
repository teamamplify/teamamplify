"""UNGM (UN Global Marketplace) procurement notices source."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import List

from bs4 import BeautifulSoup

from aria.config import MAX_RESULTS_PER_SOURCE, SEARCH_LOOKBACK_DAYS
from aria.models import RawOpportunity
from aria.sources.base import get

logger = logging.getLogger(__name__)

SEARCH_URL = "https://www.ungm.org/Public/Notice"
BASE_URL = "https://www.ungm.org"


def search(lookback_days: int = SEARCH_LOOKBACK_DAYS) -> List[RawOpportunity]:
    opportunities: dict[str, RawOpportunity] = {}

    search_terms = [
        "strategy consultancy",
        "impact measurement",
        "gender advisory",
        "monitoring evaluation",
        "organisational development",
        "capacity building",
        "theory of change",
    ]

    for term in search_terms:
        try:
            resp = get(
                SEARCH_URL,
                params={
                    "Keywords": term,
                    "DeadlineFrom": (datetime.utcnow() - timedelta(days=1)).strftime("%m/%d/%Y"),
                    "PageIndex": 0,
                    "PageSize": MAX_RESULTS_PER_SOURCE,
                },
                headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "User-Agent": "Mozilla/5.0 ARIA/1.0",
                },
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
        except Exception as exc:
            logger.warning("UNGM search failed for %r: %s", term, exc)
            continue

        # Parse notice rows from the UNGM HTML table
        for row in soup.select("table.tablesorter tbody tr, .notice-row, .tbl-notices tr"):
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            link_tag = row.find("a", href=re.compile(r"/Public/Notice/\d+"))
            if not link_tag:
                continue

            notice_id = re.search(r"/Public/Notice/(\d+)", link_tag["href"])
            if not notice_id:
                continue

            opp_id = f"ungm-{notice_id.group(1)}"
            if opp_id in opportunities:
                continue

            title = link_tag.get_text(strip=True)
            url = BASE_URL + link_tag["href"]
            text_cells = [c.get_text(strip=True) for c in cells]

            # Try to extract org and deadline from cells
            org = text_cells[1] if len(text_cells) > 1 else ""
            deadline_raw = text_cells[-1] if text_cells else ""

            opportunities[opp_id] = RawOpportunity(
                id=opp_id,
                title=title,
                description=title,
                source_name="UNGM (UN Procurement)",
                source_url=url,
                organisation=org,
                raw_deadline=deadline_raw,
                budget=None,
            )

    logger.info("UNGM: %d opportunities found", len(opportunities))
    return list(opportunities.values())
