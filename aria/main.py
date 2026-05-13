"""ARIA main orchestrator — plan, search, evaluate, report, deliver."""
from __future__ import annotations

import logging
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from aria import config
from aria import emailer, evaluate, history, report, search
from aria.models import RunResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aria")


def run() -> RunResult:
    run_date = datetime.utcnow()
    run_number = history.get_run_number()
    surfaced_ids = history.get_surfaced_ids()

    print(f"\nARIA activated. Planning search strategy for {run_date.strftime('%d %B %Y')}...")
    print(f"Run #{run_number} | {len(surfaced_ids)} opportunities in history (will skip duplicates)\n")

    # ── STEP 1: PLAN ─────────────────────────────────────────────────────────
    logger.info("=== STEP 1: PLAN ===")
    logger.info(
        "Targeting: ToRs, public tenders, speaking gigs, and partnership calls. "
        "Seasonal note: May is typically active for Q2 tender cycles in NL/EU."
    )
    logger.info("Sources: ReliefWeb, TED EU, TenderNed, UNGM, Bond UK, Oneworld.nl, Impactpool, DevEx, Pianoo")

    # ── STEP 2: SEARCH ───────────────────────────────────────────────────────
    logger.info("=== STEP 2: SEARCH ===")
    raw_opportunities, sources_searched = search.run_all_searches(
        surfaced_ids=surfaced_ids,
        lookback_days=config.SEARCH_LOOKBACK_DAYS,
    )
    total_raw = len(raw_opportunities)
    logger.info("Raw candidates after dedup: %d", total_raw)

    # ── STEP 3 & 4: EVALUATE & ENRICH ────────────────────────────────────────
    logger.info("=== STEPS 3–4: EVALUATE & ENRICH ===")
    if os.getenv("ANTHROPIC_API_KEY"):
        scored_opportunities = evaluate.evaluate_all(raw_opportunities)
    else:
        logger.warning(
            "ANTHROPIC_API_KEY not set — skipping Claude evaluation. "
            "Set the key to enable intelligent scoring."
        )
        scored_opportunities = []

    total_scored = len(scored_opportunities)

    result = RunResult(
        run_number=run_number,
        date=run_date,
        opportunities=scored_opportunities,
        sources_searched=sources_searched,
        total_raw=total_raw,
        total_scored=total_scored,
    )

    # ── STEP 5: REPORT & DELIVER ─────────────────────────────────────────────
    logger.info("=== STEP 5: REPORT & DELIVER ===")
    html_body = report.generate_html(result)
    text_body = report.generate_text(result)

    if scored_opportunities:
        subject = (
            f"ARIA Intelligence Report — {run_date.strftime('%d %b %Y')} "
            f"| {total_scored} {'opportunity' if total_scored == 1 else 'opportunities'} found"
        )
    else:
        subject = (
            f"ARIA Report — {run_date.strftime('%d %b %Y')} "
            "| No qualifying opportunities this run"
        )

    delivered = emailer.send(
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        from_email=config.FROM_EMAIL,
        to_email=config.TO_EMAIL,
    )

    # ── Record run ───────────────────────────────────────────────────────────
    history.record_run(
        run_number=run_number,
        opportunity_ids=[o.id for o in scored_opportunities],
        opportunity_count=total_scored,
        date=run_date,
    )

    # ── Confirmation ─────────────────────────────────────────────────────────
    delivery_status = "delivered" if delivered else "FAILED TO DELIVER"
    next_run = report._next_run_date(run_date)

    print(
        f"\nARIA report {delivery_status} to {config.TO_EMAIL} — "
        f"{total_scored} {'opportunity' if total_scored == 1 else 'opportunities'} surfaced. "
        f"Next run: {next_run}."
    )

    if result.priority:
        print(f"\n🔥 {len(result.priority)} PRIORITY opportunity/ies requiring immediate action:")
        for opp in result.priority:
            print(f"   [{opp.overall_score}/10] {opp.title} ({opp.deadline_display})")

    return result
