"""Report generation — plain text and dark-themed HTML email."""
from __future__ import annotations

from datetime import datetime
from typing import List

from aria.models import Opportunity, RunResult


# ── Plain text report ─────────────────────────────────────────────────────────

def generate_text(result: RunResult) -> str:
    lines = [
        "━" * 50,
        "ARIA INTELLIGENCE REPORT",
        f"Amplify Impact | {result.date.strftime('%d %B %Y')} | Run #{result.run_number}",
        "━" * 50,
        "",
        "EXECUTIVE SUMMARY",
        _executive_summary(result),
        "",
    ]

    if result.priority:
        lines += [
            "━" * 50,
            "PRIORITY OPPORTUNITIES (Score 8-10 | Act immediately)",
            "━" * 50,
            "",
        ]
        for i, opp in enumerate(result.priority, 1):
            lines += _text_priority_card(i, opp)

    if result.pipeline:
        lines += [
            "━" * 50,
            "PIPELINE OPPORTUNITIES (Score 6-7 | Worth monitoring)",
            "━" * 50,
            "",
        ]
        for opp in result.pipeline:
            lines.append(
                f"• {opp.title} | {opp.organisation} | "
                f"{opp.source_name} | Deadline: {opp.deadline_display} | "
                f"Score: {opp.overall_score}/10"
            )
        lines.append("")

    if not result.opportunities:
        lines.append("No qualifying opportunities found this run.")
        lines.append("")

    lines += [
        "━" * 50,
        "INTELLIGENCE NOTES",
        "━" * 50,
        "",
        f"SOURCES SEARCHED: {', '.join(result.sources_searched)}",
        f"TOTAL CANDIDATES REVIEWED: {result.total_raw}",
        f"QUALIFIED OPPORTUNITIES: {result.total_scored}",
        "",
        f"NEXT RUN RECOMMENDED: {_next_run_date(result.date)}",
        "",
        "━" * 50,
        f"Sent by ARIA — Amplify Impact Intelligence Agent | {result.date.strftime('%d %b %Y')} | Run #{result.run_number}",
    ]

    return "\n".join(lines)


def _executive_summary(result: RunResult) -> str:
    total = len(result.opportunities)
    priority_count = len(result.priority)
    pipeline_count = len(result.pipeline)

    if total == 0:
        return (
            f"ARIA completed a full scan across {len(result.sources_searched)} sources "
            f"reviewing {result.total_raw} candidates. No opportunities met the quality "
            "threshold this run — market activity may be low or seasonal. "
            "Standing sources will be rescanned on the next scheduled run."
        )

    themes = _detect_themes(result.opportunities)
    theme_str = f" Key themes this run: {', '.join(themes)}." if themes else ""

    return (
        f"ARIA surfaced {total} qualifying opportunities from "
        f"{len(result.sources_searched)} sources ({result.total_raw} candidates reviewed). "
        f"{priority_count} {'opportunity requires' if priority_count == 1 else 'opportunities require'} "
        f"immediate action; {pipeline_count} {'is' if pipeline_count == 1 else 'are'} worth monitoring."
        f"{theme_str}"
    )


def _detect_themes(opps: List[Opportunity]) -> List[str]:
    theme_map = {
        "gender finance": ["gender", "2x", "women", "feminist"],
        "AI governance": ["ai", "artificial intelligence", "responsible ai", "digital"],
        "impact measurement": ["impact measurement", "theory of change", "monitoring", "evaluation"],
        "public sector": ["government", "ministry", "public sector", "overheid"],
        "international development": ["development", "ingo", "ngo", "global south"],
        "organisational transformation": ["transformation", "organisational", "governance", "strategy"],
    }
    found = []
    all_text = " ".join(
        f"{o.title} {o.description}".lower() for o in opps
    )
    for theme, keywords in theme_map.items():
        if any(kw in all_text for kw in keywords):
            found.append(theme)
    return found[:4]


