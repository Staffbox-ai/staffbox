"""Offline check of the quote code on the DEV sets: the model's reply is fixed to a correct extraction (item, quantity,
unit as the customer wrote it), so every miss here is a code miss. No model, no GPU.
Run: python3 scripts/offline_check.py   (exit 1 on any miss)"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from staffbox import actions, evals

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIX = json.loads((ROOT / "evals/fixtures/dev-extractions.json").read_text())


def route(pricing, request, reply):
    real = evals.chat
    try:
        evals.chat = lambda *a, **k: (reply, 0)
        return evals.route_quote("", "", pricing, request)[0]
    finally:
        evals.chat = real


def from_prompt(p, prompt):
    """A standard-set quote prompt names its SKU (code, or exact description) and its quantity."""
    m = re.search(r"\(([A-Z0-9/-]+)\)|\bof ([A-Z]{1,3}-[A-Z0-9/-]+)", prompt)
    sku = (m.group(1) or m.group(2)) if m else max((k for k, v in p["skus"].items() if v["desc"] in prompt), key=lambda k: len(p["skus"][k]["desc"]))
    q = re.search(r"(\d+)\s*(ft|feet|lb|x|of)\b", prompt)
    unit = {"feet": "ft", "ft": "ft", "lb": "lb"}.get(q.group(2), "")
    return f"QUOTE: sku={sku}; qty={q.group(1)}" + (f"; unit={unit}" if unit else "")


def check(verbose=False):
    results = {}
    for ex, files in FIX.items():
        if ex.startswith("_"):
            continue
        p = actions.load_pricing(ROOT / "examples" / ex / "vault")
        for fname, fixed in files.items():
            ok, n, misses = 0, 0, []
            for t in map(json.loads, (ROOT / "examples" / ex / fname).read_text().splitlines()):
                if t["id"] not in fixed and t["type"] != "quote":
                    continue  # lookups, routing and non-price unknowns never reach the quote code
                reply = fixed.get(t["id"]) or from_prompt(p, t["prompt"])
                out = route(p, t["prompt"], reply)
                good = evals.grade(t, evals.final_answer(out))
                n += 1; ok += good
                if not good or verbose:
                    misses.append((t["id"], t["expect"], out.replace("\n", " / ")[:300]))
            results[f"{ex}/{fname}"] = (ok, n, misses)
    return results


if __name__ == "__main__":
    res = check("-v" in sys.argv)
    for k, (ok, n, misses) in res.items():
        print(f"{k}: {ok}/{n}")
        for m in misses:
            print("   ", *m)
    sys.exit(0 if all(ok == n for ok, n, _ in res.values()) else 1)
