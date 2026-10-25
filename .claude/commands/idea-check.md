---
description: Deep check of one symbol and (optionally) the user's thesis — multi-timeframe count, positioning, fundamentals, sizing and the opposing case. Add "quick" for a cheaper technical-only check.
argument-hint: "<symbol> [quick] [thesis, e.g. 'wave 3 up from 1152, target 1350']"
---

Check this idea: $ARGUMENTS

If the arguments include the word **quick**, run quick mode; otherwise run full mode.

## Full mode
1. **tv-operator** — for the symbol, read the Elliott table and labels and pull OHLCV on
   W, D, 240 and 60. Add `news_get_ticker`. Restore the chart.
2. In parallel:
   - **wave-counter** — independent count; if the user gave a thesis, test it rule by rule.
   - **equity-analyst** (NSE stocks) or **crypto-derivs** (BTC) — skip for metals.
   - **macro-researcher** — only drivers specific to this market.
3. **technical-lead** → **macro-lead** → **position-sizer** → **risk-lead**.
4. **contrarian**.
5. **trade-journal** — log with `user_decision: pending`.
6. **brief-writer** — idea write-up to `reports/YYYY-MM-DD-idea-<symbol>.md`.

## Quick mode (technical only)
1. **tv-operator** — Elliott table and labels, OHLCV on D and 240 only. No news. Restore the chart.
2. **wave-counter** — independent count; test the thesis if one was given.
3. **technical-lead** — verdict and levels.
4. **position-sizer** — R multiples (and size, if limits are configured).
5. **trade-journal** — log with `user_decision: pending`.

Skip macro-lead, risk-lead, contrarian and brief-writer; say in the reply that quick mode
skipped them and that a full `/idea-check` will run them.

Reply with: verdict, levels table (scanner and wave-counter shown separately), sizing, contrarian
verdict (full mode only), and the decision the user needs to make.
