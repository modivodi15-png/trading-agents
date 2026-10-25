---
description: Change the Elliott Wave Scanner indicator — implement, compile, test on saved charts, and save only after approval.
argument-hint: "<rule change, e.g. 'flag expanded flats where C < 100% of A'>"
---

Indicator change requested: $ARGUMENTS

1. If `pine/elliott-wave-scanner.pine` is missing: **tv-operator** opens the scanner with
   `pine_open`/`pine_get_source` and saves the source there. Restore the chart.
2. **pine-dev** — implement the change locally, update `pine/CHANGELOG.md`, write test cases in
   `pine/tests.md` (at least: one Nifty stock, BTCUSDT.P, XAUUSD), and give tv-operator the steps.
3. **tv-operator** — `pine_set_source` → `pine_smart_compile` → `pine_get_errors`. If it compiles,
   read the Elliott table on each test chart. Restore the chart. **Do not save.**
4. **pine-dev** — fix and repeat steps 2–3 until it compiles cleanly and tests are evaluated.
5. **technical-lead** — review the test results against the rulebook.
6. Show the user the diff, test pass/fail table and technical-lead's review, then **ask** whether
   to save. Only on an explicit yes does tv-operator run `pine_save`.

If the user says no, have tv-operator restore the previous source with `pine_set_source` from
the saved local copy so the chart is left as it was.
