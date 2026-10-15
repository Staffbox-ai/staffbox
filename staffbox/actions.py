"""Actions: deterministic tools the worker calls instead of doing the work in its head.

quote  prices one line from the vault's own pricing notes (any note tagged `pricing`):
       a table with a SKU column and a price column (optional setup-fee column),
       optional option-surcharge tables (first column = option name, second = "N%"),
       and a quantity-break table (quantity ranges -> "N%" or "none").
The model only reads the request (SKU, quantity, options); the arithmetic and every lookup are code.

The pricing pipeline (one explicit rule order, rounded to the cent after every step):
  0 goods      quantity (in the item's own unit) x list price (+ option surcharges on the unit price)
  1 break      quantity break from the break table, counted in the item's own unit. Skipped for the units and SKU
               prefixes a note says get "no quantity break" ("items priced by the foot or by the pound", "(WH-)").
               A break table whose header names a unit ("Feet on the line") applies to that unit only.
  2 level      account price level, only when the request or a customer note (frontmatter `price_level:`) names it;
               otherwise list, and the answer says so
  3 surcharge  dated group surcharges: a table with a Surcharge column and an Effective column; the row in effect on
               the request date is used. "N%" is a percent of the line, "$X" with "per <unit>" is per unit sold
               (applies only to items sold in that unit)
  4 cut        cut charge and minimum cut for items sold by length and cut from a reel, coil or stick
  then setup fees (never discounted).
The order of steps 1-4 is read from the vault: sentences such as "after the quantity break and before the surcharge",
"added after the price level" or "get the break first, then their price level" become constraints; the default
order above breaks ties, and notes that contradict each other stop the quote (ask who owns pricing).

Trade price books (all optional, all read from the vault, nothing trade-specific in code):
  Unit column     ea; a measure (ft or m by length, lb or kg by weight); "box/bag/case of N" (packs); or a unit like
                  "stick" whose description says "10 ft stick". Requests in another unit are converted (pieces -> packs,
                  feet -> sticks, reels or cylinders -> feet or pounds) only when the conversion is whole; otherwise ask.
  Full packages   the description's "500 ft reel", "20 ft stick", "25 lb cylinder" is the full package. A sentence
                  "sold by the whole coil only" / "full cylinder only" / "never cut" makes that package whole-only:
                  a quantity that is not whole packages is asked, never priced.
  Stock column    anything but "stocked"/"yes" (e.g. "special order") is never priced: decline and ask.
  Cuts            "minimum cut: N ft" and "cut charge: $X per cut" (or "cut charge $X under N ft") from any pricing
                  note or the row's notes cell. "no cut charge" bullets exempt the group they name.
  Price levels    "**Contractor level**: 12% off list" bullets (or a Level | Discount table).
  Kits            a table whose first column and at least two other columns are all price-book SKUs (e.g.
                  System | Part A | Part B) lists matched sets. A request with every part of one row is priced as
                  that row; parts from two or more columns that are not on one row are declined (ask the note's owner).
  Synonyms        a note named `synonyms` (or tagged synonyms): | customers write | we mean | rows, applied to the request first.
"""
import datetime
import re
from . import brain

PCT = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*$")
STEPS = ("break", "level", "surcharge", "cut")  # the default rule order; notes may reorder it (rule_order)


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
WEIGHT = {"lb": "lb", "lbs": "lb", "pound": "lb", "pounds": "lb", "#": "lb", "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg"}
MEASURE = dict(LENGTH, **WEIGHT)
CONTAINERS = "reel|coil|spool|roll|stick|length|cylinder|jug|drum|pail|tote"
MONTHS = {m: i for i, m in enumerate("january february march april may june july august september october november december".split(), 1)}
IN_STOCK = {"stocked", "stock", "yes", "y", "in stock", "stock item"}


def by_measure(item):
    """True when the item is priced per foot, metre, pound or kilo (its quantity is a measure, not a count)."""
    return (item or {}).get("unit") in MEASURE.values()


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


FILLER = {"before", "after", "that", "this", "then", "earlier", "previous", "rate", "old", "new", "and", "or"}


def _group(label):
    """'copper wire and cable (THHN, NM-B, MC)' -> ({'THHN','NM-B','MC'}, [{'copper','wire','cable'}]): bracketed terms
    name the members; with no brackets each comma-separated part ('X-1, X-2') is one alternative whose every word must be
    in the item description. Parts that only date the row ('..., before that') are not alternatives."""
    terms = {t.strip().upper() for b in re.findall(r"\(([^)]*)\)", label) for t in b.split(",") if t.strip()}
    parts = [_tokens(p) - {"and", "or"} for p in re.sub(r"\([^)]*\)", " ", label).split(",")]
    alts = [p for p in parts if p and not p <= FILLER]
    return terms, (alts[:1] if terms else alts)


