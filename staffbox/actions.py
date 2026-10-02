"""Actions: deterministic tools the worker calls instead of doing the work in its head.

quote  prices one line from the vault's own pricing notes (any note tagged `pricing`):
       a table with a SKU column and a price column (optional setup-fee column),
       optional surcharge tables (first column = option name, second = "N%"),
       and a volume-discount table (quantity ranges -> "N%" or "none").
       line = round(round(base * (1 + surcharges), 2) * qty * (1 - discount), 2) + qty * setup
The model only reads the request (SKU, quantity, options); the arithmetic and the tier lookup are code.
"""
import re
from . import brain

PCT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")


def _money(s):
    m = re.search(r"\$?\s*([0-9][0-9,]*\.?[0-9]*)", s)
    return float(m.group(1).replace(",", "")) if m else None


def _tables(text):
    """Every markdown table in a note as (header cells, rows of cells)."""
    out, cur = [], []
    for line in text.splitlines() + [""]:
        if line.strip().startswith("|"):
            cur.append([c.strip().strip("*") for c in line.strip().strip("|").split("|")])
        elif cur:
            if len(cur) > 2:
                out.append((cur[0], [r for r in cur[2:] if len(r) == len(cur[0])]))
            cur = []
    return out


def _range(label):
    s = label.lower().replace(",", "")
    if m := re.search(r"(\d+)\s*(?:or more|\+|and up)", s):
        return int(m.group(1)), float("inf")
    if m := re.search(r"(\d+)\s*(?:to|-|–)\s*(\d+)", s):
        return int(m.group(1)), int(m.group(2))
    if m := re.search(r"(?:under|fewer than|less than|below)\s*(\d+)", s):
        return 0, int(m.group(1)) - 1
    return None


def load_pricing(vault):
    skus, surcharges, tiers = {}, {}, []
    notes, _ = brain.load(vault)
    for n in notes.values():
        if "pricing" not in [t.lower() for t in brain._aslist(n.meta.get("tags"))]:
            continue
        for head, rows in _tables(n.body):
            h = [c.lower() for c in head]
            if "sku" in h and any("price" in c for c in h):
                i_sku, i_desc = h.index("sku"), next((i for i, c in enumerate(h) if "desc" in c), None)
                i_price = next(i for i, c in enumerate(h) if "price" in c)
                i_setup = next((i for i, c in enumerate(h) if "setup" in c), None)
                for r in rows:
                    skus[r[i_sku].upper()] = dict(desc=r[i_desc] if i_desc is not None else "", price=_money(r[i_price]),
                                                  setup=_money(r[i_setup]) if i_setup is not None else 0.0)
            elif len(h) == 2 and any(_range(r[0]) for r in rows) and "discount" in h[1]:
                for r in rows:
                    rg = _range(r[0])
                    if rg:
                        m = PCT.match(r[1])
                        tiers.append((rg[0], rg[1], float(m.group(1)) / 100 if m else 0.0))
            elif len(h) == 2 and rows and all(PCT.match(r[1]) for r in rows):
                surcharges[h[0].lower()] = {r[0].lower(): float(PCT.match(r[1]).group(1)) / 100 for r in rows}
    return dict(skus=skus, surcharges=surcharges, tiers=tiers)


def parse_quote_line(line):
    """'sku=MON-27; qty=12; finish=stained' -> ('MON-27', 12, {'finish': 'stained'})."""
    bits = [p.strip() for p in re.split(r"[;,]\s*", line.strip()) if p.strip()]
    parts = dict(p.split("=", 1) for p in bits if "=" in p)
    parts = {k.strip().lower(): v.strip().strip("'\"") for k, v in parts.items()}
    if "sku" not in parts and bits and "=" not in bits[0]:
        parts["sku"] = bits[0]  # "QUOTE: AP-6E; qty=40"
    sku, qty = parts.pop("sku", ""), parts.pop("qty", parts.pop("quantity", ""))
    return sku.upper(), int(float(qty)) if qty else 0, parts


def quote(pricing, sku, qty, options=None):
    """Price one line. Returns (total or None, one-line working that explains it)."""
    options = {k.lower(): str(v).lower() for k, v in (options or {}).items()}
    no_setup = options.pop("setup", "yes") in ("no", "none", "false", "without", "0")
    item = pricing["skus"].get(sku.upper())
    if not sku:
        return None, "no stocked item on the price list matches the request: special or custom order, not priced here"
    if not item:
        return None, f"{sku} is not on the price list: special or custom order, not priced here"
    if qty <= 0:
        return None, "quantity missing"
    pct, used = 0.0, []
    for attr, table in pricing["surcharges"].items():
        val = options.get(attr) or options.get(attr.rstrip("s"))
        if val is None:  # never assume the cheapest option: an unstated or unknown option is not priced
            return None, f"{attr} not stated or not offered (offered: {', '.join(table)}): ask which, or it is custom"
        if val not in table:
            return None, f"{attr} '{val}' is not offered (options: {', '.join(table)}): custom, not priced here"
        pct += table[val]
        used.append(f"{val} +{table[val]:.0%}")
    unit = round(item["price"] * (1 + pct), 2)
    disc = next((d for lo, hi, d in pricing["tiers"] if lo <= qty <= hi), 0.0)
    goods = round(round(unit * qty, 2) * (1 - disc), 2)
    setup = 0.0 if no_setup else round(qty * item["setup"], 2)
    total = round(goods + setup, 2)
    work = f"{qty} x {sku} at ${unit:,.2f}" + (f" ({', '.join(used)})" if used else "")
    work += f" = ${unit * qty:,.2f}" + (f", less {disc:.0%} = ${goods:,.2f}" if disc else "")
    work += (f", plus setup {qty} x ${item['setup']:,.2f} = ${setup:,.2f}" if setup else (", no setup" if no_setup and item["setup"] else "")) + f"; line total ${total:,.2f}"
    return total, work


