"""Build the Ponce Electric Supply test sets. Expected totals are computed here, from the vault's own price book,
by this file's own pricing code (it does not import staffbox.actions, so the worker's code never grades itself).

Written and committed 14 Oct 2026 BEFORE the first run, as an unseen test of the worker as it stood (quote action v2.4).
Pricing rules implemented here are the ones written in vault/sops/quote-a-line.md:
  goods = qty x list; quantity break (not per-foot items); contractor -12%; copper +8%; cut charge $7.50; round each step.
Usage: python3 make_tests.py standard > tests.jsonl
       python3 make_tests.py messy > tests-messy.jsonl
"""
import json, pathlib, random, re, sys

VAULT = pathlib.Path(__file__).parent / "vault"
COPPER, CONTRACTOR, CUT = 0.08, 0.12, 7.50


def price_book():
    """{SKU: dict(desc, unit, price, stock)} from every price-*.md table."""
    book = {}
    for p in sorted(VAULT.glob("price-*.md")):
        for line in p.read_text().splitlines():
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            if line.startswith("| ") and len(c) == 5 and c[3].startswith("$"):
                book[c[0]] = dict(desc=c[1], unit=c[2], price=float(c[3][1:].replace(",", "")), stock=c[4])
    return book


B = price_book()


def full_length(sku):
    m = re.search(r"(\d+) ft (?:reel|coil)", B[sku]["desc"])
    return int(m.group(1))


def line(sku, qty, contractor=False):
    """One line total by the SOP. qty is in the item's own unit (feet, each, stick, box)."""
    it = B[sku]
    assert it["stock"] == "stocked", sku
    x = round(qty * it["price"], 2)
    if it["unit"] != "ft":
        d = 0.10 if qty >= 200 else 0.05 if qty >= 50 else 0.0
        x = round(x * (1 - d), 2)
    if contractor:
        x = round(x * (1 - CONTRACTOR), 2)
    if sku.startswith("W-"):  # every stocked W- item is copper (the aluminum SER is special order)
        x = round(x * (1 + COPPER), 2)
        if qty % full_length(sku):
            x = round(x + CUT, 2)
    return x


def total(*lines):
    return round(sum(line(*l) for l in lines), 2)


# ---------- standard 40: same mix as Fieldstone / Peachtree (16 quote, 10 lookup, 8 triage, 6 unknown) ----------
EACH_ASKS = ["Quote {q} x {d} ({sku}). What is the line total?",
             "Customer wants {q} of the {d}, list price. How much for the line?",
             "Price {q} of {sku} please."]
CONTR_ASKS = ["Contractor account: price {q} of {sku} at contractor level.",
              "Quote {q} x {d} ({sku}) for a contractor account. What is the line total?"]
WIRE_ASKS = ["Quote {q} ft of {d} ({sku}). What is the line total?",
             "Price {q} feet of {sku} please."]
WIRE_CONTR = ["Contractor account: price {q} feet of {sku} at contractor level."]
LOOKUPS = [("What is the copper surcharge on wire right now?", ["8%"]),
           ("When did the current copper surcharge take effect?", ["october"]),
           ("What's the minimum cut length on wire?", ["25 feet"]),
           ("What do we charge to cut wire off a reel?", ["$7.50"]),
           ("How much off list does a contractor account get?", ["12%"]),
           ("What are the will-call counter hours on weekdays?", ["6:30", "4:30"]),
           ("What's the restocking fee on a return?", ["20%"]),
           ("What's the minimum order for free delivery inside I-285?", ["$500"]),
           ("Who can approve a price below contractor level?", ["branch manager"]),
           ("What deposit do we take on a special-order item?", ["50%"])]
TRIAGE = [("Need pricing on 500' of 12/2 NM and 20 single pole 20s for a job Monday.", "quote"),
          ("Where's our delivery for PO 4471? Crew is standing around on site.", "order_status"),
          ("Is my order ready to pick up at the counter? Name is Ramirez Electric.", "will_call"),
          ("Got 3 breakers that were dead out of the box, want to send them back.", "returns"),
          ("We need our credit limit raised to $50k before the hospital job starts.", "credit"),
          ("Can you hold my order for pickup Saturday morning?", "will_call"),
          ("Our statement shows an invoice we already paid in September.", "credit"),
          ("Are you hiring CDL drivers?", "other")]
