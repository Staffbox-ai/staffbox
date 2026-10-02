"""staffbox: check the brain, ask it, log to it, and score the worker.

  staffbox check   VAULT                       lint frontmatter, links, dates; log.md append-only
  staffbox context VAULT "question"            print the notes the worker would read
  staffbox ask     VAULT "question" [--model]  answer from the brain with a local model
  staffbox quote   VAULT "request" [--sku --qty --opt k=v]  price one line from the vault's pricing notes (no model)
  staffbox log     VAULT "asked" "did" [--could-not ...]   append one line to log.md
  staffbox eval    VAULT TESTS.jsonl [--model --host --modes --out]   run the scorecard
  staffbox review  NEW.jsonl [--prev OLD.jsonl --mode M --bar quote=85]  monthly review: diff, go-live gate, misses
  staffbox addtest TESTS.jsonl --id ID --type T --prompt P --expect E   a correction becomes a test (never edits)
  staffbox inbox   VAULT --in DIR --drafts DIR [--model]   draft replies to requests in a folder; never sends
"""
import argparse, datetime, json, os, pathlib, platform, sys
from . import actions, brain, evals, inbox, review

HOST = os.environ.get("OLLAMA_HOST_URL", "http://localhost:11434")


def company_name(vault):
    notes, _ = brain.load(vault)
    c = notes.get("company")
    if c:
        for line in c.body.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return "the company"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="staffbox", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check"); s.add_argument("vault")
    s = sub.add_parser("context"); s.add_argument("vault"); s.add_argument("question")
    s = sub.add_parser("ask"); s.add_argument("vault"); s.add_argument("question")
    s.add_argument("--model", default="qwen3:8b"); s.add_argument("--host", default=HOST); s.add_argument("--mode", default="brain+quote")
    s = sub.add_parser("quote"); s.add_argument("vault"); s.add_argument("request")
    s.add_argument("--sku", default=""); s.add_argument("--qty", type=int, default=0); s.add_argument("--opt", action="append", default=[])
    s = sub.add_parser("log"); s.add_argument("vault"); s.add_argument("asked"); s.add_argument("did"); s.add_argument("--could-not", default="nothing")
    s = sub.add_parser("eval"); s.add_argument("vault"); s.add_argument("tests")
    s.add_argument("--model", default="qwen3:8b"); s.add_argument("--host", default=HOST)
    s.add_argument("--modes", default="none,brain,brain+calc"); s.add_argument("--machine", default=platform.node())
    s.add_argument("--workers", type=int, default=1); s.add_argument("--num-ctx", type=int); s.add_argument("--limit", type=int)
    s.add_argument("--out", default="scorecard")
    s = sub.add_parser("review"); s.add_argument("new"); s.add_argument("--prev"); s.add_argument("--mode")
    s.add_argument("--bar", default=""); s.add_argument("--out")
    s = sub.add_parser("addtest"); s.add_argument("tests"); s.add_argument("--id", required=True); s.add_argument("--type", required=True)
    s.add_argument("--prompt", required=True); s.add_argument("--expect", required=True)
    s = sub.add_parser("inbox"); s.add_argument("vault"); s.add_argument("--in", dest="inbox", required=True); s.add_argument("--drafts", required=True)
    s.add_argument("--model", default="qwen3:8b"); s.add_argument("--host", default=HOST); s.add_argument("--num-ctx", type=int)
    a = ap.parse_args(argv)

    if a.cmd == "review":
        bar = {k: int(v) for k, v in (x.split("=") for x in a.bar.split(",") if "=" in x)}
        text, gate = review.review(review.load(a.new, a.mode), review.load(a.prev, a.mode) if a.prev else None, bar)
        if a.out:
            pathlib.Path(a.out).write_text(text)
        print(text)
        sys.exit(0 if all(gate.values()) else 3)
    if a.cmd == "addtest":
        review.add_test(a.tests, a.id, a.type, a.prompt, a.expect); print(f"added {a.id} to {a.tests}")
    if a.cmd == "inbox":
        for p in inbox.run(a.vault, a.inbox, a.drafts, a.host, a.model, company_name(a.vault), num_ctx=a.num_ctx):
            print("draft:", p)

    if a.cmd == "check":
        problems = brain.check(a.vault)
        notes, _ = brain.load(a.vault)
        for p in problems:
            print("✗", p)
        print(f"{'✓ healthy' if not problems else f'{len(problems)} problem(s)'}: {len(notes)} notes in {a.vault}")
        sys.exit(1 if problems else 0)
    if a.cmd == "context":
        text, picked = brain.context(a.vault, a.question)
        print(text); print("# notes:", ", ".join(picked), file=sys.stderr)
    if a.cmd == "ask":
        out, notes, _, calls = evals.ask(a.host, a.model, a.vault, a.question, a.mode, company_name(a.vault))
        print(out); print(f"\n[notes read: {', '.join(notes)}; calculator calls: {calls}]", file=sys.stderr)
    if a.cmd == "quote":
        pricing = actions.load_pricing(a.vault)
        opts = dict(o.split("=", 1) for o in a.opt if "=" in o)
        sku, qty, opts = actions.resolve(pricing, a.request, a.sku.upper(), a.qty, opts)
        total, work = actions.quote(pricing, sku, qty, opts)
        print(work if total is None else f"{work}\nANSWER: ${total:,.2f}")
        sys.exit(0 if total is not None else 2)
    if a.cmd == "log":
        print(brain.append_log(a.vault, a.asked, a.did, a.could_not), end="")
    if a.cmd == "eval":
        tests = [json.loads(l) for l in open(a.tests) if l.strip()][: a.limit]
        rows = evals.run(tests, a.host, a.model, a.vault, a.modes.split(","), company_name(a.vault), a.workers, a.num_ctx)
        meta = dict(company=company_name(a.vault), model=a.model, machine=a.machine, date=datetime.date.today().isoformat())
        out = pathlib.Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
        card = evals.scorecard(rows, meta)
        (out.parent / f"{out.name}.md").write_text(card)  # not with_suffix: model names like qwen3.8-27b contain dots
        (out.parent / f"{out.name}.jsonl").write_text("".join(json.dumps(dict(r, **meta)) + "\n" for r in rows))
        print(card)