def in_group(group, sku, desc):
    terms, alts = group
    hay = f"{sku} {desc}".upper()
    if terms:
        return any(re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", hay) for t in terms)
    d = _tokens(desc)
    return any(a <= d for a in alts)


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
    if not unit and (m := re.search(r"(?:/|per\s+)(ft|foot|m|meter|metre|lb|pound|kg)\b", r[i_price], re.I)):
        unit = m.group(1).lower()  # "$0.38/ft"
    item = dict(desc=r[i_desc] if i_desc is not None else "", price=_money(r[i_price]),
                setup=_money(r[i_setup]) if i_setup is not None else 0.0, unit=MEASURE.get(unit, unit) or None,
                pack=None, per=None, full=None, container=None, stock=True, stock_label="")
    if m := re.search(r"\b(?:box|pack|case|bag|carton|pkg|package)\s+of\s+(\d+)", unit if i_unit is not None else row, re.I):
        item["pack"] = int(m.group(1))
        item["unit"] = item["unit"] or f"pack of {item['pack']}"
    elif by_measure(item):  # "500 ft reel", "20 ft stick", "25 lb cylinder": the full package
        words = [k for k, v in MEASURE.items() if v == item["unit"] and k not in ("'", "#")]
        if m := re.search(rf"(\d+)\s*(?:{'|'.join(words)})\.?\s+({CONTAINERS})s?\b", row, re.I):
            item["full"], item["container"] = int(m.group(1)), m.group(2).lower()
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


def _sentences(body):
    """Plain sentences of a note: no bold marks, no [[links]] (a link's name is not part of what the sentence says)."""
    t = re.sub(r"\[\[[^\]]*\]\]", " ", body.replace("*", ""))
    return [s.strip() for ln in t.splitlines() if not ln.strip().startswith("|") for s in re.split(r"(?<=[.;])\s+", ln) if s.strip()]


STEP_WORDS = {"break": r"\b(?:quantity|volume)\s+(?:break|discount)s?\b|\bthe break\b",
              "level": r"\blevels?\b",
              "surcharge": r"\bsurcharges?\b",
              "cut": r"\bcut charges?\b"}


def _hits(text, words):
    return sorted((m.start(), k) for k, rx in words.items() for m in re.finditer(rx, text, re.I))


def _step_in(text, last=False, words=STEP_WORDS):
    """The rule step a piece of text names: the first one (or the last one) mentioned."""
    hits = _hits(text, words)
    return (hits[-1] if last else hits[0])[1] if hits else None


def _steps_in(text, words=STEP_WORDS):
    return list(dict.fromkeys(k for _, k in _hits(text, words)))


def order_constraints(name, body, surcharge_names=()):
    """Rule-order sentences in one note -> [(earlier step, later step, the sentence)].
    'X ... after A and before B' -> A<X, X<B ('X' defaults to the note's own topic: a note named price-levels talks about
    the level); 'A first, then B' -> A<B."""
    """surcharge_names: what this vault calls its surcharge notes ('levy', 'copper surcharge'): the note names say it."""
    words = dict(STEP_WORDS)
    if surcharge_names:
        words["surcharge"] += "|" + "|".join(rf"\b{re.escape(s)}\b" for s in surcharge_names)
    topic = "surcharge" if name.replace("-", " ").lower() in surcharge_names else next(
        (k for k, w in (("level", "level"), ("surcharge", "surcharge"), ("break", "break"), ("break", "discount"),
                        ("cut", "cut")) if w in name.lower()), None)
    out = []
    for s in _sentences(body):
        if m := re.search(r"(.*)\bfirst\b,?\s*(?:and\s+)?then\b(.*)", s, re.I):
            a, b = _step_in(m.group(1), True, words), _step_in(m.group(2), False, words)
            if a and b and a != b:
                out.append((a, b, s))
            continue
        m = re.search(r"\b(after|before)\b", s, re.I)
        if not m:
            continue
        subject = _step_in(s[:m.start()], False, words) or topic
        if not subject:
            continue
        rest = s[m.start():]
        for part in re.split(r"(?=\b(?:after|before)\b)", rest, flags=re.I):
            word = part.split()[0].lower() if part.split() else ""
            for k in _steps_in(part, words):
                if k != subject:
                    out.append((k, subject, s) if word == "after" else (subject, k, s))
    return out


def rule_order(constraints):
    """The steps in an order every constraint allows, ties broken by STEPS. Returns (order, None) or (None, conflict)."""
    order, left = [], list(STEPS)
    while left:
        free = [s for s in left if not any(b == s and a in left for a, b, _ in constraints)]
        if not free:
            bad = [c[2] for c in constraints if c[0] in left and c[1] in left]
            return None, "; ".join(dict.fromkeys(bad))
        order.append(free[0])
        left.remove(free[0])
    return order, None


def _no_break(body):
    """'No quantity break on: items priced by the foot or by the pound; equipment (WH-), (AC-)' and 'sold by the foot get
    no quantity break' -> (units, SKU prefixes)."""
    units, prefixes = set(), set()
    t = re.sub(r"\[\[[^\]]*\]\]", " ", body.replace("*", ""))
    for m in re.finditer(r"\bno\s+(?:quantity|volume)\s+(?:break|discount)s?\b", t, re.I):
        a = max(t.rfind("\n", 0, m.start()), t.rfind(". ", 0, m.start())) + 1
        if re.match(r"\s*on\s*:", t[m.end():]):  # a list follows: up to the next blank line
            e = t.find("\n\n", m.end())
        else:
            e = min([i for i in (t.find("\n", m.end()), t.find(". ", m.end())) if i >= 0] or [len(t)])
        span = t[a: e if e >= 0 else len(t)]
        for w in re.findall(r"\b(?:by the|per|priced by|sold by)\s+(?:the\s+)?([a-z]+)", span, re.I):
            if w.lower() in MEASURE:
                units.add(MEASURE[w.lower()])
        prefixes |= set(re.findall(r"\(([A-Z][A-Z0-9]{0,5}-)\)", span))
    return units, prefixes


def _whole_only(body):
    """Packages a note says are sold whole only: 'sold by the whole coil only', 'full cylinder only', 'whole 10 ft sticks
    only', or 'never cut' with a package named in the same sentence."""
    out = set()
    for s in _sentences(body):
        for m in re.finditer(rf"\b(?:whole|full)\s+(?:\d+\s*[a-z]+\.?\s+)?({CONTAINERS})s?\s+only\b", s, re.I):
            out.add(m.group(1).lower())
        if re.search(r"\bnever cut\b", s, re.I):
            out |= {w.lower() for w in re.findall(rf"\b({CONTAINERS})s?\b", s, re.I)}
    return out


def _surcharge_value(cell, head):
    """'8%' -> ('pct', 0.08); '$3.25' under 'Surcharge per lb' -> ('per', 3.25, 'lb'); 'none' -> ('pct', 0.0);
    anything else (e.g. 'priced by the sales lead') -> None: not a stated amount."""
    if m := re.search(r"(\d+(?:\.\d+)?)\s*%", cell):
        return ("pct", float(m.group(1)) / 100)
    if m := re.search(r"\$\s*([0-9][0-9,]*(?:\.\d+)?)", cell):
        u = re.search(r"\bper\s+([a-z]+)", f"{cell} {head}", re.I)
        return ("per", float(m.group(1).replace(",", "")), MEASURE.get(u.group(1).lower(), u.group(1).lower()) if u else None)
    if re.fullmatch(r"\s*(?:none|0|-|n/a|no surcharge)?\s*", cell, re.I):
        return ("pct", 0.0)
    return None


def _is_group_table(h):
    """A dated or grouped surcharge table: a Surcharge column (not first) and a group or Effective column."""
    return (any("surcharge" in c for c in h[1:]) and "sku" not in h
            and bool(re.search(r"group|product|applies to", h[0]) or any("effective" in c or "dates" in c for c in h)))


def load_pricing(vault, today=None):
    skus, surcharges, tiers, unit_tiers, groups, levels, customers, synonyms = {}, {}, [], {}, [], {}, {}, []
    cut, cut_exempt, no_break_units, no_break_prefixes, whole_only = {}, [], set(), set(), set()
    constraints, kit_tables, default_packages = [], [], []
    today = today or datetime.date.today()
    notes, _ = brain.load(vault)
    surcharge_names = {n.name.replace("-", " ").lower() for n in notes.values() if any(_is_group_table([c.lower() for c in h])
                       for h, _ in _tables(n.body))}  # what this vault calls its surcharge ("levy" is a surcharge step)
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
            continue
        if "pricing" not in tags:
            continue
        is_levels = "level" in n.name.lower() or any("level" in a.lower() for a in brain._aslist(n.meta.get("aliases")))
        levels.update(_levels(n.body, is_levels))
        cut.update(_cut_rule(n.body))
        constraints += [(a, b, f"{n.name}: {s}") for a, b, s in order_constraints(n.name, n.body, surcharge_names)]
        u, p = _no_break(n.body)
        no_break_units |= u
        no_break_prefixes |= p
        whole_only |= _whole_only(n.body)
        default_packages += _default_packages(n.body)
        for m in re.finditer(r"(?m)^\s*[-*]\s*([^:\n]+):[^\n]*\bno cut charge\b", n.body.replace("*", "")):
            cut_exempt.append(_group(m.group(1)))
        for head, rows in _tables(n.body):
            h = [c.lower() for c in head]
            if "sku" in h and any("price" in c for c in h):
                i_sku = h.index("sku")
                for r in rows:
                    skus[r[i_sku].upper()] = _row_item(head, r)
            elif _is_group_table(h):
                i_pct = next(i for i, c in enumerate(h) if "surcharge" in c)
                i_eff = next((i for i, c in enumerate(h) if "effective" in c or "dates" in c), None)
                key = lambda label: re.split(r"[,(]", label)[0].strip().lower()
                terms = {}  # rows naming the same group ("copper wire and cable, before that") share its bracketed terms
                for r in rows:
                    terms.setdefault(key(r[0]), set()).update(_group(r[0])[0])
                for r in rows:
                    d = _dates(r[i_eff]) if i_eff is not None else []
                    groups.append(dict(group=(terms[key(r[0])], _group(r[0])[1]), value=_surcharge_value(r[i_pct], head[i_pct]),
                                       label=r[0], start=d[0] if d else None, end=d[1] if len(d) > 1 else None,
                                       note=n.name.replace("-", " ")))
            elif any("level" in c for c in h) and len(h) >= 2:
                for r in rows:
                    if m := re.search(r"(\d+(?:\.\d+)?)\s*%", " ".join(r[1:])):
                        levels[re.sub(r"\b(level|price|pricing|account)s?\b", " ", r[0].lower()).strip()] = float(m.group(1)) / 100
            elif len(h) == 2 and any(_range(r[0]) for r in rows) and "discount" in h[1]:
                scope = next((MEASURE[w] for w in re.findall(r"[a-z]+", h[0]) if w in MEASURE), None)
                for r in rows:
                    rg = _range(r[0])
                    if rg:
                        m = PCT.match(r[1])
                        t = (rg[0], rg[1], float(m.group(1)) / 100 if m else 0.0)
                        (unit_tiers.setdefault(scope, []) if scope else tiers).append(t)
            elif len(h) == 2 and rows and all(PCT.match(r[1]) for r in rows):
                surcharges[h[0].lower()] = {r[0].lower(): float(PCT.match(r[1]).group(1)) / 100 for r in rows}
            elif len(h) >= 3:
                kit_tables.append((head, rows, n.meta.get("owner") or "the person who owns pricing"))
    kits = []
    for head, rows, owner in kit_tables:  # matched sets: first column and 2+ other columns are all price-book SKUs
        cols = [i for i in range(len(head)) if rows and all(r[i].upper() in skus for r in rows)]
        if 0 in cols and len(cols) >= 3:
            kits += [dict(sku=r[0].upper(), parts={head[i]: r[i].upper() for i in cols[1:]}, owner=owner) for r in rows]
    if levels and "list" not in levels:
        levels["list"] = 0.0
    order, conflict = rule_order(constraints)
    return dict(skus=skus, surcharges=surcharges, tiers=tiers, unit_tiers=unit_tiers, groups=groups, levels=levels,
                customers=customers, synonyms=sorted(synonyms, key=lambda kv: -len(kv[0])), cut=cut, cut_exempt=cut_exempt,
                no_break_units=no_break_units, no_break_prefixes=no_break_prefixes, whole_only=whole_only, kits=kits,
                order=order, order_conflict=conflict, constraints=constraints, today=today,
                default_packages=default_packages)


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


class Ask(Exception):
    """A step that cannot price the line: the message says what to ask."""


def _step_break(p, c):
    item, sku, qty, u = c["item"], c["sku"], c["qty"], c["item"].get("unit")
    tiers = p.get("unit_tiers", {}).get(u)
    why = None
    if tiers is None:
        if by_measure(item) and u in p.get("no_break_units", ()):
            why = f"no quantity break (sold per {u})"
        elif pre := next((x for x in sorted(p.get("no_break_prefixes", ())) if sku.startswith(x)), None):
            why = f"no quantity break on {pre} items"
        else:
            tiers = p["tiers"]
    if why:
        return why if p["tiers"] else None
    d = next((d for lo, hi, d in tiers or [] if lo <= qty <= hi), 0.0)
    if d:
        c["goods"] = round(c["goods"] * (1 - d), 2)
        return f"less {d * 100:g}% quantity break = ${c['goods']:,.2f}"
    return None


def _step_level(p, c):
    if not p.get("levels"):
        return None
    name = (c["level"] or "list").lower()
    if name not in p["levels"]:
        raise Ask(f"price level '{name}' is not in the price book (levels: {', '.join(p['levels'])}): ask who owns pricing")
    lp = p["levels"][name]
    if lp:
        c["goods"] = round(c["goods"] * (1 - lp), 2)
        return f"{name} level -{lp * 100:g}% = ${c['goods']:,.2f}"
    return "list price" + ("" if c["level"] else " (no account level named)")


def _step_surcharge(p, c):
    on, item, sku = c["on"], c["item"], c["sku"]
    rows = [g for g in p.get("groups", []) if (g["start"] is None or g["start"] <= on) and (g["end"] is None or on <= g["end"])
            and in_group(g["group"], sku, item["desc"])]
    rows = [g for g in rows if not (g["value"] and g["value"][0] == "per" and g["value"][2] and g["value"][2] != item.get("unit"))]
    if not rows:
        return None
    if any(g["value"] is None for g in rows):
        raise Ask(f"the surcharge for {sku} ({rows[0]['label']}) is not a stated amount: ask who owns pricing")
    if len({g["value"] for g in rows}) > 1:
        raise Ask(f"{sku} matches more than one surcharge row ({'; '.join(sorted(g['label'] for g in rows))}): ask who owns pricing")
    g, v = rows[0], rows[0]["value"]
    name = re.split(r"[,(]", g["label"])[0].strip()
    when = f" (rate on {on.day} {on:%b %Y})" if g["start"] or g["end"] else ""
    if v[0] == "pct":
        if not v[1]:
            return None
        c["goods"] = round(c["goods"] * (1 + v[1]), 2)
        return f"plus {g['note']} {v[1] * 100:g}% on {name}{when} = ${c['goods']:,.2f}"
    amt = round(c["qty"] * v[1], 2)
    c["goods"] = round(c["goods"] + amt, 2)
    return f"plus {g['note']} on {name} {c['qty']:g} {item.get('unit') or 'x'} x ${v[1]:,.2f} = ${amt:,.2f}{when} = ${c['goods']:,.2f}"


def _step_cut(p, c):
    item, sku, qty = c["item"], c["sku"], c["qty"]
    if item.get("unit") not in LENGTH.values():
        return None
    rule = item.get("cut") or p.get("cut") or {}
    if not rule or any(in_group(g, sku, item["desc"]) for g in p.get("cut_exempt", [])):
        return None
    full, u = item.get("full"), item["unit"]
    rem = qty % full if full else qty
    if rem and rule.get("min") and rem < rule["min"]:
        raise Ask(f"{qty:g} {u} of {sku} needs a {rem:g} {u} cut, under the {rule['min']} {u} minimum cut: ask the customer")
    if rule.get("charge") and (qty < rule["under"] if rule.get("under") else rem):
        c["goods"] = round(c["goods"] + rule["charge"], 2)
        what = f"{rem:g} {u} cut from a {full} {u} {item.get('container') or 'length'}" if full and not rule.get("under") else "cut"
        return f"plus cut charge ${rule['charge']:,.2f} ({what}) = ${c['goods']:,.2f}"
    return None


STEP_FN = {"break": _step_break, "level": _step_level, "surcharge": _step_surcharge, "cut": _step_cut}


def quote(pricing, sku, qty, options=None, level=None, on=None):
    """Price one line. qty is in the item's own unit (see to_unit). Returns (total or None, one-line working).
    The steps run in pricing['order'] (read from the notes); each step that changes the price says so in the working."""
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
    if pricing.get("order_conflict"):
        return None, f"the pricing notes give conflicting rule orders ({pricing['order_conflict']}): ask who owns pricing"
    full, cont = item.get("full"), item.get("container")
    if full and cont in pricing.get("whole_only", ()) and qty % full:
        return None, (f"{sku} is sold by the whole {full} {item['unit']} {cont} only; {qty:g} {item['unit']} is not a whole "
                      f"number of {cont}s: ask the customer")
    pct, used = 0.0, []
    for attr, table in pricing["surcharges"].items():
        val = options.get(attr) or options.get(attr.rstrip("s"))
        if val is None:  # never assume the cheapest option: an unstated or unknown option is not priced
            return None, f"{attr} not stated or not offered (offered: {', '.join(table)}): ask which, or it is custom"
        if val not in table:
            return None, f"{attr} '{val}' is not offered (options: {', '.join(table)}): custom, not priced here"
        pct += table[val]
        used.append(f"{val} +{table[val]:.0%}")
    measure = by_measure(item)
    u = f" {item['unit']}" if measure else ""
    unit = round(item["price"] * (1 + pct), 2)
    c = dict(item=item, sku=sku.upper(), qty=qty, level=level, on=on or pricing.get("today") or datetime.date.today(),
             goods=round(unit * qty, 2))
    work = f"{qty:g}{u} x {sku} at ${unit:,.2f}" + (f"/{item['unit']}" if measure else "") + (f" ({', '.join(used)})" if used else "")
    work += f" = ${c['goods']:,.2f}"
    for step in pricing.get("order") or STEPS:
        try:
            said = STEP_FN[step](pricing, c)
        except Ask as e:
            return None, str(e)
        if said:
            work += f", {said}"
    goods = c["goods"]
    setup = 0.0 if no_setup else round(qty * item["setup"], 2)
    total = round(goods + setup, 2)
    work += (f", plus setup {qty} x ${item['setup']:,.2f} = ${setup:,.2f}" if setup else (", no setup" if no_setup and item["setup"] else "")) + f"; line total ${total:,.2f}"
    return total, work


def match_kits(pricing, lines):
    """lines: [(sku, qty, options)]. Every part of one kit row on the request -> that row (same quantity each).
    Parts from two or more kit columns that are not on one row -> an Ask naming the note's owner.
    Returns (lines, notes for the working)."""
    kits = pricing.get("kits") or []
    if not kits:
        return lines, []
    role = {s: col for k in kits for col, s in k["parts"].items()}
    pre = {}
    for k in kits:
        for col, s in k["parts"].items():
            pre.setdefault(col, set()).add(re.match(r"[A-Z0-9]*-?", s).group(0))
    for s, _, _ in lines:  # a column whose parts share one prefix ("AC-") names the role of any item with that prefix
        for col, ps in pre.items():
            if s not in role and len(ps) == 1 and next(iter(ps)).endswith("-") and s.startswith(next(iter(ps))):
                role[s] = col
    out, notes, used = list(lines), [], set()
    for k in kits:
        idx = {}
        for i, (s, q, o) in enumerate(out):
            if i not in used and s in k["parts"].values() and s not in idx:
                idx[s] = i
        if len(idx) == len(k["parts"]):
            qs = {out[i][1] for i in idx.values()}
            if len(qs) != 1:
                raise Ask(f"the request has {' and '.join(sorted(idx))} in different quantities: ask the customer how many "
                          f"{k['sku']} sets")
            first = min(idx.values())
            out[first] = (k["sku"], qs.pop(), out[first][2])
            used |= set(idx.values()) - {first}
            notes.append(f"{' + '.join(k['parts'].values())} = {k['sku']} (one row of the matched-set table)")
    out = [l for i, l in enumerate(out) if i not in used]
    left = [s for s, _, _ in out if s in role]
    if len({role[s] for s in left}) > 1:
        roles = {role[s] for s in left}
        owner = next((k["owner"] for k in kits if roles & set(k["parts"])), kits[0]["owner"])
        raise Ask(f"{' + '.join(left)} are not a listed matched set (no single row has them together): not priced; "
                  f"ask the {owner}")
    return out, notes


UNIT_WORDS = dict(MEASURE, **{w: "box" for w in "box boxes bx bxs case cases pack packs pk pkg carton cartons bag bags".split()},
                  **{w: "piece" for w in "pc pcs piece pieces ea each".split()},
                  **{w: "reel" for w in "reel reels coil coils spool spools roll rolls cylinder cylinders jug jugs drum drums pail pails tote totes".split()},
                  **{w: "unit" for w in "stick sticks length lengths".split()})


def said_unit(text, qty):
    """The unit written right after the quantity in the request: '200 ft' -> 'ft', "75'" -> 'ft', '50#' -> 'lb',
    '2 boxes' -> 'box', '2 jugs' -> 'reel' (a full package)."""
    words = "|".join(sorted(map(re.escape, UNIT_WORDS), key=len, reverse=True))
    n = f"{qty:g}" if isinstance(qty, float) else str(qty)
    for m in re.finditer(rf"(?<![\w./-]){re.escape(n)}\s*-?\s*({words})(?![a-z0-9])", text, re.I):
        return UNIT_WORDS[m.group(1).lower()]
    if n == "1" and (m := re.search(rf"\b(?:a|an|one)\s+({words})(?![a-z0-9])", text, re.I)):
        return UNIT_WORDS[m.group(1).lower()]  # "a bag of ...", "one coil"
    return None


def _plural(word, k):
    return word if k == 1 else (word + "es" if word.endswith(("x", "s")) else word + "s")


def to_unit(pricing, sku, qty, text, unit_hint=None, context=""):
    """Put the quantity in the item's own unit (feet, pounds, sticks, packs). Returns (qty, note) or (None, why to ask).
    text is the request as the customer wrote it (before synonyms). Ambiguous or non-whole conversions are asked, never rounded."""
    item = pricing["skus"].get(sku.upper())
    if not item or not item.get("unit") or qty <= 0:
        return qty, ""
    said = said_unit(text, qty)
    hint = UNIT_WORDS.get(str(unit_hint or "").lower().strip("."))
    if not said and hint in ("ft", "m", "lb", "kg", "reel", "piece") and any(UNIT_WORDS.get(w) == hint for w in re.findall(r"[a-z]+|'|#", f"{text} {context}".lower())):
        said = hint  # the model's unit, only when the request uses that unit somewhere (never 'box' from a product name)
    nums = {int(x) for x in re.findall(r"(?<![\w./])(\d{1,6})(?![\w.%/])", text)} | {int(x) for x in re.findall(r"(?<![\w.])(\d{1,6})(?=\s*(?:ft|feet|lbs?|')|'|#)", text)}
    if by_measure(item):
        u, full, cont = item["unit"], item.get("full"), item.get("container") or "package"
        if full and qty == full and said in (None, u) and (m := re.search(rf"(?<![\d./]){full}\b[^,;+&]*?\bx\s*(\d+)\b", text, re.I)):
            k = int(m.group(1))  # "pex 1/2 300 x2": the package size, then how many packages
            return k * full, f"{k} x {full} {u} {cont} = {k * full} {u}"
        if said in (None, u):
            return qty, ""
        if full and (said == "reel" or (said == "unit" and cont in ("stick", "length"))):
            return qty * full, f"{qty} x {full} {u} {cont} = {qty * full} {u}"
        return None, f"{sku} is sold per {u}; the request says {qty} {said}: ask the customer for the quantity in {u}"
    if item.get("pack"):
        n, word = item["pack"], (item["unit"] or "pack").split()[0]
        if said == "box":
            return qty, ""
        if said is None and re.sub(r"[^A-Z0-9]", "", sku.upper()) in re.sub(r"[^A-Z0-9]", "", text.upper()):
            return qty, ""  # "Price 4 of WN-YL-100": the code names the pack item, the count is packs
        if said is None and re.search(rf"\b(?:box|bag|case|pack|carton)\s+of\s+{n}\b", text, re.I) and qty * n not in nums:
            return qty, ""  # "4 of the coupling, bag of 50": the request names the pack, the count is packs
        if said is None and qty * n in nums and qty not in nums:
            return qty, f"{qty * n} pieces = {qty} {_plural(word, qty)} of {n}"  # already converted
        if said in (None, "piece") and qty % n == 0:
            return qty // n, f"{qty} pieces = {qty // n} {_plural(word, qty // n)} of {n}"
        return None, f"{sku} is sold by the {word} of {n} only; {qty} {'pieces' if said == 'piece' else ''} is not a whole number of {word}es, or it is unclear whether {qty} means pieces or {_plural(word, 2)}: ask the customer".replace("  ", " ").replace("bages", "bags").replace("casees", "cases")
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
        parts = [x.strip() for x in m.split(",") if x.strip()]
        if len(parts) > 1 and (d := re.findall(r"\d+", key)):  # "M11 | MERV 8, MERV 11 filter" -> "MERV 11 filter"
            hit = [x for x in parts if set(re.findall(r"\d+", x)) & set(d)]
            m = hit[0] if len(hit) == 1 else m
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
    text = PACKAGE.sub(" ", text)  # "10 ft stick", "500 ft reel": the package, not the quantity
    text = re.sub(r"\$\s*[0-9][0-9,]*(?:\.\d+)?", " ", text)
    nums = [int(n) for n in re.findall(r"(?<![\w./-])(\d{1,5})(?![\w.%/])", text)]  # "3/4" is a size, not a quantity
    if by_measure(pricing["skus"].get(sku)):  # "1000ft #12", "50#": a length or weight written with its unit is the quantity
        nums += [int(n) for n in re.findall(r"(?<![\w.-])(\d{1,6})(?=\s*(?:FT|FEET|FOOT|M|METERS?|METRES?|LBS?|POUNDS?|KG)\b|'|#)", text)]
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
    s = re.sub(r"\b([a-z0-9]+)-([a-z])\b", r"\1\2", s.lower())  # "pex-a" -> "pexa": a one-letter grade is not a stopword
    s = re.sub(r"(\d+)/(\d+)(?:\s*(?:in\b|inch(?:es)?\b|\"))?", r"\1f\2", s)  # "3/4in" = "3/4" = "3/4\"": one size token
    s = re.sub(r"\b(\d+)-(\d+)\b", r"\1f\2", s)  # "12-2" = "12/2"
    for w in re.findall(r"\d+\.\d+[a-z0-9]*|[a-z0-9]+", s.replace("usb-c", "usbc").replace("wi-fi", "wifi")):  # "3.5" stays one
        w = re.sub(r"(?<=[a-z]{3})s$", "", w) if len(w) > 3 else w  # "docks" -> "dock", "tees" -> "tee", but "ups" stays
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
    if {w for w in t if re.search(r"\d", w)} - descs[best[0][1]]:
        return None  # "400A meter-main combo" is not the exit combo: a size or rating the item does not have
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
        if by_measure(v) or v.get("per"):  # "500 ft reel", "10 ft stick" is the package, not a spec:
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


PACKAGE = re.compile(rf"\b\d+\s*[a-z]+\.?\s+(?:{CONTAINERS})s?\b", re.I)


def _core(desc):
    """The description without its package ('type L pipe 3/4in, 20 ft stick' -> 'type L pipe 3/4in'): items that differ
    only in package size are one item to identify; pick_package chooses the package."""
    return PACKAGE.sub(" ", desc)


def supported(pricing, text, sku):
    """True when the request names something that identifies this SKU: its code, or a description word no other
    item shares. 'laptops' alone does not pick between two laptops, so the model's choice is not accepted.
    Package size is ignored here (see pick_package); a not-stocked item only competes when it fits the request better."""
    t = re.sub(r"(\d+)\s*(?:in\b|inch\b|\")", r"\1in", text, flags=re.I)
    flat = re.sub(r"[^A-Z0-9]", "", t.upper())
    if re.sub(r"[^A-Z0-9]", "", sku.upper()) in flat:
        return True
    descs = {k: _tokens(_core(v["desc"])) for k, v in pricing["skus"].items()}
    core = descs.get(sku, set())
    same = {k for k, d in descs.items() if d == core}  # the same item in other package sizes
    df = {}
    for k, d in descs.items():
        if k not in same or k == sku:
            for w in d:
                df[w] = df.get(w, 0) + 1
    mine, said = core, _tokens(t)
    unique = {w for w in mine if df[w] == 1}
    if bool(unique & said) or (bool(mine) and mine <= said):  # a unique word, or the whole description
        return True
    hit = mine & said  # or the words said, together, fit this item and no other ("thhn 12 black")
    others = {k: d for k, d in descs.items() if k not in same}
    stocked = lambda k: pricing["skus"][k].get("stock", True)
    return (len(hit) >= 2 and not any(hit <= d for k, d in others.items() if stocked(k))
            and not any((d & said) > hit for d in others.values()))


def _default_packages(body):
    """'If the customer does not say 10 ft or 20 ft sticks, quote the 20 ft stick SKU' -> [(20, 'stick')]."""
    return [(int(m.group(1)), m.group(2).lower()) for m in re.finditer(
        rf"\b(?:does not|doesn't|do not|don't)\s+(?:say|give|name)[^.]*?,\s*(?:quote|use|price)\s+the\s+(\d+)\s*[a-z]+\.?\s+({CONTAINERS})s?\b",
        body.replace("*", ""), re.I)]


def pick_package(pricing, sku, qty, text):
    """Items that differ only in package size (10 ft / 20 ft stick, 100 / 300 ft coil): the package the request names;
    else the default package a note states; else the one package whose full size equals the quantity; else the model's
    pick if there is no other choice. Returns (sku, note) or (None, why to ask). qty is in the item's unit."""
    item = pricing["skus"].get(sku)
    if not item or not item.get("full") or re.sub(r"[^A-Z0-9]", "", sku) in re.sub(r"[^A-Z0-9]", "", text.upper()):
        return sku, ""
    core = _tokens(_core(item["desc"]))
    sib = {k: v for k, v in pricing["skus"].items() if v.get("full") and v.get("unit") == item["unit"]
           and _tokens(_core(v["desc"])) == core and v.get("stock", True)}
    if len(sib) < 2:
        return sku, ""
    u = [w for w, v in MEASURE.items() if v == item["unit"] and w not in ("#",)]
    named = [k for k, v in sib.items() if re.search(
        rf"(?<![\d/.]){v['full']}\s*(?:{'|'.join(map(re.escape, u))})?\.?\s*(?:{CONTAINERS}|s\b)", text, re.I)]
    if len(named) == 1:
        return named[0], ("" if named[0] == sku else f"{named[0]} (the {sib[named[0]]['full']} {item['unit']} {sib[named[0]]['container']} the request names)")
    dflt = [k for k, v in sib.items() if (v["full"], v["container"]) in pricing.get("default_packages", [])]
    if not named and len(dflt) == 1:
        return dflt[0], f"{dflt[0]} (no {item['container']} size named: the default {sib[dflt[0]]['full']} {item['unit']} {item['container']})"
    fit = [k for k, v in sib.items() if v["full"] == qty]
    if not named and len(fit) == 1:
        return fit[0], ("" if fit[0] == sku else f"{fit[0]} ({qty} {item['unit']} is one full {item['container']})")
    sizes = ", ".join(f"{v['full']} {item['unit']}" for v in sib.values())
    return None, f"{sku} comes in {item['container']}s of {sizes} and the request does not say which: ask the customer"


def _spec_units(pricing):
    """Words written after a number in two or more descriptions ('5 ton', '50 gal', '20A'): the price book's own ratings.
    Lengths, weights and package words are quantities or packages, not ratings."""
    seen = {}
    for v in pricing["skus"].values():
        for _, u in re.findall(r"(?<![\w/.-])(\d+(?:\.\d+)?)[\s-]*([a-z]+\d?)\b", v["desc"].lower()):
            seen[u] = seen.get(u, 0) + 1
    skip = set(MEASURE) | set(CONTAINERS.split("|")) | {"x", "to", "of", "and", "or", "in", "inch", "box", "bag", "case", "pack"}
    return {u for u, k in seen.items() if k >= 2 and u not in skip}


def _ratings(s, units):
    """[(unit, {values}, start, end)]: '3.5 ton' -> ('ton', {3.5}); '2.5 to 3 ton' -> ('ton', {2.5, 3.0})."""
    if not units:
        return []
    u = "|".join(sorted(map(re.escape, units), key=len, reverse=True))
    out = []
    for m in re.finditer(rf"(?<![\w/.-])(\d+(?:\.\d+)?)(?:\s*(?:to|-)\s*(\d+(?:\.\d+)?))?[\s-]*({u})\b", s.lower()):
        out.append((m.group(3), {float(m.group(1))} | ({float(m.group(2))} if m.group(2) else set()), m.start(), m.end()))
    return out


def spec_conflict(pricing, text, sku):
    """The request attaches a rating to this kind of item ('3.5 ton condenser') and this SKU has another value of that
    rating while some item of the same kind has the asked value: the model picked the wrong item. Returns why, or ''."""
    item = pricing["skus"].get(sku)
    if not item:
        return ""
    units = _spec_units(pricing)
    mine = {}
    for u, vals, _, _ in _ratings(item["desc"], units):
        mine.setdefault(u, set()).update(vals)
    words = _tokens(re.sub(r"\d+(?:\.\d+)?", " ", item["desc"]))
    for sent in re.split(r"(?<=[.?!])\s+|\n+", text):
        toks = [(w.group(0), w.start(), w.end()) for w in re.finditer(r"[A-Za-z][A-Za-z-]*", sent)]
        for u, vals, s0, s1 in _ratings(sent, units):
            if u not in mine or vals & mine[u]:
                continue
            near = set()
            for w, a, b in [x for x in toks if x[2] <= s0][-1:] + [x for x in toks if x[1] >= s1][:2]:
                near |= _tokens(w)
            if not (near & words):
                continue  # the rating is about another item on the request
            kind = [k for k, v in pricing["skus"].items() if k != sku and near & _tokens(v["desc"])
                    and any(u2 == u and vals & v2 for u2, v2, _, _ in _ratings(v["desc"], units))]
            if kind:
                after = next((w for w, a, _ in toks if a >= s1), "")
                return (f"the request asks for {sent[s0:s1].strip()} {after}".rstrip() + f", but {sku} is "
                        f"{'/'.join(f'{x:g}' for x in sorted(mine[u]))} {u}: not priced; ask the customer which item")
    return ""


def echo_of(pricing, text, sku, other):
    """True when every request word that fits this SKU is also in the other line's item: the line repeats that item's
    own description (a rating or a part name), it is not a separate item the customer asked for."""
    said = _tokens(text)
    hit = _tokens(_core(pricing["skus"][sku]["desc"])) & said
    return bool(other in pricing["skus"]) and hit <= _tokens(pricing["skus"][other]["desc"])
