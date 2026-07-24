# Amplitude GTM Pipeline — Finding What Databases Can't Filter

> **[YOUR WRITING — one-sentence hook. Suggested angle: ZoomInfo can't tell you HOW a company sells. This pipeline can.]**

**The result:** 25 noisy YC startups in → 20 verified SaaS → 7 product-led → 1 with a dedicated product hire — fully automated, 86 Clay credits, zero human research time.

---

## The Problem

**[YOUR WRITING — 2-3 sentences. Suggested points: searching "software" in a traditional database returns robotics, biotech and SaaS mixed together; no database has a "product-led growth" filter; SDRs burn hours qualifying accounts manually with 12 open tabs.]**

## The System

```
┌─────────────┐     ┌──────────────────────────────┐     ┌─────────────┐
│   PYTHON    │     │            CLAY               │     │   PYTHON    │
│  ingestion  │ ──▶ │       AI qualification        │ ──▶ │  activation │
│             │     │                               │     │             │
│ YC batch API│     │ 1. SaaS check (Claygent)      │     │ score ≥ 8   │
│ liveness    │     │ 2. PLG vs SLG (conditional)   │     │ → Slack     │
│ filter      │     │ 3. PM headcount (conditional) │     │   #sdr-alerts│
│ dedupe      │     │ 4. Lead score formula         │     │             │
└─────────────┘     └──────────────────────────────┘     └─────────────┘
```

### The enriched table

![Clay pipeline table](clay_pipeline_table.jpg)

### The output — a rep-ready Slack alert

![Slack alert](slack_alert.png)

## How It Works

### Phase 1 — Ingestion (`phase1.py`)
- Pulls a YC batch from the public JSON API — deliberately **noisy** input (SaaS, biotech, hardware, marketplaces mixed)
- Passes **only** company name + URL downstream. YC's own category tags are deliberately ignored — **[YOUR WRITING — why: proving the AI layer works on raw input]**
- Free filters before any paid step: `status: Active` + HTTP liveness check (never pay to analyze a dead website)
- Resilient delivery: exponential backoff (`tenacity`), structured logging, domain-level dedupe

### Phase 2 — AI Qualification (Clay + Claygent)
- **SaaS check:** Claygent visits each site → "SaaS" or best-guess label (GPT 5.4 Nano, 1 credit/row — cheap model for the easy binary call)
- **GTM motion:** classifies Product-led vs Sales-led from the site's CTAs, 80%-confidence rule (Argon, 3 credits/row — strong model for the nuanced call). **Runs only on rows verified as SaaS** — the conditional gate that keeps credits off biotech companies
- **PM headcount:** "Find Employee Headcount by Criteria" for product titles, also gated on SaaS

### Phase 3 — Score & Route
- Formula column: **+5** Product-led · **+3** SaaS · **+1 per PM** — zero credits
- `phase3_alert.py` posts accounts scoring ≥ 8 to Slack as a formatted SDR digest. Below threshold, no human ever sees it

## Pilot Results (YC Summer 2026 batch)

| Funnel stage | Count |
|---|---|
| Raw companies ingested | 25 |
| Verified SaaS (AI) | 20 |
| Product-led | 7 |
| Product-led + dedicated PM | 1 (Shepherd — top score 9/9) |
| **Total cost** | **86 Clay credits** |

**[YOUR WRITING — 1-2 sentences on what this means. Suggested: every robotics/biotech company was filtered before a single paid enrichment ran; the scoring separated a clear #1 account.]**

## Design Decisions

| Decision | Alternative rejected | Why |
|---|---|---|
| YC directory as source | G2 / Capterra | Pre-categorized sources make the AI layer redundant; G2 = Cloudflare + ToS issues |
| Public JSON API | Selenium + proxies | Found the underlying API — judgment over brute force |
| Ignore YC's industry tags | Filter on source metadata | **[YOUR WRITING]** |
| Liveness check in Python | Let Clay handle dead sites | Checks are free upstream, expensive downstream |
| Cheap model for SaaS check, strong model for GTM motion | One model for everything | Match model cost to task difficulty |
| Conditional runs on every enrichment | Enrich all rows | ~40% credit savings; cost discipline at every rung |
| Slack webhook from Python | Clay native Slack integration | Paywalled on free tier — same outcome at the code layer |

## Running It

```bash
pip install requests tenacity

# Phase 1: build the list (CSV path for Clay free tier; --webhook for paid)
python phase1.py --csv companies.csv --batch winter-2026

# → import CSV into Clay, run enrichments (prompts in /prompts.md)

# Phase 3: export scored table from Clay, alert Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
python phase3_alert.py --csv clay_export.csv --min-score 8
```

## What I'd Build Next

**[YOUR WRITING — suggested: hybrid GTM classification as a third bucket, contact-level enrichment on Tier 1 only, CRM sync, scheduled runs on new YC batch announcements, cost-per-qualified-account tracking.]**

---

*Built by Roy Manor — [YOUR LINKS]*
