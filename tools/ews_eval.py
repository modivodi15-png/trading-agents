#!/usr/bin/env python3
"""Replay the Elliott Wave Scanner's Python engine over history and score its scenarios.

No look-ahead: bars are fed one at a time, a reading uses only the bars fed so far, and a signal taken on
bar i is entered at bar i+1's open. A scenario "signal" is a new rank-k reading (new pattern, direction or
invalidation level) with a target zone and an invalidation level on the right sides of price. It is then
followed forward until the near target is hit (win), the invalidation is hit (loss; a bar that touches
both counts as a loss), or the horizon runs out (marked to market).

Follows the testing protocol in the scanner repo's docs/STRATEGY.md: costs, a random-direction baseline
(same entries, same target and stop distances, coin-flip direction), and the first vs second half of history.

Usage
  python ews_eval.py run  --repo ../elliott-wave-scanner --csv data/BTCUSD_D.csv --ticker BTCUSD --tf D \
                          --out reports/eval/base-BTC-D.json [--ranks 1] [--step 1] [--horizon 120] [--cost-pct 0.05]
  python ews_eval.py compare reports/eval/base-BTC-D.json reports/eval/cand-BTC-D.json
"""
import argparse
import json
import os
import random
import statistics
import sys
import time as _time
from collections import defaultdict


def load_engine(repo):
    py = os.path.join(os.path.abspath(repo), "python")
    if not os.path.isdir(os.path.join(py, "ewscan")):
        sys.exit(f"ewscan not found under {py}")
    sys.path.insert(0, py)
    from ewscan import Scanner, Settings  # noqa: E402
    from ewscan.io import load_csv  # noqa: E402
    return Scanner, Settings, load_csv


def pattern_of(sc):
    import re
    nm = (sc.name or sc.head or "?").split(" · ")[0]
    nm = re.sub(r"^#\d+\s*", "", nm)
    for cut in (" ⌛", " ⚠", "…", ","):
        nm = nm.split(cut)[0]
    return nm.strip()


def band(fit):
    return "≥80" if fit >= 80 else "70–79" if fit >= 70 else "60–69" if fit >= 60 else "<60"


def follow(bars, i0, direction, entry, target, stop, horizon, end=None):
    """-> (outcome, exit_price, bars_held) following bars from index i0 (the entry bar) up to index end"""
    last = min(len(bars) - 1 if end is None else end, i0 + horizon)
    for k in range(i0, last + 1):
        _, _, h, l, c = bars[k][:5]
        if direction > 0:
            hit_s, hit_t = l <= stop, h >= target
        else:
            hit_s, hit_t = h >= stop, l <= target
        if hit_s:
            return "loss", stop, k - i0 + 1
        if hit_t:
            return "win", target, k - i0 + 1
    return "expired", bars[last][4], last - i0 + 1


def r_of(direction, entry, exitp, stop, cost_pct):
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    gross = (exitp - entry) * direction / risk
    cost = 2 * cost_pct / 100 * entry / risk
    return gross - cost


