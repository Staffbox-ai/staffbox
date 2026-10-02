"""The scorecard: run a customer's test set against the worker and grade every answer.

Three rungs of the fix ladder, measured separately so the before/after is visible:
  none        the model alone, told only the company name
  brain       the model plus the notes `brain.context` retrieves from the vault
  brain+calc  the same, plus a calculator tool the model calls with CALC: lines
  brain+quote the brain, plus the quote action (staffbox.actions): a short routing call extracts SKU, quantity
              and options, code prices the line from the vault's own pricing notes; anything else goes to `brain`
"""
import ast, concurrent.futures as cf, json, operator, re, time, urllib.request
from . import actions, brain

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


def chat_openai(host, model, messages, timeout=600):
    """Any OpenAI-compatible endpoint (a cloud comparison, never the default). Key from STAFFBOX_CLOUD_KEY."""
    import os
    body = {"model": model, "messages": messages, "temperature": 0}
    req = urllib.request.Request(f"{host.rstrip('/')}/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": f"Bearer {os.environ['STAFFBOX_CLOUD_KEY']}"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["choices"][0]["message"]["content"] or "", r.get("usage", {}).get("completion_tokens", 0)


def chat(host, model, messages, num_ctx=None, timeout=600):
    if host.startswith("https://") and "/v1" in host:
        return chat_openai(host, model, messages, timeout)
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
    pricing = actions.load_pricing(vault) if mode == "brain+quote" else None
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    tokens, calls = 0, 0
    if mode == "brain+quote" and pricing["skus"]:
        out, n, calls = route_quote(host, model, pricing, question, num_ctx)
        tokens += n
        if out:
            return out, notes, tokens, calls
    for rnd in range(4):
        out, n = chat(host, model, msgs, num_ctx)
        tokens += n
        calcs = re.findall(r"(?m)^\s*CALC:\s*(.+)$", out)
        # Small models often write CALC lines and a guessed ANSWER in one reply; the first round's CALCs are
        # always evaluated and sent back, so the final answer is written after seeing the exact results.
        if mode != "brain+calc" or not calcs or (rnd > 0 and "ANSWER:" in out.split("CALC:")[-1]):
            break
        results = []
        for c in calcs:
            try:
                results.append(f"{c.strip()} = {calc(c)}")
            except Exception:
                results.append(f"{c.strip()} = error (use numbers and + - * / only)")
            calls += 1
        msgs += [{"role": "assistant", "content": out}, {"role": "user", "content": "Results:\n" + "\n".join(results) + "\nUse these exact results (rounded to the cent where the procedure says so). Recheck your working, then give the final ANSWER line."}]
    return out, notes, tokens, calls


ROUTE = (
    "You turn an office request into one pricing call, or say NONE.\n"
    "Price list SKUs: {skus}\n{opts}"
    "If the request asks for the price of a quantity of one item, reply with ONLY one line:\n"
    "QUOTE: sku=<SKU from the list, or the closest description if no SKU fits>; qty=<number>{optfmt}\n"
    "Use the SKU whose description matches the request. If the item is not on the list, still write the item as sku=<what they asked for>.\n"
    "If the request is anything else (a policy question, routing an email, a non-price question), reply with ONLY: NONE"
)


def route_quote(host, model, pricing, question, num_ctx=None):
    """Action routing: a short dedicated call decides whether this is a quote, and extracts SKU, qty and options.
    Code prices the line. Returns (answer text or "", tokens, calls)."""
    skus = "; ".join(f"{k} = {v['desc']}" for k, v in pricing["skus"].items())
    opts = "".join(f"Options for {a}: {', '.join(t)}\n" for a, t in pricing["surcharges"].items())
    optfmt = "".join(f"; {a}=<value if named>" for a in pricing["surcharges"])
    out, n = chat(host, model, [{"role": "system", "content": ROUTE.format(skus=skus, opts=opts, optfmt=optfmt)},
                                {"role": "user", "content": question}], num_ctx)
    m = re.search(r"QUOTE:\s*(.+)", out)
    if not m:
        return "", n, 0
    try:
        sku, qty, o = actions.parse_quote_line(m.group(1))
        o = {k: v for k, v in o.items() if v and not v.startswith("<")}
        sku, qty, o = actions.resolve(pricing, question, sku, qty, o)
        total, work = actions.quote(pricing, sku, qty, o)
    except Exception as e:
        return "", n, 1
    if total is None:
        return f"{work}.\nANSWER: NOT IN VAULT: {work}. Ask the person who owns pricing (see people).", n, 1
    return f"Quote action: {work}.\nANSWER: ${total:,.2f}", n, 1


def final_answer(text):
    m = re.findall(r"ANSWER:\s*(.+)", text)
    return (m[-1] if m else text.strip().splitlines()[-1] if text.strip() else "").strip().strip("*").strip()


def money(s):
    """The dollar amount in an answer: the last $-prefixed number, else the last number."""
    m = re.findall(r"\$\s*([0-9][0-9,]*\.?[0-9]*)", s) or re.findall(r"([0-9][0-9,]*\.?[0-9]*)", s)
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
        progress(f"{'PASS' if ok else 'FAIL'} {mode:<10} {t['id']:<12} {ans[:70]!r}", flush=True)
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
    lines += ["", "Average seconds per answer: " + " · ".join(f"{m} {s:.1f}s" for m, s in secs.items()),
              "90th-percentile seconds: " + " · ".join(f"{m} {p90([r['seconds'] for r in rows if r['mode'] == m]):.1f}s" for m in modes)]
    if any(r["type"] == "quote" for r in rows):
        lines += ["", "Quotes, the pilot pass bar (a refusal is a miss; \"right\" means the exact line total, no edits):", "",
                  "| Mode | Priced | Right of priced | Right of all |", "|---|---|---|---|"]
        for m in modes:
            q = quote_quality([r for r in rows if r["mode"] == m])
            lines.append(f"| {m} | {q['priced']}/{q['n']} ({q['priced_pct']}%) | {q['right']}/{q['priced']} ({q['right_of_priced_pct']}%) | {q['right']}/{q['n']} |")
    lines += ["",
              "Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.", "",
              "Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or \"not in vault\" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.", "",
              "## Misses", "", "| Mode | Test | Expected | Got |", "|---|---|---|---|"]
    for r in rows:
        if not r["ok"]:
            lines.append(f"| {r['mode']} | {r['id']} | {r['expect']} | {r['answer'][:90].replace('|', '/')} |")
    return "\n".join(lines) + "\n"


def p90(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(0.9 * len(xs)))] if xs else 0.0


def priced(answer):
    """True when the answer commits to a dollar figure (not a refusal or an escalation)."""
    a = answer.lower()
    return money(answer) is not None and "not in vault" not in a and "not in the vault" not in a and "$" in answer


def quote_quality(rows):
    """The pilot pass bar for quote rows: share priced, share right of those priced, right of all."""
    q = [r for r in rows if r["type"] == "quote"]
    pr = [r for r in q if priced(r["answer"])]
    right = sum(r["ok"] for r in pr)
    pct = lambda a, b: 100 * a // b if b else 0
    return dict(n=len(q), priced=len(pr), right=right, priced_pct=pct(len(pr), len(q)), right_of_priced_pct=pct(right, len(pr)))
