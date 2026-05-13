"""Run history — tracks surfaced opportunities to prevent duplicates."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Set

from aria.config import HISTORY_FILE


def _load() -> dict:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return {"run_count": 0, "surfaced_ids": [], "runs": []}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


def get_run_number() -> int:
    return _load()["run_count"] + 1


def get_surfaced_ids() -> Set[str]:
    return set(_load()["surfaced_ids"])


def record_run(
    run_number: int,
    opportunity_ids: list[str],
    opportunity_count: int,
    date: datetime,
) -> None:
    data = _load()
    data["run_count"] = run_number
    # Add new IDs, keeping a rolling window of last 500 to avoid unbounded growth
    all_ids = list(set(data["surfaced_ids"]) | set(opportunity_ids))
    data["surfaced_ids"] = all_ids[-500:]
    data["runs"].append(
        {
            "run_number": run_number,
            "date": date.isoformat(),
            "opportunities_surfaced": opportunity_count,
        }
    )
    _save(data)
