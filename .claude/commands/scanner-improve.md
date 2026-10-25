---
description: Automatic scanner improvement cycle (scheduled every 48 hours). Refreshes data, scores recent readings, tests at most one change against strict gates, and when a change has passed twice applies it everywhere — scanner repo, Python engine, TradingView scanner and EW Rider, agent config — with automatic rollback.
---

Run one improvement cycle. The user has authorised this cycle to change and save the scanner without asking,
**only** through the gates below. If any step is unclear or fails, stop safely (step 9) rather than guess.

If the subagents in `.claude/agents/` aren't available (e.g. a scheduled cloud session), do each step yourself,
following that agent's file. TradingView tools may be named `mcp__tradingview__*` (local) or
`mcp__remote-devices__tradingview__*` (scheduled session linked to the laptop); they're the same tools.

## 0. Setup
- Both repos up to date: this pack and the scanner repo (`config/scanner.yaml` → `repo_path`, `repo_url`).
  `git pull` each; clone if missing.
- Read `config/scanner.yaml`, `config/eval-set.yaml`, `feedback/log.md`, `feedback/ledger.md`, `feedback/cycles.md`.
- **tv-operator**: `tv_health_check`. If TradingView or the laptop can't be reached, log
  "skipped: TradingView unreachable" in `feedback/cycles.md`, commit, push, notify, stop.
- **tv-operator**: version check (tag vs `expected_version`). On a mismatch, stop and notify. If
  `tradingview_username` is empty, open `tradingview_script` in the Pine editor, read the username from its
  import lines, save it to `config/scanner.yaml`, and restore the editor.

## 1. Fresh data
**tv-operator**: export every market in `markets` and `holdout_markets` (max bars) to `data/`. Restore the chart.

## 2. Rollback watch (before anything new)
For each ledger entry with status `live` whose go-live date is within `auto.rollback.watch_cycles` cycles:
**scanner-evaluator** replays the live version and the version before it (git worktree at the previous tag),
counting only signals after the go-live date, across all markets. If live is worse by
`auto.rollback.worse_by_r` avg R or more and both have ≥ `min_signals_per_bucket` such signals → **roll back
everywhere** (step 7 in reverse: revert the commit in the scanner repo, restore and save the previous source in
TradingView for the scanner and Rider, set `expected_version` back, ledger status `rolled back`). Then go to step 8.

## 3. Baseline and failures
- **scanner-evaluator**: baseline on the current version, `--holdout-months` from the config, `step_quick`.
- **trade-journal**: update outcomes of open journal ideas.
- **scanner-evaluator**: log failures in `feedback/log.md`: any pattern/degree/score-band bucket with negative
  avg R in 3+ tuning markets (n ≥ `min_signals_per_bucket` each), plus open user feedback, plus wave-counter
  parity reports. Use **tuning-set, in-sample results only** for this — never the holdout.

## 4. Pick one candidate (`max_candidates_per_cycle: 1`)
Priority: (a) a ledger entry at `passed 1/2` → re-test it on today's data (step 5), no new candidate;
(b) otherwise the open failure with the most evidence. Skip if `max_live_changes_per_30_days` is reached.
**technical-lead** turns it into one change: a score, weight, threshold or guideline (never a hard rule —
`hard_rules_locked`), mapped to its RULEBOOK.md section. Skip ideas the ledger shows rejected twice.
**pine-dev**: implement it in the **Python port only**, on branch `auto/<FB id>`; `pytest` must pass.
Add it to `feedback/ledger.md`.

## 5. Gates (all must pass) — scanner-evaluator, `step_final`
1. Tuning set: the `acceptance` rules (markets improved, none clearly worse, second half improves, beats random).
2. Holdout period (last `holdout_months`) of every market: avg R and median R not lower than base.
3. Holdout markets: avg R and median R not lower than base.
Record the result in the ledger. First pass → status `passed 1/2`, stop here this cycle (step 8). A pass on a
later cycle with fresh data → `passed 2/2` → step 6. Any fail → `rejected` (note which gate), delete nothing.

## 6. Port to Pine — pine-dev
On the same branch: port the change to the Pine library or indicator that holds that logic; if EWRules
changed, also the EW Rider import. Bump `EWS_VER`, write the CHANGELOG entry ("automatic, FB id, gates
passed, ledger link"), update RULEBOOK.md where it states the changed value. Run the parity tests that apply.
**tv-operator**: `pine_check` every changed script (bridge) with the username in the imports. Compile errors → fix
(up to 3 tries) or mark the ledger `port failed` and stop.

## 7. Go live everywhere
- **Library changed (EWBase/EWRules/EWProject):** TradingView requires a person to click Publish for a library.
  tv-operator saves the library source in the editor; status `awaiting library publish`; notify the user with
  the exact steps (open the library → Publish script → Update existing script). Stop. The next cycle sees the
  new library version, updates the import numbers, and continues from here.
- **tv-operator**: put the change into `tradingview_script` through Claude in Chrome, sending only the changed
  lines ("Code into the editor"), and save; then the Rider if it changed. If Claude in Chrome isn't available in
  this session, stop here: status `awaiting go-live`, notify the user, and the next cycle (or the user running
  `/pine-change`) finishes it. Then refresh the chart instance (fresh copy, user's inputs kept, old one removed). Read the
  Elliott table on BINANCE:BTCUSDT.P, OANDA:XAUUSD and one Nifty stock: the new `EWS` tag must show and the
  tables must parse. If not → restore and save the previous source, ledger `go-live failed`, stop.
- **pine-dev**: merge the branch into `main`, tag it, push; CHANGELOG notes the TradingView script version.
- Set `expected_version` in `config/scanner.yaml`, ledger `live` with today's date.
- Restore the chart.

## 8. Report and save state
- Add one line to `feedback/cycles.md`. Commit and push this pack (`feedback/`, `config/scanner.yaml`).
- Write `reports/eval/<date>-cycle.md` and send the user a short notification: what failed, what was tested,
  gate results, and anything that went live or was rolled back.

## 9. Stopping safely
On any unexpected error: restore the chart and the Pine editor, leave `main` and the live TradingView scripts
as they were, log the error in `feedback/cycles.md`, push, notify.
