# trading-agents

A Claude Code multi-agent system for Elliott Wave–led trading research across Nifty 50, BTC,
gold and silver, reading your TradingView Desktop chart through the TradingView MCP server.

Analysis only — it never places orders.

## Team

```
trading-master (main session, rules in CLAUDE.md)
├── technical-lead ── tv-operator · wave-counter · screener · pine-dev · crypto-derivs
├── macro-lead ────── macro-researcher · equity-analyst
├── risk-lead ─────── position-sizer · trade-journal
└── shared ────────── contrarian · brief-writer
```

Claude Code subagents can't call other subagents, so the main session (trading-master) calls the
specialists, hands their outputs to the right lead, then to contrarian and brief-writer.
Only **tv-operator** touches TradingView, so agents never fight over your one chart.

| Agent | Role |
|---|---|
| technical-lead | Weighs scanner vs own count, timeframe alignment, grades setups |
| macro-lead | Regime call, per-market tilt, event risk vs setups |
| risk-lead | Final gate: R:R, portfolio limits, veto; weekly stats review |
| tv-operator | All TradingView reads; restores your chart afterwards |
| wave-counter | Independent multi-degree count from your rulebook; checks each scanner count |
| screener | Universe scan → Buy / Sell / Mixed via `config/signal-rules.md` |
| pine-dev | Maintains the Elliott Wave Scanner (Pine v6), tests changes |
| macro-researcher | Rates, carry, yen, metals, flows, India macro — sourced |
| equity-analyst | Results, valuation, event calendar for stocks |
| crypto-derivs | BTC funding, basis, OI, liquidations, options, ETF flows |
| position-sizer | Size from invalidation and your limits |
| trade-journal | Logs every idea and outcome; hit rates by pattern and score |
| contrarian | Opposing case for every idea |
| brief-writer | Daily brief, idea write-ups, weekly review |

## Scanner version and repo

The agents use your `elliott-wave-scanner` repo, set in `config/scanner.yaml`:
- **wave-counter** reads `docs/RULEBOOK.md` and runs the Python engine `ewscan` on the same bars as a
  repeatable check (all three degrees match the chart since v18.1).
- **pine-dev** edits the real Pine source and CHANGELOG on a branch.
- **tv-operator** checks the `EWS vNN` tag in the scanner table against `expected_version` and stops on a
  mismatch. Every journaled idea records the version. Since several saved TradingView scripts share the
  title "Elliott Wave Scanner", keep only one on the chart.

Clone the scanner repo next to this folder (`Downloads\elliott-wave-scanner`), or change `repo_path`.
v18 (saved as script version 30) has no tag; with `expected_version: v18` readings are marked unverified.
Once v19 (branch `ews-version-tag`) is saved, set `expected_version: v19`.

## Models

Each agent's model is set in its frontmatter to match how much judgment the job needs:

| Model | Agents |
|---|---|
| haiku | tv-operator, screener, position-sizer, trade-journal, brief-writer |
| sonnet | macro-researcher, equity-analyst, crypto-derivs, technical-lead, macro-lead, risk-lead, contrarian, pine-dev |
| opus | wave-counter |

The main session (trading-master) uses whatever model you pick in Claude Code. Sonnet is
enough for routine runs like `/morning-scan`; switch to Opus for hard discussions.
To change an agent, edit the `model:` line in `.claude/agents/<name>.md`.

## Workflows

| Command | What it does |
|---|---|
| `/morning-scan [universe]` | Daily scan → shortlist → checks → brief |
| `/idea-check <symbol> [thesis]` | Full workup of one idea |
| `/weekly-review` | Score past ideas, find what works, propose changes |
| `/pine-change <rule change>` | Change the scanner, test, save on approval |

Or just ask in plain language — trading-master routes it.

## Setup (on your laptop)

1. Unzip to a folder, e.g. `C:\Users\ankur\Downloads\trading-agents`.
2. Open that folder in the **Code** tab of the Claude desktop app (or run `claude` in it).
3. Make sure Claude Code can see the TradingView MCP server. If it is only configured for the
   desktop chat app, add it to Claude Code as well under the name `tradingview` — the tool
   permissions in `.claude/settings.json` assume `mcp__tradingview__*`. Run `/mcp` to check.
4. Have TradingView Desktop open with the **Elliott Wave Scanner** on the chart.
5. Fill in `config/risk-limits.yaml` and set `configured: true`. Sizing is disabled until then.
6. Drop your EW rulebook and ABC reference docs into `rulebook/`.
7. Try `/idea-check NSE:JSWSTEEL` first — one symbol, quick to sanity-check the setup.

## Safety built in
- `.claude/settings.json` makes Claude ask before any alert create/delete, Pine save/delete,
  clearing drawings or removing watchlist items, and blocks replay trading.
- Every idea must carry an invalidation level and timestamp, and is journaled.
- Scanner counts and wave-counter counts are always reported separately.

## Scheduling the morning scan
A scheduled task can run `/morning-scan` on weekdays before the NSE open, but only while your
laptop is on and TradingView Desktop is running.
