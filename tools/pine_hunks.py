#!/usr/bin/env python3
"""Turn a Pine change into the smallest set of find-and-replace edits, for sending to the Pine Editor in Chrome.

Only the changed lines (plus enough surrounding text to be unique) leave this machine; the full script never
goes through the tool call. The browser applies the edits to the editor's own text and checks fingerprints
before and after, so a wrong base or a bad edit is caught before anything is saved.

  python pine_hunks.py <old.pine> <new.pine> [--username NAME] > edit.js

Writes a self-contained JavaScript snippet for Claude in Chrome's javascript_tool on in.tradingview.com/pine/
(with the right script open). It: finds Monaco, checks the editor text (CRLF normalised) has the old SHA-256,
applies each edit (each must match exactly once), checks the result has the new SHA-256, puts it in the
editor as one undoable edit, and returns a short status. It never saves; save from the script menu after.
"""
import argparse
import difflib
import hashlib
import json
import sys


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def hunks(old, new):
    a, b = old.splitlines(keepends=True), new.splitlines(keepends=True)
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        # grow context (whole lines) until the old text is unique in the old file
        for ctx in range(1, 40):
            s1, s2 = max(0, i1 - ctx), min(len(a), i2 + ctx)
            o = "".join(a[s1:s2])
            if old.count(o) == 1:
                n = "".join(a[s1:i1]) + "".join(b[j1:j2]) + "".join(a[i2:s2])
                out.append([o, n])
                break
        else:
            sys.exit(f"could not make edit at old lines {i1}-{i2} unique")
    # check: applying in order reproduces new
    t = old
    for o, n in out:
        assert t.count(o) == 1
        t = t.replace(o, n, 1)
    if t != new:
        sys.exit("edits don't reproduce the new file (overlapping hunks); widen context")
    return out


JS = r"""
(async () => {
  const EDITS = __EDITS__, OLD = "__OLD__", NEW = "__NEW__";
  const H = async s => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s)))).map(b => b.toString(16).padStart(2, '0')).join('');
  let m = window.monaco || window.__mon;
  if (!m) for (const k of Object.keys(window).filter(k => k.startsWith('webpackChunk'))) {
    try { window[k].push([['__x' + Date.now()], {}, req => { for (const id of Object.keys(req.m)) { try { const x = req(id); if (x && x.editor && typeof x.editor.getEditors === 'function') { window.__mon = x; break; } } catch (e) {} } }]); } catch (e) {}
  }
  m = window.monaco || window.__mon;
  if (!m) return 'abort: Monaco not found';
  const ed = m.editor.getEditors()[0], model = ed.getModel();
  let s = model.getValue().replace(/\r\n/g, '\n');
  if (await H(s) !== OLD) return 'abort: editor text is not the expected base version (sha ' + (await H(s)).slice(0, 12) + ')';
  const counts = EDITS.map(([o]) => s.split(o).length - 1);
  if (counts.some(c => c !== 1)) return 'abort: edit match counts ' + JSON.stringify(counts);
  for (const [o, n] of EDITS) s = s.replace(o, () => n);
  if (await H(s) !== NEW) return 'abort: result fingerprint mismatch';
  ed.pushUndoStop();
  ed.executeEdits('pine_hunks', [{ range: model.getFullModelRange(), text: s, forceMoveMarkers: true }]);
  ed.pushUndoStop();
  const done = await H(model.getValue().replace(/\r\n/g, '\n'));
  return done === NEW ? 'ok: ' + EDITS.length + ' edits applied, editor matches target ' + NEW.slice(0, 12) + ' (not saved yet)' : 'abort: editor text after edit does not match';
})()
"""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("old")
    p.add_argument("new")
    p.add_argument("--username", help="replace YOUR_TV_USERNAME/ in both files with this username")
    a = p.parse_args()
    old, new = (open(f, encoding="utf-8").read() for f in (a.old, a.new))
    if a.username:
        old, new = (x.replace("YOUR_TV_USERNAME/", a.username + "/") for x in (old, new))
    ed = hunks(old, new)
    js = JS.replace("__EDITS__", json.dumps(ed, ensure_ascii=False)).replace("__OLD__", sha(old)).replace("__NEW__", sha(new))
    sys.stdout.write(js.strip() + "\n")
    sys.stderr.write(f"{len(ed)} edits, {sum(len(n) for _, n in ed)} chars sent (full script {len(new)} chars)\n")


if __name__ == "__main__":
    main()