def run(a):
    Scanner, Settings, load_csv = load_engine(a.repo)
    bars = load_csv(a.csv)
    sc = Scanner(Settings(), ticker=a.ticker, timeframe=a.tf)
    signals, last_key = [], {}
    t0 = _time.time()
    # holdout: the last N months are never used for tuning; in-sample signals stop being followed at its start
    cut_t = bars[-1][0] - a.holdout_months * 30.44 * 86400000 if a.holdout_months else None
    cut_i = next((k for k, x in enumerate(bars) if x[0] >= cut_t), len(bars)) if cut_t else len(bars)
    for i, b in enumerate(bars[:-1]):
        sc.feed(*b[:5])
        if i < a.warmup or i % a.step:
            continue
        res = sc.analyze()
        if not res:
            continue
        for s in res.scenarios:
            if s.rank > a.ranks or not s.direction or s.near is None or s.invalidation is None:
                continue
            key = (s.degree, pattern_of(s), s.direction, round(s.invalidation, 6))
            if last_key.get(s.rank) == key:
                continue
            last_key[s.rank] = key
            entry = bars[i + 1][1]
            d, tgt, stp = s.direction, s.near, s.invalidation
            if (tgt - entry) * d <= 0 or (entry - stp) * d <= 0:
                continue  # target already passed or stop on the wrong side at entry
            if abs(entry - stp) / entry * 100 < a.min_risk_pct:
                continue  # stop inside normal noise: R would be meaningless
            hold = i + 1 >= cut_i
            out, ex, held = follow(bars, i + 1, d, entry, tgt, stp, a.horizon, None if hold else cut_i - 1)
            r = r_of(d, entry, ex, stp, a.cost_pct)
            if r is None:
                continue
            signals.append(dict(bar=i, time=b[0], rank=s.rank, degree=s.degree, pattern=pattern_of(s),
                                fit=round(s.fit, 1), band=band(s.fit), dir=d, entry=entry, target=tgt,
                                stop=stp, outcome=out, r=round(r, 3), held=held, holdout=hold))
    meta = dict(repo=os.path.abspath(a.repo), commit=git_head(a.repo), csv=os.path.abspath(a.csv),
                ticker=a.ticker, tf=a.tf, bars=len(bars), first=bars[0][0], last=bars[-1][0],
                ranks=a.ranks, step=a.step, horizon=a.horizon, cost_pct=a.cost_pct, warmup=a.warmup,
                min_risk_pct=a.min_risk_pct, holdout_months=a.holdout_months,
                holdout_from=bars[cut_i][0] if cut_i < len(bars) else None,
                seconds=round(_time.time() - t0, 1))
    ins = [x for x in signals if not x["holdout"]]
    hos = [x for x in signals if x["holdout"]]
    out = dict(meta=meta, summary=summarize(ins, bars[:cut_i], a), holdout=holdout_summary(hos, bars, a),
               signals=signals)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print_summary(out)


