---
description: Change the Elliott Wave Scanner — implement in the scanner repo on a branch, compile, test on charts, and save to TradingView only after approval.
argument-hint: "<change, e.g. 'flag expanded flats where C < 100% of A'>"
---

Scanner change requested: $ARGUMENTS

If the change touches scores, weights, thresholds or guidelines (anything that changes which counts rank
where), first check `feedback/log.md` / `reports/eval/` for an *adopt* verdict from scanner-evaluator. If
there is none, stop and suggest `/scanner-feedback test` first. Display-only changes (tables, labels,
colours, the version tag) and the user's explicit hard-rule decisions don't need one.

1. **pine-dev** — read `config/scanner.yaml`; clone the scanner repo to `repo_path` if missing and create a
   branch. Implement the change, bump `EWS_VER`, update `CHANGELOG.md` (and `docs/RULEBOOK.md` if a rule
   changed), update and test the Python port if the logic changed, write chart test cases, and give
   tv-operator the steps.
2. **tv-operator** — put the user's TradingView username in the import lines, compile (`pine_check` first;
   if the chart test needs it, `pine_set_source` → `pine_smart_compile` → `pine_get_errors`), then read the
   Elliott table on each test chart and confirm the new `EWS` tag shows. Restore the chart. **Do not save.**
3. **pine-dev** — fix and repeat steps 1–2 until it compiles cleanly and the tests are evaluated.
4. **technical-lead** — review the test results against the rulebook.
5. Show the user the diff, Python test result, chart test pass/fail table and technical-lead's review, then
   **ask** whether to save. If a library changed, list which library must be published first and the new
   import version.
6. Only on an explicit yes: tv-operator runs `pine_save` on the script named in `tradingview_script`.
   pine-dev then sets `expected_version` in `config/scanner.yaml`, records the TradingView script version in
   CHANGELOG, commits and merges the branch.

If the user says no, tv-operator restores the editor to the previous source so the chart is left as it was,
and the branch stays unmerged.
