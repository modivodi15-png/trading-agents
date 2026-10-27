# Improvement cycle log

One line per /scanner-improve run (newest first).

| date (IST) | scanner version | data through | failures logged | candidate | verdict | action | notes |
|---|---|---|---|---|---|---|---|
| 2026-10-27 19:10 | v18-unverified (no EWS tag on chart; v19 saved as script v31, not on chart yet) | none exported (bridge max 500 bars) | 0 | none | — | stopped at step 1 (step 9 safe stop) | Bridge `data_get_ohlcv` caps at 500 bars (BTC D: 2025-06-15→2026-10-26) and cannot write files; no laptop folder connected; cloud egress to public data blocked. 500 bars < warmup 200 + 9-month holdout + 20 signals/bucket, so no baseline or gate run. Live scripts and main unchanged; chart restored to OANDA:XAUUSD 240. See reports/eval/2026-10-27-cycle.md |
