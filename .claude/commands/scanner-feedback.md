---
description: Log feedback on the Elliott Wave Scanner, or test whether a proposed change improves it. Use "baseline" to measure the current version, "test <branch|FB id>" to evaluate a change, or plain text to log feedback.
argument-hint: "<feedback text> | baseline | test <branch or FB id> | status"
---

Scanner feedback request: $ARGUMENTS

- **Plain feedback** (e.g. "RELIANCE D 14 Oct: called a zigzag, it was an expanded flat"):
  **scanner-evaluator** logs it in `feedback/log.md`. If the same issue now has 3+ reports, or the user asks,
  **technical-lead** turns it into one concrete proposed change, mapped to a RULEBOOK.md section, and asks the
  user whether to have pine-dev build it.
- **baseline**: **scanner-evaluator** checks the data in `config/eval-set.yaml` (tv-operator exports any missing
  CSV, sequentially, restoring the chart), then replays every market on the current version and reports.
- **test <branch or FB id>**: if no branch exists yet, **pine-dev** implements the change on a new branch in the
  scanner repo — Python port first, so it can be tested — with no TradingView changes. Then
  **scanner-evaluator** compares it with the baseline and gives its verdict. If it says adopt, ask the user
  whether to run `/pine-change` to port, compile and save it.
- **status**: **scanner-evaluator** lists open feedback, items under test and recent verdicts.

Nothing in this workflow edits the live indicator or saves to TradingView.