def git_head(repo):
    try:
        import subprocess
        return subprocess.check_output(["git", "-C", repo, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "?"


def stats(sig):
    n = len(sig)
    if not n:
        return dict(n=0)
    closed = [s for s in sig if s["outcome"] != "expired"]
    wins = sum(s["outcome"] == "win" for s in sig)
    rs = [s["r"] for s in sig]
    gp = sum(r for r in rs if r > 0)
    gl = -sum(r for r in rs if r < 0)
    return dict(n=n, closed=len(closed), win_rate=round(wins / n, 3),
                hit_rate=round(wins / len(closed), 3) if closed else None,
                avg_r=round(statistics.mean(rs), 3), median_r=round(statistics.median(rs), 3),
                total_r=round(sum(rs), 2),
                pf=round(gp / gl, 2) if gl else None, low_sample=n < 10)


def baseline(sig, bars, a, seeds=200):
    """coin-flip direction, same entry and same target/stop distances"""
    wr, ar = [], []
    for seed in range(seeds):
        rnd = random.Random(seed)
        rs, wins = [], 0
        for s in sig:
            d = rnd.choice((1, -1))
            dt, ds = abs(s["target"] - s["entry"]), abs(s["entry"] - s["stop"])
            tgt, stp = s["entry"] + d * dt, s["entry"] - d * ds
            out, ex, _ = follow(bars, s["bar"] + 1, d, s["entry"], tgt, stp, a.horizon)
            rs.append(r_of(d, s["entry"], ex, stp, a.cost_pct))
            wins += out == "win"
        if rs:
            wr.append(wins / len(rs))
            ar.append(statistics.mean(rs))
    if not ar:
        return None
    ar.sort()
    wr.sort()
    lo, hi = int(0.025 * len(ar)), int(0.975 * len(ar)) - 1
    return dict(seeds=seeds, avg_r_mean=round(statistics.mean(ar), 3), avg_r_95=[round(ar[lo], 3), round(ar[hi], 3)],
                win_rate_mean=round(statistics.mean(wr), 3))


def summarize(sig, bars, a):
    groups = defaultdict(lambda: defaultdict(list))
    for s in sig:
        for g in ("pattern", "degree", "band", "rank", "dir"):
            groups[g][str(s[g])].append(s)
    mid = bars[len(bars) // 2][0]
    halves = dict(first=stats([s for s in sig if s["time"] < mid]), second=stats([s for s in sig if s["time"] >= mid]))
    base = baseline(sig, bars, a)
    o = stats(sig)
    edge = None
    if base and o.get("n"):
        edge = "beats random" if o["avg_r"] > base["avg_r_95"][1] else \
               "worse than random" if o["avg_r"] < base["avg_r_95"][0] else "not distinguishable from random"
    return dict(overall=o, halves=halves, baseline=base, edge=edge,
                by={g: {k: stats(v) for k, v in sorted(d.items())} for g, d in groups.items()})


def holdout_summary(sig, bars, a):
    o = stats(sig)
    base = baseline(sig, bars, a) if sig else None
    edge = None
    if base and o.get("n"):
        edge = "beats random" if o["avg_r"] > base["avg_r_95"][1] else \
               "worse than random" if o["avg_r"] < base["avg_r_95"][0] else "not distinguishable from random"
    return dict(overall=o, baseline=base, edge=edge)


def print_summary(out):
    m, s = out["meta"], out["summary"]
    print(f"{m['ticker']} {m['tf']} · {m['bars']} bars · commit {m['commit']} · {m['seconds']}s")
    print("overall", s["overall"])
    print("halves ", s["halves"])
    print("random ", s["baseline"], "→", s["edge"])
    if m.get("holdout_months"):
        print("HOLDOUT", out["holdout"]["overall"], "→", out["holdout"]["edge"])
    for g, d in s["by"].items():
        print(f"by {g}:")
        for k, v in d.items():
            print(f"  {k:28} {v}")


def compare(a):
    A, B = (json.load(open(p)) for p in (a.base, a.cand))
    for k in ("ticker", "tf", "csv", "ranks", "step", "horizon", "cost_pct", "min_risk_pct", "holdout_months"):
        if A["meta"][k] != B["meta"][k]:
            sys.exit(f"not comparable: {k} differs ({A['meta'][k]} vs {B['meta'][k]})")
    print(f"{A['meta']['ticker']} {A['meta']['tf']}: base {A['meta']['commit']} vs candidate {B['meta']['commit']}")

    def row(name, x, y):
        f = lambda v: "—" if v is None else v  # noqa: E731
        print(f"  {name:30} n {f(x.get('n'))}→{f(y.get('n'))}  win {f(x.get('win_rate'))}→{f(y.get('win_rate'))}"
              f"  hit {f(x.get('hit_rate'))}→{f(y.get('hit_rate'))}  avgR {f(x.get('avg_r'))}→{f(y.get('avg_r'))}"
              f"  medR {f(x.get('median_r'))}→{f(y.get('median_r'))}  PF {f(x.get('pf'))}→{f(y.get('pf'))}")
    row("overall", A["summary"]["overall"], B["summary"]["overall"])
    for h in ("first", "second"):
        row(f"{h} half", A["summary"]["halves"][h], B["summary"]["halves"][h])
    print(f"  edge vs random: {A['summary']['edge']} → {B['summary']['edge']}")
    if A["meta"].get("holdout_months"):
        row("HOLDOUT", A["holdout"]["overall"], B["holdout"]["overall"])
        print(f"  holdout edge vs random: {A['holdout']['edge']} → {B['holdout']['edge']}")
    for g in sorted(set(A["summary"]["by"]) | set(B["summary"]["by"])):
        ka, kb = A["summary"]["by"].get(g, {}), B["summary"]["by"].get(g, {})
        print(f" by {g}:")
        for k in sorted(set(ka) | set(kb)):
            row(k, ka.get(k, {}), kb.get(k, {}))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--repo", required=True, help="scanner repo (or a git worktree of a branch)")
    r.add_argument("--csv", required=True)
    r.add_argument("--ticker", required=True)
    r.add_argument("--tf", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--ranks", type=int, default=1, help="score scenarios ranked 1..N (default 1)")
    r.add_argument("--step", type=int, default=1, help="analyse every Nth bar (speed; 1 = every bar)")
    r.add_argument("--horizon", type=int, default=120, help="bars to follow a signal before marking to market")
    r.add_argument("--cost-pct", type=float, default=0.05, help="cost per side, %% of price")
    r.add_argument("--warmup", type=int, default=200, help="bars fed before the first reading")
    r.add_argument("--holdout-months", type=float, default=0,
                   help="keep the last N months out of the main results (reported separately as HOLDOUT)")
    r.add_argument("--min-risk-pct", type=float, default=0.5, help="skip signals whose stop is closer than this %% of price")
    c = sp.add_parser("compare")
    c.add_argument("base")
    c.add_argument("cand")
    a = p.parse_args()
    run(a) if a.cmd == "run" else compare(a)


if __name__ == "__main__":
    main()
