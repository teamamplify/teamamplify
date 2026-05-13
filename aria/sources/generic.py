"""Generic web scrapers for Bond UK, oneworld.nl, DevEx, Pianoo, and others."""
from __future__ import annotations

import logging
import re
from typing import List

from bs4 import BeautifulSoup

from aria.models import RawOpportunity
from aria.sources.base import get

logger = logging.getLogger(__name__)


# ── Bond UK ───────────────────────────────────────────────────────────────────

def search_bond_uk() -> List[RawOpportunity]:
    """Bond UK — UK INGO sector opportunities."""
    opportunities = []
    try:
        resp = get("https://www.bond.org.uk/jobs/?type=consultancy&type=tender")
        soup = BeautifulSoup(resp.text, "lxml")
        for article in soup.select("article.job, .job-listing, .post"):
            link = article.find("a", href=re.compile(r"/jobs/"))
            if not link:
                continue
            title = link.get_text(strip=True)
            url = link["href"]
            if not url.startswith("http"):
                url = "https://www.bond.org.uk" + url
            org_el = article.select_one(".company, .organisation, .employer")
            org = org_el.get_text(strip=True) if org_el else ""
            deadline_el = article.select_one(".deadline, .closing-date, time")
            deadline_raw = deadline_el.get_text(strip=True) if deadline_el else ""
            desc_el = article.select_one(".excerpt, .description, p")
            desc = desc_el.get_text(strip=True) if desc_el else title

            opp_id = f"bond-{hash(url) % 10**8}"
            opportunities.append(
                RawOpportunity(
                    id=opp_id,
                    title=title,
                    description=desc[:1500],
                    source_name="Bond UK",
                    source_url=url,
                    organisation=org,
                    raw_deadline=deadline_raw,
                )
            )
    except Exception as exc:
        logger.warning("Bond UK scrape failed: %s", exc)
    logger.info("Bond UK: %d opportunities found", len(opportunities))
    return opportunities


# ── Oneworld.nl ───────────────────────────────────────────────────────────────

def search_oneworld_nl() -> List[RawOpportunity]:
    """Oneworld.nl vacaturebank — Dutch NGO/social sector ToRs."""
    opportunities = []
    search_terms = ["consultant", "adviseur", "evaluatie", "strategie"]
    seen = set()
    for term in search_terms:
        try:
            resp = get(
                "https://www.oneworld.nl/vacaturebank/",
                params={"s": term, "category": "consultancy"},
            )
            soup = BeautifulSoup(resp.text, "lxml")
            for item in soup.select(".vacancy, article.vacature, .job-item"):
                link = item.find("a", href=True)
                if not link:
                    continue
                url = link["href"]
                if url in seen:
                    continue
                seen.add(url)
                title = link.get_text(strip=True) or item.get_text(strip=True)[:80]
                org_el = item.select_one(".org, .company, .organisatie")
                org = org_el.get_text(strip=True) if org_el else ""
                deadline_el = item.select_one(".deadline, time")
                deadline_raw = deadline_el.get_text(strip=True) if deadline_el else ""
                opp_id = f"oneworld-{hash(url) % 10**8}"
                opportunities.append(
                    RawOpportunity(
                        id=opp_id,
                        title=title,
                        description=title,
                        source_name="Oneworld.nl",
                        source_url=url,
                        organisation=org,
                        raw_deadline=deadline_raw,
                    )
                )
        except Exception as exc:
            logger.warning("Oneworld.nl scrape failed for %r: %s", term, exc)
    logger.info("Oneworld.nl: %d opportunities found", len(opportunities))
    return opportunities


# ── Impactpool ────────────────────────────────────────────────────────────────