def _text_priority_card(index: int, opp: Opportunity) -> List[str]:
    lines = [
        f"{index}. {opp.title}",
        f"   Organisation: {opp.organisation or 'Not specified'}",
        f"   Source: {opp.source_name} — {opp.source_url}",
        f"   Category: {opp.category}",
        f"   Deadline: {opp.deadline_display} {opp.deadline_urgency}",
        f"   Budget: {opp.budget or 'Not specified'}",
        f"   Fit Score: {opp.overall_score}/10",
        f"   (Relevance: {opp.relevance} | Track Record: {opp.track_record} | "
        f"Win Prob: {opp.win_probability} | Strategic: {opp.strategic_value})",
    ]
    if opp.why_this_fits:
        lines += ["", f"   WHY THIS FITS: {opp.why_this_fits}"]
    if opp.lead_with:
        lines += [f"   LEAD WITH: {opp.lead_with}"]
    if opp.consortium_needed:
        lines += [f"   CONSORTIUM NEEDED: {opp.consortium_needed}"]
    if opp.suggested_first_move:
        lines += [f"   SUGGESTED FIRST MOVE: {opp.suggested_first_move}"]
    lines.append("")
    return lines


def _next_run_date(from_date: datetime) -> str:
    from datetime import timedelta
    next_run = from_date + timedelta(days=7)
    return next_run.strftime("%d %B %Y")


# ── HTML email report ─────────────────────────────────────────────────────────

