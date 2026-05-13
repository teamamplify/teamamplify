"""Configuration constants for ARIA."""
import os

# ── Scoring ──────────────────────────────────────────────────────────────────

SCORING_WEIGHTS = {
    "relevance": 0.30,
    "track_record": 0.25,
    "win_probability": 0.25,
    "strategic_value": 0.20,
}

SCORE_THRESHOLD = 6.0
ENRICHMENT_THRESHOLD = 8.0

# ── Search ───────────────────────────────────────────────────────────────────

SEARCH_LOOKBACK_DAYS = int(os.getenv("ARIA_LOOKBACK_DAYS", "30"))
MAX_RESULTS_PER_SOURCE = 20

# ── Email ────────────────────────────────────────────────────────────────────

FROM_EMAIL = os.getenv("FROM_EMAIL", "team@amplifyimpact.agency")
TO_EMAIL = os.getenv("TO_EMAIL", "whitney@amplifyimpact.today")

# ── Models ───────────────────────────────────────────────────────────────────

CLAUDE_MODEL = "claude-sonnet-4-6"

# ── Paths ────────────────────────────────────────────────────────────────────

HISTORY_FILE = os.getenv(
    "ARIA_HISTORY_FILE",
    os.path.join(os.path.dirname(__file__), "data", "run_history.json"),
)

# ── Amplify Impact Profile (used as Claude evaluation context) ───────────────

AMPLIFY_PROFILE = """
ORGANISATION: Amplify Impact B.V.
FOUNDER: Whitney van Schyndel (Global 100 recognised)
CORE PHILOSOPHY: "From impact as framework… to impact as fabric."

Amplify Impact works at the highest strategic levels of government, public sector, and
international development. They are NOT an auditing firm — they partner with audit, legal
and IT governance specialists for large tenders. They lead consortia and convene the right
partners per brief.

WORKS WITH:
- National government ministries and public execution bodies (ZBOs, agencies,
  uitvoeringsorganisaties)
- International development organisations and programmes
- Development finance institutions and gender finance bodies
- INGOs, NGOs and civil society organisations
- Multi-country employment, education and social service organisations
- Impact-focused foundations and philanthropic bodies
- Social enterprises and mission-driven businesses

PROVEN EXPERTISE (these are the areas where Amplify Impact is genuinely competitive):
- Strategy & transformation at board/RvB level
- Advocacy strategy & policy influence
- Gender lens investing & gender finance
- Impact communications, narratives & case studies
- Stakeholder engagement & co-creation
- Monitoring, evaluation & impact reporting
- Social impact measurement — Theory of Change, Impact Measurement Frameworks,
  data architecture for impact, embedding impact culture
- Organisational design — governance, learning systems, decision-making infrastructure,
  change management
- Responsible AI strategy in public and social sector contexts
- Global impact reporting
- Consortium leadership and partnership coordination
- Capacity building, training & competency development
- Award submissions & recognition strategy

KEY PAST CLIENTS & COMPARABLE WORK (use these for track record scoring):
- UWV — European tender, strategic & tactical advisory, responsible AI strategy.
  Led IMPACT@WORK consortium. (Public sector / employment / AI governance)
- 2X Global — gender finance communications & investee support (gender finance)
- Justice & Peace Nederland — advocacy strategy (advocacy / civil society)
- The BUSY Group (AU/UK/NZ/CA) — global Theory of Change, Impact Measurement
  Framework, data architecture (multi-country IMF / ToC)
- Kifiya Financial Technology PLC — impact reporting (fintech / social enterprise)
- Challenge Fund for Youth Employment / Min. Buitenlandse Zaken (€135M, 11 countries,
  230,000 jobs) (international development / employment / M&E)
- Department for Work & Pensions (UK), FCDO, Min. Buitenlandse Zaken NL
  (public sector transformation)
- COA — organisational and procurement advisory (Dutch public sector)
- Openbaar Ministerie NL — mandate restructuring & governance (Dutch public sector)
- Gemeente Amsterdam — strategic communications & participation
- Australian Dept. of Social Services — outcome measurement

CONTRACT RANGE: €15,000 – €150,000+
LANGUAGES: Dutch and English
GEOGRAPHIC SCOPE: Netherlands + international

WHAT AMPLIFY IMPACT DOES NOT DO (exclude these):
- Pure auditing, accounting, or legal compliance work
- Pure private sector commercial work with no social impact, governance or
  transformation dimension
- Highly technical IT implementation (they advise on AI/digital strategy, not build systems)
"""

# ── EU CPV codes relevant to Amplify Impact's services ───────────────────────

RELEVANT_CPV_CODES = [
    "79400000",  # Business and management consultancy
    "79410000",  # General business and management consultancy
    "79411000",  # General management consultancy
    "79411100",  # Business development consultancy
    "79416000",  # Public relations services
    "73200000",  # Research and development consultancy
    "79315000",  # Social research services
    "79320000",  # Public opinion survey services
    "79421000",  # Project management services
    "85300000",  # Social work and related services
    "85320000",  # Social services
    "80500000",  # Training services
    "72220000",  # Systems and technical consultancy services
]

# ── Search keywords ───────────────────────────────────────────────────────────

DUTCH_KEYWORDS = [
    "strategie advies organisatie",
    "impact meting theorie verandering",
    "gender finance investering",
    "maatschappelijke impact advies",
    "transformatie verandermanagement",
    "stakeholder engagement beleid",
    "monitoring evaluatie",
    "verantwoord AI publieke sector",
    "capaciteitsopbouw training",
    "organisatieontwikkeling governance",
]

ENGLISH_KEYWORDS = [
    "strategy consultancy social impact",
    "impact measurement theory of change",
    "gender lens investing finance",
    "organisational development governance",
    "monitoring evaluation international development",
    "responsible AI strategy public sector",
    "advocacy strategy policy influence",
    "stakeholder engagement co-creation",
    "capacity building training development",
    "social impact reporting",
]
