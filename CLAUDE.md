# ARIA — Amplify Research & Intelligence Agent

Autonomous opportunity intelligence agent for Amplify Impact B.V.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
python run_aria.py
```

## Run modes

```bash
python run_aria.py                      # Full run: search → evaluate → email
python run_aria.py --dry-run            # Search only (test source connectivity)
python run_aria.py --lookback-days 14   # Override lookback window
```

## Required environment variables

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API for opportunity scoring |
| `SENDGRID_API_KEY` | Email delivery (primary) |
| `FROM_EMAIL` | Sender address |
| `TO_EMAIL` | Recipient address |

SMTP fallback: set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`.

If neither SendGrid nor SMTP is configured, reports are saved to `aria/data/reports/`.

## Architecture

```
aria/
  config.py       # Constants, Amplify profile, scoring weights
  models.py       # RawOpportunity, Opportunity, RunResult dataclasses
  history.py      # Run deduplication (aria/data/run_history.json)
  search.py       # Orchestrates all source searches
  evaluate.py     # Claude-powered FIT SCORING PROTOCOL
  report.py       # Plain text + dark-themed HTML report generation
  emailer.py      # SendGrid → SMTP → file fallback delivery
  main.py         # Main ARIA orchestrator
  sources/
    reliefweb.py  # ReliefWeb API (international development ToRs)
    ted.py        # TED EU tenders REST API
    tenderned.py  # Dutch government procurement API
    ungm.py       # UN Global Marketplace scraper
    generic.py    # Bond UK, Oneworld.nl, Impactpool, DevEx, Pianoo
run_aria.py       # CLI entry point
```

## Scoring model

Opportunities are scored across 4 dimensions (weighted average must be ≥ 6.0):

| Dimension | Weight |
|---|---|
| Relevance | 30% |
| Track Record | 25% |
| Win Probability | 25% |
| Strategic Value | 20% |

Opportunities scoring ≥ 8.0 receive full enrichment (WHY THIS FITS, LEAD WITH, CONSORTIUM NEEDED, SUGGESTED FIRST MOVE).

## Scheduling

For automated weekly runs, add to crontab:
```
0 7 * * MON cd /path/to/teamamplify && python run_aria.py >> aria/data/aria.log 2>&1
```
