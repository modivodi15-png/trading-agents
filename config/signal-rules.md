# Signal rules for the Elliott Wave Scanner

These rules turn the scanner's ranked counts into Buy / Sell / Mixed. They are the
user's rules, not the scanner's; change them here and every agent follows.

## Reading the scanner table
`data_get_pine_tables(study_filter="Elliott")` returns up to four rows plus an optional confluence row:

```
<rank> [H|L] <pattern> | <▲|▼><target low>–<target high> ✕<invalidation> | <score> [⏳<time left> | drop <n>d] [⌛] [⚠]
◆ <▲|▼> <price or range>  <H+M+L degrees in confluence>
```

- `H` / `L` prefix = higher / lower degree than the main count. No prefix = main degree.
- `▲` bullish projection, `▼` bearish. `▲met` / `▼met` = target already reached.
- `✕` = invalidation price for that count.
- `⏳` = estimated time window left; `drop Nd` / `⌛` = the time window has expired (count is stale).
- `⚠` = scanner warning on proportions.
- `◆` row = price level where targets from several degrees cluster.

## Classification
1. Score each row: `+score` if ▲, `−score` if ▼.
2. Halve the weight of rows that are stale (`drop` or `⌛`) or flagged `⚠`.
3. Ignore rows whose target is already `met` (they describe a finished move).
4. Net = sum of weighted scores.
5. **Buy** if the rank-1 row is ▲ and Net ≥ +30.
   **Sell** if the rank-1 row is ▼ and Net ≤ −30.
   Otherwise **Mixed**; label it "leaning bullish/bearish" by the sign of Net.
6. Flag a **caution** when the ◆ confluence direction disagrees with the classification,
   or when the rank-1 invalidation sits on the wrong side of price or target.

## Quality filters for the shortlist
- Rank-1 score ≥ 70
- Distance from last price to rank-1 invalidation ≤ 8% (daily) — tight, defined risk
- Reward to first target ≥ 1.5× distance to invalidation
