---
description: Weekly review — update outcomes for every journaled idea, compute hit rates by pattern/score/market, and propose rule or scanner changes.
---

Run the weekly review.

1. **trade-journal** — list ideas with status `open` and their symbols/timeframes.
2. **tv-operator** — pull OHLCV from each idea's date to now for those symbols. Restore the chart.
3. **trade-journal** — update outcomes (target / invalidated / expired) for taken and skipped ideas;
   compute the review statistics.
4. **risk-lead** — interpret the stats; propose changes only for buckets with ≥10 closed ideas.
5. **technical-lead** — if the stats point to a scanner weakness (e.g. one pattern type keeps
   failing), describe the rule change for pine-dev. Do not start the change.
6. **brief-writer** — weekly review to `reports/YYYY-MM-DD-weekly.md`.

Reply with the 3 clearest findings and any proposed changes awaiting the user's decision.