UNKNOWN = ["Price 10 of the 400A meter-main combos.",
           "What is the warranty on the LED high bays?",
           "Price 4 of the 2-pole 50A GFCI breakers (PG2-50).",
           "Quote 300 ft of 2 AWG THHN, black (W-THHN2-BK).",
           "What does delivery cost to Macon?",
           "Do we sell solar inverters, and at what price?"]


def standard():
    r = random.Random(1014)
    stocked = [k for k, v in B.items() if v["stock"] == "stocked"]
    wire = [k for k in stocked if B[k]["unit"] == "ft" and k.startswith("W-")]
    each = [k for k in stocked if B[k]["unit"] != "ft"]
    plan = ["each"] * 8 + ["contr"] * 3 + ["wire"] * 4 + ["wire_contr"]
    r.shuffle(plan)
    tests = []
    for i, kind in enumerate(plan, 1):
        if kind in ("each", "contr"):
            sku = r.choice(each); q = r.choice([4, 6, 10, 12, 20, 24, 40, 50, 60, 75, 100, 150, 200, 250])
            asks = EACH_ASKS if kind == "each" else CONTR_ASKS
        else:
            sku = r.choice(wire); q = r.choice([100, 150, 250, 300, 500, 750, 1000])
            asks = WIRE_ASKS if kind == "wire" else WIRE_CONTR
        c = kind.endswith("contr")
        tests.append(dict(id=f"quote-{i:02d}", type="quote", tag=kind, prompt=r.choice(asks).format(q=q, d=B[sku]["desc"], sku=sku),
                          expect=line(sku, q, c)))
    tests += [dict(id=f"lookup-{i+1:02d}", type="lookup", prompt=p, expect=e) for i, (p, e) in enumerate(LOOKUPS)]
    tests += [dict(id=f"triage-{i+1:02d}", type="triage", prompt=f"Route this email to one queue.\n\n\"{p}\"", expect=e) for i, (p, e) in enumerate(TRIAGE)]
    tests += [dict(id=f"unknown-{i+1:02d}", type="unknown", prompt=p, expect="NOT IN VAULT") for i, p in enumerate(UNKNOWN)]
    return tests


# ---------- messy 15: contractor emails; abbreviations, missing lengths, mixed units; 4 should ask or decline ----------
ASK = "NOT IN VAULT"
MESSY = [
    ("multi-abbrev", "need 250' 12-2 nm-b and 6 sp 20a breakers. thx", total(("W-NM12-2", 250), ("PB1-20", 6))),
    ("boxes-of", "2 boxes yellow wire nuts + 1 box red pls", total(("WN-YL-100", 2), ("WN-RD-100", 1))),
    ("feet-to-sticks", "pls price 200 ft of 3/4 emt", total(("CD-EMT-075", 20))),
    ("contractor-slang", "contractor acct - 60 of the 6in can retrofits", total(("LT-DL6", 60, True))),
    ("full-reels", "1000ft #12 thhn blk", total(("W-THHN12-BK", 1000))),
    ("missing-length", "need some 12/2 for a basement job + 10 1g old work boxes", ASK),
    ("pieces-to-boxes", "300 yellow wire nuts", total(("WN-YL-100", 3))),
    ("two-fixtures", "8 2x4 flat panels and 2 exit/emergency combos", total(("LT-FP24", 8), ("LT-EXC", 2))),
    ("qty-first", "qty 40 2p 30a breakers", total(("PB2-30", 40))),
    ("cut-wire", "75' of 10/2 nm w/ground", total(("W-NM10-2", 75))),
    ("special-order-ser", "do u have 4/0 al SER? need 150'", ASK),
    ("recept-pieces", "50 single gang new work boxes + 50 15a TR duplex recepts", total(("BX-1G-NW", 50), ("RC-15TR-10", 5))),
    ("special-order-panel", "price a 200A 40 space panel, outdoor (rainproof)", ASK),
    ("contractor-two-lines", "on our contractor account: 12 20A GFCI recepts and 12 WP in-use covers", total(("RC-GF20", 12, True), ("CV-WP-INUSE", 12, True))),
    ("missing-qty", "need 4 of the 150w high bays and some 1/2 emt", ASK),
]


def messy():
    return [dict(id=f"messy-{i:02d}", type="unknown" if e == ASK else "quote", tag=t, prompt=p, expect=e) for i, (t, p, e) in enumerate(MESSY, 1)]


if __name__ == "__main__":
    for t in {"standard": standard, "messy": messy}[sys.argv[1]]():
        print(json.dumps(t))
