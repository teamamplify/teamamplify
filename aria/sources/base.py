"""Shared HTTP utilities for source integrations."""
from __future__ import annotations

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "ARIA/1.0 (Amplify Impact Intelligence Agent; "
        "contact: team@amplifyimpact.agency)"
    ),
    "Accept": "application/json, text/html, */*",
}
DEFAULT_TIMEOUT = 20


def get(url: str, params: dict | None = None, **kwargs) -> requests.Response:
    return requests.get(
        url,
        params=params,
        headers=DEFAULT_HEADERS,
        timeout=DEFAULT_TIMEOUT,
        **kwargs,
    )


def post(url: str, json: dict | None = None, **kwargs) -> requests.Response:
    return requests.post(
        url,
        json=json,
        headers={**DEFAULT_HEADERS, "Content-Type": "application/json"},
        timeout=DEFAULT_TIMEOUT,
        **kwargs,
    )
