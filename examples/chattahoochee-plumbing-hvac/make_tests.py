"""Build the Chattahoochee Plumbing & HVAC Supply (fictional) test sets. Expected totals are computed here, from the
vault's own price book, by this file's own pricing code (it does not import staffbox.actions, so the worker's code never
grades itself).

Written and committed 14 Oct 2026 BLIND: from Staffbox-ai/staffbox main only, without looking at any in-flight worker
branch. Not yet scored. Score it once, after the worker PR lands; never tune the worker against it.
Pricing rules implemented here are the ones written in vault/sops/quote-a-line.md and vault/units-and-cuts.md:
  matched pair -> SYS row; goods = qty x list; quantity break (not per-foot, per-pound or equipment lines);
  contractor -10% or Trade Pro -15%; refrigerant + surcharge per lb (parsed from refrigerant-surcharge.md);
  copper cut charge $3.50 when the feet are not whole sticks; round each step.
Usage: python3 make_tests.py standard > tests.jsonl
       python3 make_tests.py messy > tests-messy.jsonl
"""
import json, pathlib, random, re, sys

VAULT = pathlib.Path(__file__).parent / "vault"
LEVEL = {None: 0.0, "contractor": 0.10, "pro": 0.15}
CUT = 3.50
EQUIPMENT = ("WH-", "AC-", "AH-", "SYS-")


def cells(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]


def price_book():
    """{SKU: dict(desc, unit, price, stock)} from every price-*.md table."""
    book = {}
    for p in sorted(VAULT.glob("price-*.md")):
        for line in p.read_text().splitlines():
            c = cells(line)
            if line.startswith("| ") and len(c) == 5 and c[3].startswith("$"):
                book[c[0]] = dict(desc=c[1], unit=c[2], price=float(c[3][1:].replace(",", "")), stock=c[4])
    return book


def matched_systems():
    """{(condenser, air handler): system SKU} from the matched-systems table."""
    out = {}
    for line in (VAULT / "price-hvac-equipment.md").read_text().splitlines():
        c = cells(line)
        if line.startswith("| SYS-") and len(c) == 4:
            out[(c[1], c[2])] = c[0]
    return out


def surcharges():
    """{refrigerant name: $ per lb} for the rates in effect today ("until further notice")."""
    out = {}
    for line in (VAULT / "refrigerant-surcharge.md").read_text().splitlines():
        c = cells(line)
        if line.startswith("| R-") and len(c) == 3 and "until further notice" in c[2]:
            for name in c[0].split(", "):
                out[name] = float(c[1].lstrip("$"))
    return out


B, SYSTEMS, SUR = price_book(), matched_systems(), surcharges()


def size(sku, pattern):
    return int(re.search(pattern, B[sku]["desc"]).group(1))


def pack(sku):
    m = re.match(r"(?:bag|case) of (\d+)", B[sku]["unit"])
    return int(m.group(1)) if m else None


def packs(sku, pieces):
    """Pieces -> bags or cases; must be whole (else the right answer is to ask)."""
    assert pieces % pack(sku) == 0, (sku, pieces)
    return pieces // pack(sku)


def system_for(condenser, air_handler):
    return SYSTEMS.get((condenser, air_handler))


def pipe(kind, nominal):
    """Copper pipe named without a stick length -> the 20 ft stick SKU (units-and-cuts)."""
    return f"CP-{kind}{nominal}-20"


def breaks(sku):
    return B[sku]["unit"] not in ("ft", "lb") and not sku.startswith(EQUIPMENT)


def line(sku, qty, level=None):
    """One line total by the SOP. qty is in the item's own unit (feet, pounds, each, bag, case, coil, system)."""
    it = B[sku]
    assert it["stock"] == "stocked", sku
    if sku.startswith("PX-"):
        assert qty % size(sku, r"(\d+) ft coil") == 0, (sku, qty)
    if sku.startswith("RF-"):
        assert qty % size(sku, r"(\d+) lb cylinder") == 0, (sku, qty)
    if sku.startswith("CP-") and it["unit"] == "ft":
        assert qty >= 2 and qty == int(qty), (sku, qty)
    x = round(qty * it["price"], 2)
    if breaks(sku):
        d = 0.08 if qty >= 100 else 0.04 if qty >= 25 else 0.0
        x = round(x * (1 - d), 2)
    if level:
        x = round(x * (1 - LEVEL[level]), 2)
    if sku.startswith("RF-"):
        x = round(x + round(qty * SUR[it["desc"].split()[0]], 2), 2)
    if sku.startswith("CP-") and it["unit"] == "ft" and qty % size(sku, r"(\d+) ft stick"):
        x = round(x + CUT, 2)
    return x


