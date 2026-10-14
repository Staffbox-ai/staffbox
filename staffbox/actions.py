"""Actions: deterministic tools the worker calls instead of doing the work in its head.

quote  prices one line from the vault's own pricing notes (any note tagged `pricing`):
       a table with a SKU column and a price column (optional setup-fee column),
       optional surcharge tables (first column = option name, second = "N%"),
       and a volume-discount table (quantity ranges -> "N%" or "none").
       line = round(round(base * (1 + surcharges), 2) * qty * (1 - discount), 2) + qty * setup
The model only reads the request (SKU, quantity, options); the arithmetic and the tier lookup are code.

Trade price books (all optional, all read from the vault, nothing trade-specific in code):
  Unit column     ea, ft or m (sold by length), "box of N" (packs), or a unit like "stick" whose description says
                  "10 ft stick". Requests in another unit are converted (pieces -> boxes, feet -> sticks, reels -> feet)
                  only when the conversion is whole; otherwise the worker asks.
  Stock column    anything but "stocked"/"yes" (e.g. "special order") is never priced: decline and ask.
  Reels and cuts  full reel/coil length from the row ("500 ft reel"); "minimum cut: N ft" and "cut charge: $X per cut"
                  (or "cut charge $X under N ft") from any pricing note or the row's notes cell. "no cut charge" bullets exempt
                  the group they name.
  Price levels    "**Contractor level**: 12% off list" bullets (or a Level | Discount table). Used only when the request
                  or a customer note (frontmatter `price_level:`) names the level; otherwise list, and the answer says so.
  Group surcharge a table whose first column is a product group, e.g. "copper wire and cable (THHN, NM-B) | 8% | 1 October
                  2026 until further notice": applies to SKUs whose description names a term in brackets, on the line after
                  the price level, using the row in effect today.
  Synonyms        a note named `synonyms` (or tagged synonyms): | customers write | we mean | rows, applied to the request first.
Order: goods -> quantity break -> price level -> group surcharge -> cut charge, rounding to the cent at each step.
"""
import datetime
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


LENGTH = {"ft": "ft", "feet": "ft", "foot": "ft", "'": "ft", "lf": "ft", "m": "m", "meter": "m", "meters": "m", "metre": "m", "metres": "m"}
MONTHS = {m: i for i, m in enumerate("january february march april may june july august september october november december".split(), 1)}
IN_STOCK = {"stocked", "stock", "yes", "y", "in stock", "stock item"}