def generate_html(result: RunResult) -> str:
    priority_cards = "".join(_html_priority_card(i, opp) for i, opp in enumerate(result.priority, 1))
    pipeline_rows = "".join(_html_pipeline_row(opp) for opp in result.pipeline)

    pipeline_section = ""
    if result.pipeline:
        pipeline_section = f"""
        <table style="width:100%;border-collapse:collapse;margin-bottom:24px;">
          <thead>
            <tr style="border-bottom:1px solid #1E3A5F;">
              <th style="text-align:left;padding:8px 4px;color:#F97316;font-size:13px;">Opportunity</th>
              <th style="text-align:left;padding:8px 4px;color:#F97316;font-size:13px;">Organisation</th>
              <th style="text-align:left;padding:8px 4px;color:#F97316;font-size:13px;">Deadline</th>
              <th style="text-align:center;padding:8px 4px;color:#F97316;font-size:13px;">Score</th>
            </tr>
          </thead>
          <tbody>
            {pipeline_rows}
          </tbody>
        </table>
        """

    no_opps_msg = ""
    if not result.opportunities:
        no_opps_msg = """
        <div style="background:#112240;border-left:3px solid #F97316;padding:16px;
                    border-radius:4px;margin-bottom:24px;">
          <p style="margin:0;color:#94A3B8;font-style:italic;">
            No qualifying opportunities found this run. ARIA reviewed
            {total_raw} candidates across {source_count} sources —
            all were below the quality threshold or already surfaced.
          </p>
        </div>
        """.format(total_raw=result.total_raw, source_count=len(result.sources_searched))

    score_badge_style = (
        "display:inline-block;background:#F97316;color:#0D1B2A;"
        "font-weight:700;font-size:18px;padding:6px 14px;"
        "border-radius:20px;margin-bottom:12px;"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>ARIA Intelligence Report — {result.date.strftime('%d %B %Y')}</title>
</head>
<body style="margin:0;padding:0;background:#0D1B2A;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#FFFFFF;">

  <!-- Header -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0B1829;border-bottom:2px solid #F97316;">
    <tr>
      <td style="padding:32px 40px;">
        <div style="font-size:11px;letter-spacing:3px;color:#F97316;text-transform:uppercase;margin-bottom:8px;">
          Amplify Impact Intelligence
        </div>
        <div style="font-size:26px;font-weight:700;color:#FFFFFF;margin-bottom:4px;">
          ARIA Intelligence Report
        </div>
        <div style="font-size:13px;color:#94A3B8;">
          {result.date.strftime('%d %B %Y')} &nbsp;·&nbsp; Run #{result.run_number}
          &nbsp;·&nbsp; {len(result.opportunities)} qualifying opportunities
        </div>
      </td>
    </tr>
  </table>

  <div style="max-width:700px;margin:0 auto;padding:32px 20px;">

    <!-- Executive Summary -->
    <div style="background:#112240;border-radius:8px;padding:24px;margin-bottom:32px;">
      <div style="font-size:11px;letter-spacing:2px;color:#F97316;text-transform:uppercase;margin-bottom:12px;">
        Executive Summary
      </div>
      <p style="margin:0;line-height:1.7;color:#CBD5E1;font-size:15px;">
        {_executive_summary(result)}
      </p>
    </div>

    <!-- Priority Opportunities -->
    {"" if not result.priority else _html_section_header("Priority Opportunities", "Score 8–10 · Act immediately")}
    {priority_cards}
    {no_opps_msg}

    <!-- Pipeline Opportunities -->
    {"" if not result.pipeline else _html_section_header("Pipeline Opportunities", "Score 6–7 · Worth monitoring")}
    {pipeline_section}

    <!-- Intelligence Notes -->
    {_html_section_header("Intelligence Notes", "Sources &amp; signals")}
    <div style="background:#112240;border-radius:8px;padding:24px;margin-bottom:24px;">
      <div style="margin-bottom:16px;">
        <span style="color:#F97316;font-size:12px;font-weight:600;text-transform:uppercase;
                     letter-spacing:1px;">Sources Searched</span>
        <p style="margin:6px 0 0;color:#CBD5E1;font-size:14px;line-height:1.6;">
          {' &nbsp;·&nbsp; '.join(result.sources_searched)}
        </p>
      </div>
      <div style="border-top:1px solid #1E3A5F;padding-top:16px;margin-top:16px;">
        <span style="color:#F97316;font-size:12px;font-weight:600;text-transform:uppercase;
                     letter-spacing:1px;">Run Statistics</span>
        <p style="margin:6px 0 0;color:#CBD5E1;font-size:14px;">
          Candidates reviewed: <strong style="color:#FFFFFF;">{result.total_raw}</strong>
          &nbsp;·&nbsp;
          Qualified: <strong style="color:#FFFFFF;">{result.total_scored}</strong>
          &nbsp;·&nbsp;
          Priority: <strong style="color:#F97316;">{len(result.priority)}</strong>
        </p>
      </div>
      <div style="border-top:1px solid #1E3A5F;padding-top:16px;margin-top:16px;">
        <span style="color:#F97316;font-size:12px;font-weight:600;text-transform:uppercase;
                     letter-spacing:1px;">Next Run Recommended</span>
        <p style="margin:6px 0 0;color:#CBD5E1;font-size:14px;">
          {_next_run_date(result.date)}
        </p>
      </div>
    </div>

  </div>

  <!-- Footer -->
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#071224;border-top:1px solid #1E3A5F;margin-top:16px;">
    <tr>
      <td style="padding:20px 40px;text-align:center;">
        <div style="font-size:12px;color:#475569;">
          Sent by <strong style="color:#F97316;">ARIA</strong> — Amplify Impact Intelligence Agent
          &nbsp;·&nbsp; {result.date.strftime('%d %b %Y')} &nbsp;·&nbsp; Run #{result.run_number}
        </div>
      </td>
    </tr>
  </table>

</body>
</html>"""


def _html_section_header(title: str, subtitle: str) -> str:
    return f"""
    <div style="margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid #1E3A5F;">
      <div style="font-size:16px;font-weight:700;color:#F97316;">{title}</div>
      <div style="font-size:12px;color:#64748B;margin-top:2px;">{subtitle}</div>
    </div>
    """


def _html_priority_card(index: int, opp: Opportunity) -> str:
    urgency = opp.deadline_urgency
    score_color = "#22C55E" if opp.overall_score >= 8.5 else "#F97316"

    enrichment_html = ""
    if opp.why_this_fits or opp.lead_with or opp.consortium_needed or opp.suggested_first_move:
        rows = []
        if opp.why_this_fits:
            rows.append(_html_detail_row("Why this fits", opp.why_this_fits))
        if opp.lead_with:
            rows.append(_html_detail_row("Lead with", opp.lead_with))
        if opp.consortium_needed:
            rows.append(_html_detail_row("Consortium needed", opp.consortium_needed))
        if opp.suggested_first_move:
            rows.append(_html_detail_row("Suggested first move", opp.suggested_first_move, highlight=True))
        enrichment_html = f"""
        <div style="margin-top:16px;padding-top:16px;border-top:1px solid #1E3A5F;">
          {"".join(rows)}
        </div>"""

    return f"""
    <div style="background:#112240;border-radius:8px;margin-bottom:20px;
                border-left:4px solid {score_color};overflow:hidden;">
      <!-- Card header -->
      <div style="padding:20px 24px 16px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;
                    margin-bottom:12px;">
          <div style="font-size:12px;color:#64748B;text-transform:uppercase;
                      letter-spacing:1px;">{index}. {opp.category}</div>
          <div style="background:{score_color};color:#0D1B2A;font-weight:700;
                      font-size:15px;padding:4px 12px;border-radius:16px;
                      white-space:nowrap;margin-left:12px;">
            {opp.overall_score}/10
          </div>
        </div>
        <div style="font-size:17px;font-weight:600;color:#FFFFFF;margin-bottom:8px;
                    line-height:1.4;">
          <a href="{opp.source_url}" style="color:#FFFFFF;text-decoration:none;">
            {opp.title}
          </a>
        </div>
        <div style="font-size:13px;color:#94A3B8;margin-bottom:12px;">
          {opp.organisation or "Organisation not specified"}
          &nbsp;·&nbsp; {opp.source_name}
        </div>

        <!-- Meta row -->
        <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:12px;">
          <span style="color:#94A3B8;">
            📅 <strong style="color:#CBD5E1;">Deadline:</strong>
            {opp.deadline_display} {urgency}
          </span>
          {"" if not opp.budget else f'<span style="color:#94A3B8;">💰 <strong style="color:#CBD5E1;">Budget:</strong> {opp.budget}</span>'}
        </div>

        <!-- Score breakdown -->
        <div style="margin-top:12px;font-size:11px;color:#64748B;">
          Relevance {opp.relevance}/10 &nbsp;·&nbsp;
          Track record {opp.track_record}/10 &nbsp;·&nbsp;
          Win prob {opp.win_probability}/10 &nbsp;·&nbsp;
          Strategic {opp.strategic_value}/10
        </div>

        {enrichment_html}

        <div style="margin-top:16px;">
          <a href="{opp.source_url}"
             style="display:inline-block;background:#F97316;color:#0D1B2A;
                    font-weight:600;font-size:13px;padding:8px 20px;
                    border-radius:6px;text-decoration:none;">
            View Opportunity →
          </a>
        </div>
      </div>
    </div>"""


def _html_detail_row(label: str, content: str, highlight: bool = False) -> str:
    color = "#F97316" if highlight else "#94A3B8"
    return f"""
    <div style="margin-bottom:10px;">
      <div style="font-size:11px;font-weight:600;color:{color};text-transform:uppercase;
                  letter-spacing:1px;margin-bottom:3px;">{label}</div>
      <div style="font-size:13px;color:#CBD5E1;line-height:1.6;">{content}</div>
    </div>"""


def _html_pipeline_row(opp: Opportunity) -> str:
    return f"""
    <tr style="border-bottom:1px solid #112240;">
      <td style="padding:10px 4px;font-size:13px;">
        <a href="{opp.source_url}" style="color:#93C5FD;text-decoration:none;">
          {opp.title[:65]}{"…" if len(opp.title) > 65 else ""}
        </a>
      </td>
      <td style="padding:10px 4px;font-size:12px;color:#94A3B8;">
        {(opp.organisation or "")[:30]}
      </td>
      <td style="padding:10px 4px;font-size:12px;color:#94A3B8;white-space:nowrap;">
        {opp.deadline_display} {opp.deadline_urgency}
      </td>
      <td style="padding:10px 4px;text-align:center;">
        <span style="background:#1E3A5F;color:#F97316;font-weight:700;
                     font-size:12px;padding:3px 8px;border-radius:12px;">
          {opp.overall_score}
        </span>
      </td>
    </tr>"""