def resolve(pricing, question, sku, qty, options):
    """Check the model's extraction against the request text; the text wins when they disagree.
    SKU: must be on the price list, else a SKU code or description found in the request.
    Quantity: must be a number in the request that is not part of a size (6x24) or a SKU code."""
    q = words_to_digits(question).upper()
    if sku not in pricing["skus"]:
        codes = [k for k in pricing["skus"] if k in q]
        sing = lambda t: re.sub(r"(\w)S\b", r"\1", t.upper())  # "SHAKER DOORS" ~ "SHAKER DOOR"
        descs = [k for k, v in pricing["skus"].items() if v["desc"] and sing(v["desc"]) in sing(q)]
        found = codes or sorted(descs, key=lambda k: -len(pricing["skus"][k]["desc"]))
        sku = found[0] if found else (match_description(pricing, sku) or sku)
    text = q
    for k, v in pricing["skus"].items():
        text = text.replace(k, " ").replace(v["desc"].upper(), " ") if v["desc"] else text.replace(k, " ")
    text = re.sub(r"\d+(?:\.\d+)?\s*[X×]\s*\d+(?:\.\d+)?", " ", text)
    text = re.sub(r"\$\s*[0-9][0-9,]*(?:\.\d+)?", " ", text)
    nums = [int(n) for n in re.findall(r"(?<![\w.-])(\d{1,5})(?![\w.%])", text)]
    if qty not in nums and len(nums) == 1:
        qty = nums[0]
    opts = dict(options)
    for attr, table in pricing["surcharges"].items():
        named = [o for o in sorted(table, key=len, reverse=True) if re.search(rf"\b{re.escape(o.upper())}\b", q)]
        if named and opts.get(attr) not in table:
            opts[attr] = named[0]
    return sku, qty, opts


WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
                                     "sixteen seventeen eighteen nineteen".split())}
WORDS.update({"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90})
SYN = {"screen": "monitor", "display": "monitor", "wi": "wifi", "ap": "access point", "battery": "ups", "backup": "ups",
       "docking": "dock", "usbc": "usb-c", "pc": "desktop", "computer": "desktop", "notebook": "laptop"}


def words_to_digits(text):
    """'two dozen' -> '24', 'a dozen' -> '12', 'twenty-five' -> '25', 'just the one' -> '1'."""
    t = re.sub(r"\bjust the one\b|\bthe one\b", " 1 ", text, flags=re.I)
    def num(m):
        a, b = m.group(1).lower(), (m.group(2) or "").lower()
        return str(WORDS[a] + (WORDS[b] if b else 0))
    t = re.sub(r"\b(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[- ](one|two|three|four|five|six|seven|eight|nine))?\b", num, t, flags=re.I)
    t = re.sub(r"\b(a|one|two|three|four|five|six)\s+dozen\b", lambda m: str(12 * (1 if m.group(1).lower() in ("a", "one") else WORDS[m.group(1).lower()])), t, flags=re.I)
    t = re.sub(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)\b",
               lambda m: str(WORDS[m.group(1).lower()]), t, flags=re.I)
    return t


def _tokens(s):
    out = set()
    for w in re.findall(r"[a-z0-9]+", s.lower().replace("usb-c", "usbc").replace("wi-fi", "wifi")):
        w = re.sub(r"(?<=[a-z]{2})s$", "", w)
        w = re.sub(r"^(\d+)(?:inch)$", r"\1in", w)
        out |= set(SYN.get(w, w).split())
    return out - {"the", "a", "of", "and", "for", "with", "x", "port"} | ({"port"} & set())


def match_description(pricing, text):
    """The stocked SKU whose description best matches free text, or None when nothing clearly matches.
    A word found in only one item's description is decisive; otherwise two shared words are needed. A tie means ask."""
    t = _tokens(text)
    descs = {k: _tokens(v["desc"]) | _tokens(k) for k, v in pricing["skus"].items()}
    df = {}
    for d in descs.values():
        for w in d:
            df[w] = df.get(w, 0) + 1
    best = []
    for k, d in descs.items():
        hit = d & t
        unique = any(df[w] == 1 for w in hit)
        if hit and (unique or len(hit) >= 2):
            best.append((len(hit) + (1 if unique else 0), k))
    best.sort(reverse=True)
    if not best or (len(best) > 1 and best[0][0] == best[1][0]):
        return None
    return best[0][1]
