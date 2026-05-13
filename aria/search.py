"""Search orchestrator — runs all sources and deduplicates results."""
from __future__ import annotations

import logging
from typing import List, Set, Tuple

from aria.config import SEARCH_LOOKBACK_DAYS
from aria.models import RawOpportunity
from aria.sources import generic, reliefweb, ted, tenderned, ungm

logger = logging.getLogger(__name__)


def run_all_searches(
    surfaced_ids: Set[str],
    lookback_days: int = SEARCH_LOOKBACK_DAYS,
) -> Tuple[List[RawOpportunity], List[str]]:
    """
    Execute all source searches, deduplicate, and exclude already-surfaced IDs.

    Returns:
        (opportunities, sources_searched)
    """
    sources = [
        ("ReliefWeb", lambda: reliefweb.search(lookback_days)),
        ("TED EU Tenders", lambda: ted.search(lookback_days)),
        ("TenderNed", lambda: tenderned.search(lookback_days)),
        ("UNGM", lambda: ungm.search(lookback_days)),
        ("Bond UK", generic.search_bond_uk),
        ("Oneworld.nl", generic.search_oneworld_nl),
        ("Impactpool", generic.search_impactpool),
        ("DevEx", generic.search_devex),
        ("Pianoo", generic.search_pianoo),
    ]

    all_raw: dict[str, RawOpportunity] = {}
    sources_searched: List[str] = []

    for source_name, search_fn in sources:
        logger.info("Searching %s...", source_name)
        try:
            results = search_fn()
            sources_searched.append(source_name)
            for opp in results:
                if opp.id not in all_raw and opp.id not in surfaced_ids:
                    if _is_valid(opp):
                        all_raw[opp.id] = opp
        except Exception as exc:
            logger.error("Source %s failed: %s", source_name, exc)
            sources_searched.append(f"{source_name} (error)")

    logger.info(
        "Search complete: %d unique new opportunities from %d sources",
        len(all_raw),
        len(sources),
    )
    return list(all_raw.values()), sources_searched


def _is_valid(opp: RawOpportunity) -> bool:
    """Minimal validity check — must have a title and a URL."""
    return bool(opp.title and opp.title.strip() and opp.source_url)