def _dates(s):
    """Dates written '1 October 2026' or '2026-10-01', in order."""
    out = []
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})|(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", s):
        try:
            out.append(datetime.date(int(m[1]), int(m[2]), int(m[3])) if m[1] else
                       datetime.date(int(m[6]), MONTHS[m[5].lower()], int(m[4])))
        except (KeyError, ValueError):
            pass
    return out


def _group(label):
    """'copper wire and cable (THHN, NM-B, MC)' -> ({'THHN','NM-B','MC'}, {'copper','wire','cable'}): bracketed terms
    name the members; with no brackets every word of the label must be in the item description."""
    terms = {t.strip().upper() for b in re.findall(r"\(([^)]*)\)", label) for t in b.split(",") if t.strip()}
    return terms, _tokens(re.sub(r"\([^)]*\)", " ", label).split(",")[0]) - {"and", "or", "before", "that"}


def in_group(group, sku, desc):
    terms, words = group
    hay = f"{sku} {desc}".upper()
    if terms:
        return any(re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", hay) for t in terms)
    return bool(words) and words <= _tokens(desc)


def _row_item(head, r):
    """One price-book row -> dict. Optional columns: Unit, Stock, Setup, and any notes cell (reel length, cut rule)."""
    h = [c.lower() for c in head]
    i_desc = next((i for i, c in enumerate(h) if "desc" in c), None)
    i_price = next(i for i, c in enumerate(h) if "price" in c)
    i_setup = next((i for i, c in enumerate(h) if "setup" in c), None)
    i_unit = next((i for i, c in enumerate(h) if c in ("unit", "uom", "unit of measure", "sold by", "sold per")), None)
    i_stock = next((i for i, c in enumerate(h) if c in ("stock", "stocked", "status", "availability")), None)
    row = " ".join(r)
    unit = (r[i_unit] if i_unit is not None else "").strip().lower()
    if not unit and (m := re.search(r"(?:/|per\s+)(ft|foot|m|meter|metre)\b", r[i_price], re.I)):
        unit = m.group(1).lower()  # "$0.38/ft"
    item = dict(desc=r[i_desc] if i_desc is not None else "", price=_money(r[i_price]),
                setup=_money(r[i_setup]) if i_setup is not None else 0.0, unit=LENGTH.get(unit, unit) or None,
                pack=None, per=None, full=None, stock=True, stock_label="")
    if m := re.search(r"\b(?:box|pack|case|bag|carton|pkg|package)\s+of\s+(\d+)", unit if i_unit is not None else row, re.I):
        item["pack"] = int(m.group(1))
        item["unit"] = item["unit"] or f"pack of {item['pack']}"
    elif item["unit"] in ("ft", "m"):
        if m := re.search(rf"(\d+)\s*{item['unit']}\.?\s+(?:reel|coil|spool|roll)\b", row, re.I):
            item["full"] = int(m.group(1))
    elif item["unit"] and item["unit"] not in ("ea", "each", "pc", "piece"):
        if m := re.search(rf"(\d+(?:\.\d+)?)\s*(ft|m)\.?\s+{re.escape(item['unit'])}\b", row, re.I):
            item["per"] = (float(m.group(1)), m.group(2).lower())  # "10 ft stick"
    if i_stock is not None:
        item["stock_label"] = r[i_stock].strip()
        item["stock"] = item["stock_label"].lower() in IN_STOCK
    if cut := _cut_rule(row):
        item["cut"] = cut
    return item


def _cut_rule(text):
    """'Minimum cut: 25 feet ... Cut charge: $7.50 per cut' or 'cut charge $5 under 100 ft' -> dict, or {}."""
    t = text.replace("*", "")
    out = {}
    if m := re.search(r"cut charge\W{0,3}\$\s*([0-9]+(?:\.[0-9]+)?)([^.\n|]*)", t, re.I):
        out["charge"] = float(m.group(1))
        if u := re.search(r"(?:under|below|less than)\s*(\d+)\s*(?:ft|feet|foot|m)\b", m.group(2), re.I):
            out["under"] = int(u.group(1))
    if m := re.search(r"minimum cut\W{0,3}(\d+)\s*(?:ft|feet|foot|m)\b", t, re.I):
        out["min"] = int(m.group(1))
    return out


def _levels(body, note_is_levels):
    """'- **Contractor level**: 12% off list' -> {'contractor': 0.12}; '- **List**: the price in the price book' -> {'list': 0}."""
    out = {}
    for m in re.finditer(r"(?m)^\s*[-*]\s*\*\*([^*]+)\*\*\s*:\s*(.+)$", body):
        label, rest = m.group(1).strip().lower(), m.group(2)
        if not (note_is_levels or "level" in label):
            continue
        name = re.sub(r"\b(level|price|pricing|account)s?\b", " ", label).strip() or label
        if pct := re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:off|discount|below)", rest, re.I):
            out[name] = float(pct.group(1)) / 100
        elif mult := re.search(r"(?:multiplier|[x×])\s*(0?\.\d+)", rest, re.I):
            out[name] = round(1 - float(mult.group(1)), 6)
        elif name == "list":
            out[name] = 0.0
    return out


def load_pricing(vault, today=None):
    skus, surcharges, tiers, groups, levels, customers, synonyms = {}, {}, [], [], {}, {}, []
    cut, cut_exempt, length_no_break = {}, [], False
    today = today or datetime.date.today()
    notes, _ = brain.load(vault)
    for n in notes.values():
        tags = [t.lower() for t in brain._aslist(n.meta.get("tags"))]
        if lvl := n.meta.get("price_level") or n.meta.get("price-level"):  # a customer note naming its account level
            for name in [n.name.replace("-", " ")] + brain._aslist(n.meta.get("aliases")):
                customers[name.lower()] = lvl.lower().replace(" level", "").strip()
        if n.name.lower() == "synonyms" or "synonyms" in tags:
            for head, rows in _tables(n.body):
                for r in rows:
                    if len(r) >= 2 and r[0] and r[1]:
                        synonyms += [(k.strip(), r[1].strip()) for k in r[0].split(",") if k.strip()]
        if "pricing" not in tags:
            continue
        is_levels = "level" in n.name.lower() or any("level" in a.lower() for a in brain._aslist(n.meta.get("aliases")))
        levels.update(_levels(n.body, is_levels))
        cut.update(_cut_rule(n.body))
        for m in re.finditer(r"(?m)^\s*[-*]\s*([^:\n]+):[^\n]*\bno cut charge\b", n.body.replace("*", "")):
            cut_exempt.append(_group(m.group(1)))
        if re.search(r"(?:by the|per)\s+(?:foot|meter|metre|length)[^.\n]*\bno (?:quantity|volume) (?:break|discount)", n.body, re.I):
            length_no_break = True
        for head, rows in _tables(n.body):
            h = [c.lower() for c in head]
            if "sku" in h and any("price" in c for c in h):
                i_sku = h.index("sku")
                for r in rows:
                    skus[r[i_sku].upper()] = _row_item(head, r)
            elif re.search(r"group|product|applies to", h[0]) and any("surcharge" in c for c in h[1:]):
                i_pct = next(i for i, c in enumerate(h) if "surcharge" in c)
                i_eff = next((i for i, c in enumerate(h) if "effective" in c or "dates" in c), None)
                key = lambda label: re.split(r"[,(]", label)[0].strip().lower()
                terms = {}  # rows naming the same group ("copper wire and cable, before that") share its bracketed terms
                for r in rows:
                    terms.setdefault(key(r[0]), set()).update(_group(r[0])[0])
                for r in rows:
                    d = _dates(r[i_eff]) if i_eff is not None else []
                    if d and not (d[0] <= today and (len(d) < 2 or today <= d[1])):
                        continue  # not in effect today
                    m = re.search(r"(\d+(?:\.\d+)?)\s*%", r[i_pct])
                    groups.append(((terms[key(r[0])], _group(r[0])[1]), float(m.group(1)) / 100 if m else 0.0, r[0]))
            elif any("level" in c for c in h) and len(h) >= 2:
                for r in rows:
                    if m := re.search(r"(\d+(?:\.\d+)?)\s*%", " ".join(r[1:])):
                        levels[re.sub(r"\b(level|price|pricing|account)s?\b", " ", r[0].lower()).strip()] = float(m.group(1)) / 100
            elif len(h) == 2 and any(_range(r[0]) for r in rows) and "discount" in h[1]:
                for r in rows:
                    rg = _range(r[0])
                    if rg:
                        m = PCT.match(r[1])
                        tiers.append((rg[0], rg[1], float(m.group(1)) / 100 if m else 0.0))
            elif len(h) == 2 and rows and all(PCT.match(r[1]) for r in rows):
                surcharges[h[0].lower()] = {r[0].lower(): float(PCT.match(r[1]).group(1)) / 100 for r in rows}
    if levels and "list" not in levels:
        levels["list"] = 0.0
    return dict(skus=skus, surcharges=surcharges, tiers=tiers, groups=groups, levels=levels, customers=customers,
                synonyms=sorted(synonyms, key=lambda kv: -len(kv[0])), cut=cut, cut_exempt=cut_exempt,
                length_no_break=length_no_break)


def parse_quote_line(line):
    """'sku=MON-27; qty=12; finish=stained' -> ('MON-27', 12, {'finish': 'stained'})."""
    bits = [p.strip() for p in re.split(r"[;,]\s*", line.strip()) if p.strip()]
    parts = dict(p.split("=", 1) for p in bits if "=" in p)
    parts = {k.strip().lower(): v.strip().strip("'\"") for k, v in parts.items()}
    if "sku" not in parts and bits and "=" not in bits[0]:
        parts["sku"] = bits[0]  # "QUOTE: AP-6E; qty=40"
    sku, qty = parts.pop("sku", ""), parts.pop("qty", parts.pop("quantity", ""))
    n = re.search(r"\d+(?:\.\d+)?", qty.replace(",", ""))  # "1000ft", "1,000" or "some" (= missing)
    return sku.upper(), int(float(n.group(0))) if n else 0, parts


def quote(pricing, sku, qty, options=None, level=None):
    """Price one line. qty is in the item's own unit (see to_unit). Returns (total or None, one-line working)."""
    options = {k.lower(): str(v).lower() for k, v in (options or {}).items()}
    no_setup = options.pop("setup", "yes") in ("no", "none", "false", "without", "0")
    options.pop("unit", None)
    item = pricing["skus"].get(sku.upper())
    if not sku:
        return None, "no stocked item on the price list matches the request: special or custom order, not priced here"
    if not item:
        return None, f"{sku} is not on the price list: special or custom order, not priced here"
    if not item.get("stock", True):
        return None, f"{sku} ({item['desc']}) is {item['stock_label'] or 'not stocked'}: not priced here, never substituted"
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
    by_length = item.get("unit") in ("ft", "m")
    u = f" {item['unit']}" if by_length else ""
    unit = round(item["price"] * (1 + pct), 2)
    disc = 0.0 if by_length and pricing.get("length_no_break") else next((d for lo, hi, d in pricing["tiers"] if lo <= qty <= hi), 0.0)
    goods = round(round(unit * qty, 2) * (1 - disc), 2)
    work = f"{qty:g}{u} x {sku} at ${unit:,.2f}" + (f"/{item['unit']}" if by_length else "") + (f" ({', '.join(used)})" if used else "")
    work += f" = ${unit * qty:,.2f}" + (f", less {disc:.0%} = ${goods:,.2f}" if disc else "")
    if pricing.get("levels"):
        name = (level or "list").lower()
        if name not in pricing["levels"]:
            return None, f"price level '{name}' is not in the price book (levels: {', '.join(pricing['levels'])}): ask who owns pricing"
        lp = pricing["levels"][name]
        if lp:
            goods = round(goods * (1 - lp), 2)
            work += f", {name} level -{lp * 100:g}% = ${goods:,.2f}"
        else:
            work += ", list price" + ("" if level else " (no account level named)")
    hits = {(round(g_pct, 6), label) for g, g_pct, label in pricing.get("groups", []) if in_group(g, sku, item["desc"])}
    if len({h[0] for h in hits}) > 1:
        return None, f"{sku} matches more than one surcharge group ({'; '.join(sorted(l for _, l in hits))}): ask who owns pricing"
    if hits and (g_pct := next(iter(hits))[0]):
        goods = round(goods * (1 + g_pct), 2)
        work += f", plus {g_pct * 100:g}% {next(iter(hits))[1].split('(')[0].strip()} surcharge = ${goods:,.2f}"
    rule = item.get("cut") or pricing.get("cut") or {}
    if by_length and rule and not any(in_group(g, sku, item["desc"]) for g in pricing.get("cut_exempt", [])):
        full = item.get("full")
        rem = qty % full if full else qty
        if rem and rule.get("min") and rem < rule["min"]:
            return None, f"{qty:g}{u} of {sku} needs a {rem:g}{u} cut, under the {rule['min']}{u} minimum cut: ask the customer"
        if rule.get("charge") and (qty < rule["under"] if rule.get("under") else rem):
            goods = round(goods + rule["charge"], 2)
            work += f", plus cut charge ${rule['charge']:,.2f} = ${goods:,.2f}"
    setup = 0.0 if no_setup else round(qty * item["setup"], 2)
    total = round(goods + setup, 2)
    work += (f", plus setup {qty} x ${item['setup']:,.2f} = ${setup:,.2f}" if setup else (", no setup" if no_setup and item["setup"] else "")) + f"; line total ${total:,.2f}"
    return total, work


UNIT_WORDS = dict(LENGTH, **{w: "box" for w in "box boxes bx bxs case cases pack packs pk pkg carton cartons bag bags".split()},
                  **{w: "piece" for w in "pc pcs piece pieces ea each".split()},
                  **{w: "reel" for w in "reel reels coil coils spool spools roll rolls".split()},
                  **{w: "unit" for w in "stick sticks length lengths".split()})


def said_unit(text, qty):
    """The unit written right after the quantity in the request: '200 ft' -> 'ft', "75'" -> 'ft', '2 boxes' -> 'box'."""
    words = "|".join(sorted(map(re.escape, UNIT_WORDS), key=len, reverse=True))
    n = f"{qty:g}" if isinstance(qty, float) else str(qty)
    for m in re.finditer(rf"(?<![\w./-]){re.escape(n)}\s*-?\s*({words})(?![a-z0-9])", text, re.I):
        return UNIT_WORDS[m.group(1).lower()]
    return None


def to_unit(pricing, sku, qty, text, unit_hint=None):
    """Put the quantity in the item's own unit (feet, sticks, boxes). Returns (qty, note) or (None, why to ask).
    text is the request as the customer wrote it (before synonyms). Ambiguous or non-whole conversions are asked, never rounded."""
    item = pricing["skus"].get(sku.upper())
    if not item or not item.get("unit") or qty <= 0:
        return qty, ""
    said = said_unit(text, qty)
    hint = UNIT_WORDS.get(str(unit_hint or "").lower().strip("."))
    if not said and hint in ("ft", "m", "reel", "piece") and any(UNIT_WORDS.get(w) == hint for w in re.findall(r"[a-z]+|'", text.lower())):
        said = hint  # the model's unit, only when the request uses that unit somewhere (never 'box' from a product name)
    nums = {int(x) for x in re.findall(r"(?<![\w.])(\d{1,6})(?![\w.%])", text)} | {int(x) for x in re.findall(r"(?<![\w.])(\d{1,6})(?=\s*(?:ft|feet|')|')", text)}
    if item["unit"] in ("ft", "m"):
        if said in (None, item["unit"]):
            return qty, ""
        if said == "reel" and item.get("full"):
            return qty * item["full"], f"{qty} full reel/coil = {qty * item['full']} {item['unit']}"
        return None, f"{sku} is sold per {item['unit']}; the request says {qty} {said}: ask the customer for the length in {item['unit']}"
    if item.get("pack"):
        n = item["pack"]
        if said == "box":
            return qty, ""
        if said is None and re.sub(r"[^A-Z0-9]", "", sku.upper()) in re.sub(r"[^A-Z0-9]", "", text.upper()):
            return qty, ""  # "Price 4 of WN-YL-100": the code names the box item, the count is boxes
        if said is None and qty * n in nums and qty not in nums:
            return qty, f"{qty * n} pieces = {qty} box{'es' if qty > 1 else ''} of {n}"  # already converted
        if said in (None, "piece") and qty % n == 0:
            return qty // n, f"{qty} pieces = {qty // n} box{'es' if qty // n > 1 else ''} of {n}"
        return None, f"{sku} is sold by the box of {n} only; {qty} {'pieces' if said == 'piece' else ''} is not a whole number of boxes, or it is unclear whether {qty} means pieces or boxes: ask the customer".replace("  ", " ")
    if item.get("per"):
        per, pu = item["per"]
        if said == pu:
            if (qty / per).is_integer():
                return int(qty / per), f"{qty} {pu} = {int(qty / per)} x {per:g} {pu} {item['unit']}"
            return None, f"{sku} is sold by the {per:g} {pu} {item['unit']} only; {qty} {pu} is not whole {item['unit']}s: ask the customer"
        if said is None and qty * per in nums and qty not in nums:
            return qty, f"{qty * per:g} {pu} = {qty} x {per:g} {pu} {item['unit']}"
        return qty, ""
    if said == "box" and item["unit"] in ("ea", "each"):
        return None, f"{sku} is sold each; the request says {qty} box{'es' if qty > 1 else ''}: ask the customer how many pieces"
    return qty, ""


def expand_synonyms(pricing, text):
    """Rewrite the shop's own shorthand (the synonyms note) into price-book words, longest phrase first, in one pass
    (a replacement is never rewritten again). Separators are loose: '12-2 nm' also matches '12/2 nm' and '12 2 NM'."""
    pats, means = [], []
    for key, m in pricing.get("synonyms", []):
        toks = [re.escape(t) for t in re.split(r"[\s/-]+", key.strip()) if t]
        if toks:
            pats.append("[\\s/-]*".join(toks) + "s?")
            means.append(m)
    if not pats:
        return text
    rx = re.compile(r"(?<![\w/-])(?:" + "|".join(f"({p})" for p in pats) + r")(?![\w/-])", re.I)
    def sub(m):
        mean = means[m.lastindex - 1]
        around = text[max(0, m.start() - len(mean)): m.end() + len(mean)].lower()
        return m.group(0) if mean.lower() in around else mean  # "plug-on breakers" already says it
    return rx.sub(sub, text)


LEVEL_NEAR = r"(?:account|acct|level|price|pricing|rate|tier|customer)s?"


def account_level(pricing, text):
    """The price level the request names ('contractor account', 'at contractor level') or the level of a customer
    named in the request (a note with `price_level:`). None means list, and the answer says so."""
    t = text.lower()
    for name in sorted(pricing.get("levels", {}), key=len, reverse=True):
        n = re.escape(name)
        if re.search(rf"\b{n}\b\W+(?:\w+\W+){{0,2}}?{LEVEL_NEAR}\b|\b{LEVEL_NEAR}\W+(?:\w+\W+){{0,2}}?{n}\b", t):
            return name
    for cust, lvl in pricing.get("customers", {}).items():
        if re.search(rf"\b{re.escape(cust)}\b", t):
            return lvl
    return None


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
    if pricing["skus"].get(sku, {}).get("unit") in ("ft", "m"):  # "1000ft #12": a length written with its unit is the quantity
        nums += [int(n) for n in re.findall(r"(?<![\w.-])(\d{1,6})(?=\s*(?:FT|FEET|FOOT|M|METERS?|METRES?)\b|')", text)]
    nums = list(dict.fromkeys(nums))
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
        w = re.sub(r"(?<=[a-z]{3})s$", "", w) if len(w) > 4 else w  # "docks" -> "dock", but "ups" stays
        w = re.sub(r"(\d|\din)s$", r"\1", w)  # "24x30s" -> "24x30", "16ins" -> "16in"
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


NO_SETUP = re.compile(r"no setup|without setup|hardware only|just the hardware|(?:we|we'll|we will|ourselves)[^.]{0,40}(?:image|set (?:them|it) up|plug|install)|ourselves", re.I)


def says_no_setup(text):
    return bool(NO_SETUP.search(text))


SPEC = re.compile(r"\b(\d+)\s*[x×]\s*(\d+)\b|\b(\d+(?:\.\d+)?)\s*(?:-\s*)?(in|inch|inches|\"|ft|foot|feet|'|port|va)\b", re.I)
UNIT = {"in": "in", "inch": "in", "inches": "in", '"': "in", "ft": "ft", "foot": "ft", "feet": "ft", "'": "ft", "port": "port", "va": "va"}


def _specs(s):
    """[(unit, value, start, end)] for sizes (15x30), lengths (10ft), screens (27in), ports (48-port) and VA (1000VA)."""
    out = []
    for m in SPEC.finditer(s):
        if m.group(1):
            out.append(("size", f"{int(m.group(1))}x{int(m.group(2))}", m.start(), m.end()))
        else:
            out.append((UNIT[m.group(4).lower()], f"{float(m.group(3)):g}", m.start(), m.end()))
    return out


def unstocked(pricing, text):
    """Spec'd items the request asks for that are not stocked in that spec, e.g. '1000VA battery backup' when only
    a 1500VA one is on the price list. Returns [(what they asked, [stocked descriptions of that item])].
    The nearest item word in the same sentence names the item; the item counts only if every SKU sharing those words
    is listed with a spec of the same unit. A nearby stocked item is never substituted: the caller flags it instead."""
    fam = {}
    for k, v in pricing["skus"].items():
        specs = {(u, val) for u, val, _, _ in _specs(v["desc"])}
        if v.get("unit") in ("ft", "m") or v.get("per"):  # "500 ft reel", "10 ft stick" is the package, not a spec:
            specs = {(u, val) for u, val in specs if u not in ("ft", "m")}  # "100 ft of THHN" is a quantity
        words = _tokens(SPEC.sub(" ", v["desc"])) - {"business", "small", "poe"}
        fam[k] = (words, specs, v["desc"])
    found = []
    for sent in re.split(r"(?<=[.?!])\s+|\n+", words_to_digits(text)):
        toks = [(m.group(0), m.start(), m.end()) for m in re.finditer(r"[A-Za-z][A-Za-z-]*", sent)]
        for unit, val, s0, s1 in _specs(sent):
            near = [t for t in toks if t[2] <= s0][-3:] + [t for t in toks if t[1] >= s1][:3]  # 3 words each side
            words = set()
            for w, _, _ in near:
                words |= _tokens(w)
            skus = [k for k, (fw, sp, _) in fam.items() if fw and fw & words and any(u == unit for u, _ in sp)]
            if not skus:
                continue
            best = max(len(fam[k][0] & words) for k in skus)
            skus = [k for k in skus if len(fam[k][0] & words) == best]
            if any((unit, val) in fam[k][1] for k in skus):
                continue
            after = re.match(r"\s*([A-Za-z-]+(?:\s+[A-Za-z-]+)?)", sent[s1:])
            found.append(((sent[s0:s1] + (" " + after.group(1) if after else "")).strip(),
                          [fam[k][2] for k in skus if pricing["skus"][k].get("stock", True)]))
    return found


SKIP_IF_NOT = re.compile(r"\bif not\b,?\s*(?:then\s*)?(?:just\s*)?(?:quote|price)|\botherwise,?\s*(?:just\s*)?(?:quote|price)", re.I)


def says_skip_unstocked(text):
    """'If not, just quote the 24x30s': the customer said to price what is stocked and leave the rest out."""
    return bool(SKIP_IF_NOT.search(text))


def supported(pricing, text, sku):
    """True when the request names something that identifies this SKU: its code, or a description word no other
    item shares. 'laptops' alone does not pick between two laptops, so the model's choice is not accepted."""
    t = re.sub(r"(\d+)\s*(?:in\b|inch\b|\")", r"\1in", text, flags=re.I)
    flat = re.sub(r"[^A-Z0-9]", "", t.upper())
    if re.sub(r"[^A-Z0-9]", "", sku.upper()) in flat:
        return True
    descs = {k: _tokens(v["desc"]) for k, v in pricing["skus"].items()}
    df = {}
    for d in descs.values():
        for w in d:
            df[w] = df.get(w, 0) + 1
    mine, said = descs.get(sku, set()), _tokens(t)
    unique = {w for w in mine if df[w] == 1}
    if bool(unique & said) or (bool(mine) and mine <= said):  # a unique word, or the whole description
        return True
    hit = mine & said  # or the words said, together, fit this item and no other ("thhn 12 black")
    return len(hit) >= 2 and not any(hit <= d for k, d in descs.items() if k != sku)
