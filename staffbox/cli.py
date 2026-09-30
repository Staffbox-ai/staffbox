"""staffbox: check the brain, ask it, log to it, and score the worker.

  staffbox check   VAULT                       lint frontmatter, links, dates; log.md append-only
  staffbox context VAULT "question"            print the notes the worker would read
  staffbox ask     VAULT "question" [--model]  answer from the brain with a local model
  staffbox log     VAULT "asked" "did" [--could-not ...]   append one line to log.md
  staffbox eval    VAULT TESTS.jsonl [--model --host --modes --out]   run the scorecard
"""
import argparse, datetime, json, os, pathlib, platform, sys
from . import brain, evals

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
    s.add_argument("--model", default="qwen3:8b"); s.add_argument("--host", default=HOST); s.add_argument("--mode", default="brain+calc")
    s = sub.add_parser("log"); s.add_argument("vault"); s.add_argument("asked"); s.add_argument("did"); s.add_argument("--could-not", default="nothing")
    s = sub.add_parser("eval"); s.add_argument("vault"); s.add_argument("tests")
    s.add_argument("--model", default="qwen3:8b"); s.add_argument("--host", default=HOST)
    s.add_argument("--modes", default="none,brain,brain+calc"); s.add_argument("--machine", default=platform.node())
    s.add_argument("--workers", type=int, default=1); s.add_argument("--num-ctx", type=int); s.add_argument("--limit", type=int)
    s.add_argument("--out", default="scorecard")
    a = ap.parse_args(argv)

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