def search_impactpool() -> List[RawOpportunity]:
    """Impactpool — impact sector roles and tenders."""
    opportunities = []
    try:
        resp = get(
            "https://www.impactpool.org/jobs",
            params={
                "keywords": "consultancy strategy impact",
                "job_type": "consultancy",
            },
        )
        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select(".job-card, .job-listing, article"):
            link = item.find("a", href=re.compile(r"/jobs/\d+"))
            if not link:
                continue
            url = link["href"]
            if not url.startswith("http"):
                url = "https://www.impactpool.org" + url
            title = link.get_text(strip=True)
            org_el = item.select_one(".organization, .company, .org-name")
            org = org_el.get_text(strip=True) if org_el else ""
            deadline_el = item.select_one(".deadline, .closing-date, time")
            deadline_raw = deadline_el.get_text(strip=True) if deadline_el else ""
            desc_el = item.select_one(".description, .excerpt, p")
            desc = desc_el.get_text(strip=True) if desc_el else title
            opp_id = f"impactpool-{hash(url) % 10**8}"
            opportunities.append(
                RawOpportunity(
                    id=opp_id,
                    title=title,
                    description=desc[:1500],
                    source_name="Impactpool",
                    source_url=url,
                    organisation=org,
                    raw_deadline=deadline_raw,
                )
            )
    except Exception as exc:
        logger.warning("Impactpool scrape failed: %s", exc)
    logger.info("Impactpool: %d opportunities found", len(opportunities))
    return opportunities


# ── DevEx ─────────────────────────────────────────────────────────────────────

def search_devex() -> List[RawOpportunity]:
    """DevEx — international development sector opportunities."""
    opportunities = []
    try:
        resp = get(
            "https://www.devex.com/jobs/search",
            params={
                "q": "strategy impact consultancy",
                "type[]": "consultancy",
                "location": "",
            },
            headers={
                "Accept": "text/html",
                "User-Agent": "Mozilla/5.0 ARIA/1.0",
            },
        )
        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select(".job-card, article.job, .result-item"):
            link = item.find("a", href=re.compile(r"/jobs/\d+"))
            if not link:
                continue
            url = link["href"]
            if not url.startswith("http"):
                url = "https://www.devex.com" + url
            title = link.get_text(strip=True)
            org_el = item.select_one(".organization, .company")
            org = org_el.get_text(strip=True) if org_el else ""
            deadline_el = item.select_one(".deadline, time")
            deadline_raw = deadline_el.get_text(strip=True) if deadline_el else ""
            opp_id = f"devex-{hash(url) % 10**8}"
            opportunities.append(
                RawOpportunity(
                    id=opp_id,
                    title=title,
                    description=title,
                    source_name="DevEx",
                    source_url=url,
                    organisation=org,
                    raw_deadline=deadline_raw,
                )
            )
    except Exception as exc:
        logger.warning("DevEx scrape failed: %s", exc)
    logger.info("DevEx: %d opportunities found", len(opportunities))
    return opportunities


# ── Pianoo ────────────────────────────────────────────────────────────────────

def search_pianoo() -> List[RawOpportunity]:
    """Pianoo — Dutch public procurement intelligence."""
    opportunities = []
    try:
        resp = get(
            "https://www.pianoo.nl/nl/overheidsopdrachten/aanbestedingen",
            params={"search_api_fulltext": "strategie advies impact organisatie"},
        )
        soup = BeautifulSoup(resp.text, "lxml")
        for item in soup.select("article, .aanbesteding-item, .result"):
            link = item.find("a", href=True)
            if not link or not link.get("href"):
                continue
            url = link["href"]
            if not url.startswith("http"):
                url = "https://www.pianoo.nl" + url
            title = link.get_text(strip=True)
            if not title:
                continue
            opp_id = f"pianoo-{hash(url) % 10**8}"
            opportunities.append(
                RawOpportunity(
                    id=opp_id,
                    title=title,
                    description=title,
                    source_name="Pianoo",
                    source_url=url,
                    organisation="Dutch Government",
                    raw_deadline="",
                )
            )
    except Exception as exc:
        logger.warning("Pianoo scrape failed: %s", exc)
    logger.info("Pianoo: %d opportunities found", len(opportunities))
    return opportunities