def total(*lines):
    return round(sum(line(*l) for l in lines), 2)


# ---------- standard 40: same mix as Ponce / Fieldstone / Peachtree (16 quote, 10 lookup, 8 triage, 6 unknown) ----------
EACH_ASKS = ["Quote {q} x {d} ({sku}). What is the line total?",
             "Customer wants {q} of the {d}, list price. How much for the line?",
             "Price {q} of {sku} please."]
LEVEL_ASKS = {"contractor": ["Contractor account: price {q} of {sku} at contractor level.",
                             "Quote {q} x {d} ({sku}) for a contractor account. What is the line total?"],
              "pro": ["Trade Pro account: price {q} of {sku} at Trade Pro level.",
                      "Quote {q} x {d} ({sku}) for a Trade Pro account. What is the line total?"]}
FEET_ASKS = ["Quote {q} ft of {d} ({sku}). What is the line total?",
             "Price {q} feet of {sku} please."]
FEET_CONTR = ["Contractor account: price {q} feet of {sku} at contractor level."]
LB_ASKS = ["Quote {q} lb of {d} ({sku}). What is the line total?"]
LOOKUPS = [("What is the refrigerant surcharge on R-410A right now, per pound?", ["$3.25"]),
           ("When did the current R-410A surcharge take effect?", ["october"]),
           ("What do we charge to cut copper pipe?", ["$3.50"]),
           ("How much off list does a Trade Pro account get?", ["15%"]),
           ("How much off list does a contractor account get?", ["10%"]),
           ("What are the will-call counter hours on weekdays?", ["6:00", "5:00"]),
           ("What's the restocking fee on a return?", ["15%"]),
           ("What's the minimum order for free delivery inside I-285?", ["$750"]),
           ("Who can approve a price below a customer's price level?", ["branch manager"]),
           ("What deposit do we take on a special-order item?", ["30%"])]
TRIAGE = [("Need a price on 2 of the 50 gal gas heaters and 200' of 3/4 L for a job Thursday.", "quote"),
          ("Truck was supposed to drop our condenser at the Decatur job by 10. Where is it? PO 8812.", "order_status"),
          ("Is the Patel Plumbing order ready at the counter yet?", "will_call"),
          ("You sent 1/2 PEX-B instead of PEX-A. Never opened, need to swap it.", "returns"),
          ("The 40 gal electric we installed 8 months ago is leaking from the tank. Homeowner wants it covered.", "warranty"),
          ("Can we get set up on Trade Pro? We did over $300k with you last year.", "credit"),
          ("Please hold my order for pickup Saturday at 7.", "will_call"),
          ("I rep a line of tankless water heaters and would love 15 minutes with your buyer.", "other")]
UNKNOWN = ["Price 2 of the 4-ton heat pumps.",
           "What is the warranty term on the air handlers?",
           "Price 1 of the 50 gal heat pump water heaters (WH-HP50).",
           "Quote 100 ft of type K copper 3/4in, 20 ft stick (CP-K075-20).",
           "What does delivery cost to Gainesville?",
           "Do we carry boilers, and what does a 100,000 BTU one cost?"]


def standard():
    r = random.Random(1014)
    stocked = [k for k, v in B.items() if v["stock"] == "stocked"]
    each = [k for k in stocked if breaks(k)]
    pipes = [k for k in stocked if k.startswith("CP-") and B[k]["unit"] == "ft"]
    pex = [k for k in stocked if k.startswith("PX-")]
    refr = [k for k in stocked if k.startswith("RF-")]
    equip = [k for k in stocked if k.startswith(("WH-", "AC-", "AH-"))]
    systems = [k for k in stocked if k.startswith("SYS-")]
    plan = ["each"] * 5 + ["contr"] * 2 + ["pro"] * 2 + ["pipe"] * 2 + ["pipe_contr", "pex", "refrig", "equip", "system"]
    r.shuffle(plan)
    tests = []
    for i, kind in enumerate(plan, 1):
        level = {"contr": "contractor", "pro": "pro", "pipe_contr": "contractor"}.get(kind)
        if kind in ("each", "contr", "pro"):
            sku = r.choice(each); q = r.choice([4, 6, 10, 12, 20, 24, 25, 30, 40, 50, 60, 100, 120, 150])
            asks = EACH_ASKS if level is None else LEVEL_ASKS[level]
        elif kind in ("pipe", "pipe_contr"):
            sku = r.choice(pipes); q = r.choice([15, 20, 30, 40, 45, 60, 80, 100, 120, 150, 200])
            asks = FEET_ASKS if level is None else FEET_CONTR
        elif kind == "pex":
            sku = r.choice(pex); q = size(sku, r"(\d+) ft coil") * r.choice([1, 2, 3, 4])
            asks = FEET_ASKS
        elif kind == "refrig":
            sku = r.choice(refr); q = size(sku, r"(\d+) lb cylinder") * r.choice([1, 2, 4, 6])
            asks = LB_ASKS
        elif kind == "equip":
            sku = r.choice(equip); q = r.choice([1, 2, 3, 4, 6])
            asks = EACH_ASKS
        else:
            sku = r.choice(systems); q = r.choice([1, 2, 3]); level = "contractor"
            asks = LEVEL_ASKS[level]
        tests.append(dict(id=f"quote-{i:02d}", type="quote", tag=kind, prompt=r.choice(asks).format(q=q, d=B[sku]["desc"], sku=sku),
                          expect=line(sku, q, level)))
    tests += [dict(id=f"lookup-{i+1:02d}", type="lookup", prompt=p, expect=e) for i, (p, e) in enumerate(LOOKUPS)]
    tests += [dict(id=f"triage-{i+1:02d}", type="triage", prompt=f"Route this email to one queue.\n\n\"{p}\"", expect=e) for i, (p, e) in enumerate(TRIAGE)]
    tests += [dict(id=f"unknown-{i+1:02d}", type="unknown", prompt=p, expect="NOT IN VAULT") for i, p in enumerate(UNKNOWN)]
    return tests


