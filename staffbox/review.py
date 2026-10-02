"""The monthly review: compare this run with the last one, gate go-live per task type, and turn corrections into tests.

  staffbox review NEW.jsonl [--prev OLD.jsonl] [--mode brain+quote] [--bar quote=85,lookup=90,triage=90,unknown=100]
  staffbox addtest TESTS.jsonl --id ID --type quote --prompt "..." --expect 123.45   (a correction becomes a test)
"""
import json, pathlib

DEFAULT_BAR = {"quote": 85, "lookup": 90, "triage": 90, "unknown": 100}


def load(path, mode=None):
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if mode:
        rows = [r for r in rows if r["mode"] == mode]
    return {r["id"]: r for r in rows}


def review(new, prev=None, bar=None):
    """Return (markdown, gate) where gate maps task type -> True when it may be live."""
    bar = dict(DEFAULT_BAR, **(bar or {}))
    types = sorted({r["type"] for r in new.values()})
    lines, gate = ["# Review", "", "| Task type | Right | Bar | Go-live |", "|---|---|---|---|"], {}
    for t in types:
        rs = [r for r in new.values() if r["type"] == t]
        pct = 100 * sum(r["ok"] for r in rs) // len(rs)
        gate[t] = pct >= bar.get(t, 90)
        lines.append(f"| {t} | {sum(r['ok'] for r in rs)}/{len(rs)} ({pct}%) | {bar.get(t, 90)}% | {'LIVE' if gate[t] else 'not live'} |")
    if prev:
        fixed = sorted(i for i, r in new.items() if r["ok"] and i in prev and not prev[i]["ok"])
        broke = sorted(i for i, r in new.items() if not r["ok"] and i in prev and prev[i]["ok"])
        added = sorted(i for i in new if i not in prev)
        lines += ["", f"Since last run: {len(fixed)} fixed · **{len(broke)} regressed** · {len(added)} new tests", ""]
        for label, ids in (("Regressed (was right, now wrong)", broke), ("Fixed", fixed), ("New tests", added)):
            if ids:
                lines += [f"**{label}:** " + ", ".join(ids)]
    misses = [r for r in new.values() if not r["ok"]]
    lines += ["", "## Misses to fix (brain → tool → model, then re-run)", "", "| Test | Expected | Got |", "|---|---|---|"]
    lines += [f"| {r['id']} | {r['expect']} | {str(r['answer'])[:90].replace('|', '/')} |" for r in misses]
    return "\n".join(lines) + "\n", gate


def add_test(tests_path, id, type, prompt, expect):
    p = pathlib.Path(tests_path)
    ids = {json.loads(l)["id"] for l in p.read_text().splitlines() if l.strip()} if p.exists() else set()
    if id in ids:
        raise ValueError(f"test id {id} already exists; tests are never edited, add a new id")
    if type == "quote":
        expect = float(str(expect).replace("$", "").replace(",", ""))
    elif type == "lookup":
        expect = [x.strip() for x in str(expect).split("|")]
    with open(p, "a") as fh:
        fh.write(json.dumps(dict(id=id, type=type, prompt=prompt, expect=expect, source="correction")) + "\n")
