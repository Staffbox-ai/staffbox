"""The scorecard: run a customer's test set against the worker and grade every answer.

Three rungs of the fix ladder, measured separately so the before/after is visible:
  none        the model alone, told only the company name
  brain       the model plus the notes `brain.context` retrieves from the vault
  brain+calc  the same, plus a calculator tool the model calls with CALC: lines
"""
import ast, concurrent.futures as cf, json, operator, re, time, urllib.request
from . import brain

SYSTEM_NONE = "You are the office worker for {company}. Answer the question. End with one line: ANSWER: <answer>."
SYSTEM_BRAIN = (
    "You are the office worker for {company}. Use only the vault notes below. "
    "If the notes do not answer the question, the answer is NOT IN VAULT plus who to ask. Never guess. "
    "Show short working, then end with one line: ANSWER: <answer>.\n\n{context}"
)
CALC_RULE = (
    "\n\nArithmetic: do not do it in your head. Write each calculation on its own line as CALC: <expression> "
    "(numbers, + - * / and parentheses only), then stop and wait. You will get the results back. "
    "Only then give the final ANSWER line."
)
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.USub: operator.neg, ast.UAdd: operator.pos}


def calc(expr):
    def ev(n):
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](ev(n.operand))
        raise ValueError("unsupported")
    expr = expr.replace(",", "").replace("$", "").replace("×", "*").replace("x", "*").replace("%", "/100")
    return round(ev(ast.parse(expr.strip(), mode="eval").body), 4)


def chat(host, model, messages, num_ctx=None, timeout=600):
    body = {"model": model, "messages": messages, "stream": False, "think": False, "options": {"temperature": 0}}
    if num_ctx:
        body["options"]["num_ctx"] = num_ctx
    req = urllib.request.Request(f"{host.rstrip('/')}/api/chat", json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["message"]["content"], r.get("eval_count", 0)


def ask(host, model, vault, question, mode="brain", company="the company", num_ctx=None):
    if mode == "none":
        system, notes = SYSTEM_NONE.format(company=company), []
    else:
        ctx, notes = brain.context(vault, question)
        system = SYSTEM_BRAIN.format(company=company, context=ctx) + (CALC_RULE if mode == "brain+calc" else "")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    tokens, calls = 0, 0
    for _ in range(4):
        out, n = chat(host, model, msgs, num_ctx)
        tokens += n
        calcs = re.findall(r"(?m)^\s*CALC:\s*(.+)$", out)
        if mode != "brain+calc" or not calcs or "ANSWER:" in out.split("CALC:")[-1]:
            break
        results = []
        for c in calcs:
            try:
                results.append(f"{c.strip()} = {calc(c)}")
            except Exception:
                results.append(f"{c.strip()} = error (use numbers and + - * / only)")
            calls += 1
        msgs += [{"role": "assistant", "content": out}, {"role": "user", "content": "Results:\n" + "\n".join(results) + "\nNow give the final ANSWER line."}]
    return out, notes, tokens, calls


def final_answer(text):
    m = re.findall(r"ANSWER:\s*(.+)", text)
    return (m[-1] if m else text.strip().splitlines()[-1] if text.strip() else "").strip().strip("*").strip()


def money(s):
    m = re.findall(r"\$?\s*([0-9][0-9,]*\.?[0-9]*)", s)
    return float(m[-1].replace(",", "").rstrip(".")) if m else None


def grade(test, answer):
    a = answer.lower()
    kind = test["type"]
    if kind == "quote":
        got = money(answer)
        return got is not None and abs(got - test["expect"]) <= 0.011
    if kind == "triage":
        return re.sub(r"[^a-z_]", "", a.replace(" ", "_")) .endswith(test["expect"]) or a.strip(" .`'\"") == test["expect"]
    if kind == "unknown":
        return "not in vault" in a or "not in the vault" in a
    return all(x.lower() in a for x in test["expect"])  # lookup: every required phrase present


def run(tests, host, model, vault, modes, company, workers=1, num_ctx=None, progress=print):
    rows = []
    def one(job):
        mode, t = job
        t0 = time.time()
        try:
            out, notes, tok, calls = ask(host, model, vault, t["prompt"], mode, company, num_ctx)
            ans = final_answer(out)
            ok = grade(t, ans)
        except Exception as e:  # a failed call is a failed test, recorded, never skipped
            out, notes, tok, calls, ans, ok = f"ERROR {e}", [], 0, 0, f"ERROR {e}", False
        r = dict(id=t["id"], type=t["type"], mode=mode, ok=ok, answer=ans[:200], expect=t["expect"], notes=notes,
                 tokens=tok, calc_calls=calls, seconds=round(time.time() - t0, 1), raw=out[-1500:])
        progress(f"{'PASS' if ok else 'FAIL'} {mode:<10} {t['id']:<12} {ans[:70]!r}")
        return r
    jobs = [(m, t) for m in modes for t in tests]
    with cf.ThreadPoolExecutor(workers) as ex:
        rows = list(ex.map(one, jobs))
    return rows


def scorecard(rows, meta):
    modes = list(dict.fromkeys(r["mode"] for r in rows))
    types = list(dict.fromkeys(r["type"] for r in rows))
    lines = [f"# Scorecard: {meta['company']}", "",
             f"Model `{meta['model']}` on {meta['machine']} · {meta['date']} · {len(rows)//len(modes)} tests per mode · graded automatically, no human edits.", "",
             "| Task type | " + " | ".join(modes) + " |", "|---|" + "---|" * len(modes)]
    for t in types + ["**all**"]:
        cells = []
        for m in modes:
            rs = [r for r in rows if r["mode"] == m and (t == "**all**" or r["type"] == t)]
            p = sum(r["ok"] for r in rs)
            cells.append(f"{p}/{len(rs)} ({100*p//max(len(rs),1)}%)")
        lines.append(f"| {t} | " + " | ".join(cells) + " |")
    secs = {m: sum(r["seconds"] for r in rows if r["mode"] == m) / max(1, sum(1 for r in rows if r["mode"] == m)) for m in modes}
    lines += ["", "Average seconds per answer: " + " · ".join(f"{m} {s:.1f}s" for m, s in secs.items()), "",
              "Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.", "",
              "## Misses", "", "| Mode | Test | Expected | Got |", "|---|---|---|---|"]
    for r in rows:
        if not r["ok"]:
            lines.append(f"| {r['mode']} | {r['id']} | {r['expect']} | {r['answer'][:90].replace('|', '/')} |")
    return "\n".join(lines) + "\n"
