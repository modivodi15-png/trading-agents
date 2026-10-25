---
description: Daily pre-open scan — Nifty 50 + indices, BTC, gold, silver on the daily chart, filtered, checked and red-teamed into a brief.
argument-hint: "[universe: nifty50|crypto|metals|all] (default all)"
---

Run the morning scan for universe: $ARGUMENTS (default: all of nifty50, indices, crypto, metals).

1. **tv-operator** — batch-read every symbol in the universe on the `D` timeframe (see
   `config/universes.yaml`). Save raw JSONL. Restore the chart at the end.
2. **screener** — classify with `config/signal-rules.md`, build the shortlist (max 8 per side).
3. **tv-operator** — for each shortlisted symbol only, pull OHLCV for W, D and 240 (300 bars each)
   and the Elliott labels. Sequential, then restore the chart.
4. **wave-counter** — independent count for each shortlisted symbol (you may run several
   wave-counter calls in parallel; they don't touch the chart).
5. In parallel: **macro-researcher** (overnight macro, India pre-open: GIFT Nifty, FII/DII,
   crude, USDINR, US yields, DXY) and **crypto-derivs** (if BTC is shortlisted).
6. **technical-lead** → **macro-lead** → **position-sizer** → **risk-lead**.
7. **contrarian** on every approved idea.
8. **trade-journal** — log every shortlisted idea (approved, vetoed or watch).
9. **brief-writer** — daily brief to `reports/YYYY-MM-DD-brief.md`.

Finish by showing the user the top-ideas table and the path to the brief. Keep the chat summary
under 15 lines.