# ---------- messy 15: contractor texts and emails; shorthand, missing sizes/lengths, mixed units; 5 should ask or decline ----------
ASK = "NOT IN VAULT"
assert system_for("AC-42-14", "AH-48-V") is None                      # messy-06: unmatched pairing
assert B["WH-HP50"]["stock"] == "special order"                        # messy-12
assert 30 % size("RF-454B-20", r"(\d+) lb cylinder")                   # messy-08: not whole cylinders
assert all(750 != size(k, r"(\d+) ft coil") for k in B if k.startswith("PX-A050"))  # messy-15: no 750 ft coil
MESSY = [
    ("multi-abbrev", "need 60' 3/4 cu L and 10 3/4 ells, thx", total((pipe("L", "075"), 60), ("FC-EL075", 10))),
    ("pex-shorthand", "pex a 1/2 300 x2 and a bag of 1/2 exp rings", total(("PX-A050-300", 600), ("PF-EXR050-50", 1))),
    ("pieces-to-bags", "need 200 1/2 crimp rings", total(("PF-CR050-100", packs("PF-CR050-100", 200)))),
    ("trade-pro-heaters", "we're trade pro - 3 of the 50 gal gas atmos heaters + 3 exp tanks", total(("WH-G50", 3, "pro"), ("WA-XT2", 3, "pro"))),
    ("matched-system", "3 ton straight cool, condenser + matching AH, contractor acct", total((system_for("AC-36-14", "AH-36-V"), 1, "contractor"))),
    ("unmatched-system", "3.5 ton condenser w/ the 4 ton air handler (AH-48-V), how much for the pair?", ASK),
    ("refrigerant-lbs", "50# of 410a for the Smyrna changeout", total(("RF-410A-25", 50))),
    ("refrigerant-part-cylinder", "30 lbs 454b", ASK),
    ("copper-10ft-cut", "45 ft 1/2 type m, 10' sticks pls", total(("CP-M050-10", 45))),
    ("missing-size", "need 100 ft of type L for a repipe + 4 ball valves", ASK),
    ("filters-pieces-to-cases", "24 16x25x1 merv 8 filters and 12 20x25x1 m11", total(("FL-16251-M8", packs("FL-16251-M8", 24)), ("FL-20251-M11", packs("FL-20251-M11", 12)))),
    ("special-order-heater", "got any 50 gal heat pump water heaters? need 2, TP pricing", ASK),
    ("contractor-mixed-lines", "contractor acct: 1 roll 3/4 pex-b 100' + 25 3/4 pex tees + 6 3/4 pex ball valves",
     total(("PX-B075-100", 100, "contractor"), ("PF-TE075", 25, "contractor"), ("VL-BV075-PX", 6, "contractor"))),
    ("default-stick-cut", "3/4 cu L 30 ft, our acct", total((pipe("L", "075"), 30, "contractor"))),
    ("pex-not-a-coil", "750' 1/2 pex-a", ASK),
]


def messy():
    return [dict(id=f"messy-{i:02d}", type="unknown" if e == ASK else "quote", tag=t, prompt=p, expect=e) for i, (t, p, e) in enumerate(MESSY, 1)]


if __name__ == "__main__":
    for t in {"standard": standard, "messy": messy}[sys.argv[1]]():
        print(json.dumps(t))
