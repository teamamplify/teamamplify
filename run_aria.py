#!/usr/bin/env python3
"""
ARIA — Amplify Research & Intelligence Agent
Entry point for scheduled and manual runs.

Usage:
    python run_aria.py               # Run normally
    python run_aria.py --dry-run     # Search only, skip evaluation and email
    python run_aria.py --help

Environment:
    Copy .env.example to .env and fill in your API keys.
"""
import argparse
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ARIA — Amplify Research & Intelligence Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Search sources only; skip Claude evaluation and email delivery",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Override ARIA_LOOKBACK_DAYS (default: 30)",
    )
    args = parser.parse_args()

    if args.lookback_days:
        os.environ["ARIA_LOOKBACK_DAYS"] = str(args.lookback_days)

    if args.dry_run:
        # Search only — useful for testing source connectivity
        print("DRY RUN MODE — searching sources only, skipping evaluation and email\n")
        from dotenv import load_dotenv
        load_dotenv()
        from aria import history, search, config

        surfaced_ids = history.get_surfaced_ids()
        raw, sources = search.run_all_searches(
            surfaced_ids=surfaced_ids,
            lookback_days=config.SEARCH_LOOKBACK_DAYS,
        )
        print(f"\nDry run complete. Found {len(raw)} raw candidates from:")
        for src in sources:
            print(f"  · {src}")
        print("\nRe-run without --dry-run to evaluate and deliver the report.")
        return

    from aria.main import run
    run()


if __name__ == "__main__":
    main()
