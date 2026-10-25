# Rulebook overrides

The main rulebook is `docs/RULEBOOK.md` in your scanner repo (`elliott-wave-scanner`, path set in
`config/scanner.yaml`). wave-counter reads it first, and pine-dev keeps it in step with the scanner.

Use this folder only for personal rules that sit on top of it and aren't in the scanner, e.g.
- "ignore counts with score < 60"
- "no wave-5 longs on the weekly"
- your ABC correction reference notes, if you want them considered alongside RULEBOOK.md

Where a file here conflicts with RULEBOOK.md, this folder wins.
