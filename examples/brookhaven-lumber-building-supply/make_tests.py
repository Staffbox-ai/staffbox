"""Build the Brookhaven Lumber & Building Supply (fictional) test sets. Expected totals are computed here, from the
vault's own price book, by this file's own pricing code (it does not import staffbox.actions, so the worker's code never
grades itself).

Written and committed 15 Oct 2026 BLIND (unseen set #3): from Staffbox-ai/staffbox main only, without looking at any
in-flight worker branch. Not yet scored. Score it once, after the next worker change lands; never tune the worker against it.
Pricing rules implemented here are the ones written in vault/sops/quote-a-line.md, vault/price-levels.md (rule order),
vault/units-and-cuts.md and vault/policies/delivery.md:
  goods = qty x list; quantity break (lumber by full bundle 7%, board feet 200+ 5%, sheets 20+/50+ 3%/6%, fastener
  boxes/each 10+ 5%; none on lb nails, bagged goods, trim, doors); contractor -8% or builder -12% (never on a pallet row);
  market adjustment on DL-/PT- lines (parsed from lumber-market-adjustment.md, rate in effect today); trim cut charge
  $2.00 when lf is not whole lengths; bag requests split into whole pallets + loose bags; one delivery fee per order by
  zone, free in zones 1-2 at $2,500+; round each step.
Usage: python3 make_tests.py standard > tests.jsonl
       python3 make_tests.py messy > tests-messy.jsonl
"""
import json, math, pathlib, random, re, sys

VAULT = pathlib.Path(__file__).parent / "vault"
LEVEL = {None: 0.0, "contractor": 0.08, "builder": 0.12}
CUT = 2.00


def cells(line):
    return [x.strip() for x in line.strip().strip("|").split("|")]


def money(s):
    return float(s.lstrip("$").replace(",", ""))


def price_book():
    """{SKU: dict(desc, unit, price, stock)} from every price-*.md table."""
    book = {}
    for p in sorted(VAULT.glob("price-*.md")):
        for line in p.read_text().splitlines():
            c = cells(line)
            if line.startswith("| ") and len(c) == 5 and c[3].startswith("$"):
                book[c[0]] = dict(desc=c[1], unit=c[2], price=money(c[3]), stock=c[4])
    return book


def bundles():
    """{nominal size: pieces per bundle} from the bundle table in quantity-breaks.md."""
    out = {}
    for line in (VAULT / "quantity-breaks.md").read_text().splitlines():
        c = cells(line)
        if line.startswith("| ") and len(c) == 2 and c[1].isdigit():
            out[c[0]] = int(c[1])
    return out


def market():
    """{SKU prefix: adjustment} for the rates in effect today ("until further notice")."""
    out = {}
    for line in (VAULT / "lumber-market-adjustment.md").read_text().splitlines():
        c = cells(line)
        if line.startswith("| ") and len(c) == 3 and "until further notice" in c[2]:
            out[re.search(r"\((\w\w)-\)", c[0]).group(1) + "-"] = float(c[1].strip("+%")) / 100
    return out


def zones():
    """({area: zone}, {zone: fee}, free-delivery threshold, {zones that get free delivery}) from policies/delivery.md."""
    text = (VAULT / "policies" / "delivery.md").read_text()
    area, fee = {}, {}
    for line in text.splitlines():
        c = cells(line)
        if line.startswith("| ") and len(c) == 3 and c[0].isdigit():
            fee[int(c[0])] = money(c[2])
            for a in c[1].split(", "):
                area[a] = int(c[0])
    m = re.search(r"Free delivery in zones (\d) and (\d) on orders of (\$[\d,]+\.\d\d)", text)
    return area, fee, money(m.group(3)), {int(m.group(1)), int(m.group(2))}


B, BUNDLE, MARKET = price_book(), bundles(), market()
AREA, FEE, FREE_AT, FREE_ZONES = zones()
assert MARKET == {"DL-": 0.05, "PT-": 0.03}, MARKET


def nominal(sku):
    """'2x4', '5/4x6' ... from the description."""
    return re.match(r"(?:pressure-treated )?(\d+(?:/\d)?x\d+)", B[sku]["desc"]).group(1)


def stock_len(sku):
    return int(re.search(r"(\d+) ft lengths", B[sku]["desc"]).group(1))


def pack(sku):
    m = re.match(r"box of (\d+)", B[sku]["unit"])
    return int(m.group(1))


def boxes(sku, pieces):
    """Pieces -> boxes; must be whole (else the right answer is to ask)."""
    assert pieces % pack(sku) == 0, (sku, pieces)
    return pieces // pack(sku)


def board_feet(thick, width, length, pieces):
    """Nominal T (in) x W (in) x L (ft) / 12 per piece, line rounded up to a whole board foot."""
    return math.ceil(thick * width * length * pieces / 12 - 1e-9)


def pallet_of(sku):
    return sku + "-P" if sku + "-P" in B else None


def brk(sku, qty):
    if sku.startswith(("DL-", "PT-")):
        return 0.07 if qty >= BUNDLE[nominal(sku)] else 0.0
    if sku.startswith("HW-"):
        return 0.05 if qty >= 200 else 0.0
    if sku.startswith("SG-"):
        return 0.06 if qty >= 50 else 0.03 if qty >= 20 else 0.0
    if sku.startswith("FS-") and B[sku]["unit"] != "lb":
        return 0.05 if qty >= 10 else 0.0
    return 0.0


def line(sku, qty, level=None):
    """One line total by the SOP. qty is in the item's own unit (piece, bf, sheet, box, lb, bag, pallet, ea, lf)."""
    it = B[sku]
    assert it["stock"] == "stocked", sku
    x = round(qty * it["price"], 2)
    d = brk(sku, qty)
    if d:
        x = round(x * (1 - d), 2)
    if level and not it["unit"].startswith("pallet"):
        x = round(x * (1 - LEVEL[level]), 2)
    if sku[:3] in MARKET:
        x = round(x * (1 + MARKET[sku[:3]]), 2)
    if it["unit"] == "lf" and qty % stock_len(sku):
        assert qty >= 2 and qty == int(qty), (sku, qty)
        x = round(x + CUT, 2)
    return x


def bags(sku, n, level=None):
    """A bag request for an item with a pallet row: whole pallets at the pallet row + loose bags at the bag price."""
    p = pallet_of(sku)
    per = int(re.match(r"pallet of (\d+)", B[p]["unit"]).group(1))
    full, loose = divmod(n, per)
    out = []
    if full:
        out.append((p, full, level))
    if loose:
        out.append((sku, loose, level))
    return out


def total(*lines):
    return round(sum(line(*l) for l in lines), 2)


def delivered(area, *lines):
    goods = total(*lines)
    z = AREA[area]
    fee = 0.0 if z in FREE_ZONES and goods >= FREE_AT else FEE[z]
    return round(goods + fee, 2)


# the SOP's worked examples must come out of this code exactly
assert line("SG-CDX12", 30) == 942.84
assert line("DL-2810", 96, "contractor") == 990.09
assert total(*bags("CM-CON80", 48, "builder")) == 280.46
assert line("TR-CAS312", 70) == 117.50


# ---------- standard 40: same mix as Ponce / Chattahoochee (16 quote, 10 lookup, 8 triage, 6 unknown) ----------
EACH_ASKS = ["Quote {q} x {d} ({sku}). What is the line total?",
             "Customer wants {q} of the {d}, list price. How much for the line?",
             "Price {q} of {sku} please."]
LEVEL_ASKS = {"contractor": ["Contractor account: price {q} of {sku} at contractor level.",
                             "Quote {q} x {d} ({sku}) for a contractor account. What is the line total?"],
              "builder": ["Builder account: price {q} of {sku} at builder level.",
                          "Quote {q} x {d} ({sku}) for a builder program account. What is the line total?"]}
PIECE_ASKS = ["Quote {q} pieces of {d} ({sku}). What is the line total?",
              "Price {q} pcs of {sku} please."]
BF_ASKS = ["Quote {q} board feet of {d} ({sku}). What is the line total?"]
LF_ASKS = ["Quote {q} linear feet of {d} ({sku}). What is the line total?",
           "Price {q} lf of {sku} please."]
BAG_ASKS = ["Quote {q} bags of {d} ({sku}). What is the total?"]
LB_ASKS = ["Quote {q} lb of {d} ({sku}). What is the line total?"]
LOOKUPS = [("What is the market adjustment on dimensional lumber right now?", ["5%"]),
           ("When did the current lumber market adjustment take effect?", ["october"]),
           ("What do we charge to cut trim?", ["$2.00"]),
           ("How much off list does a builder account get?", ["12%"]),
           ("How much off list does a contractor account get?", ["8%"]),
           ("What are the will-call yard hours on weekdays?", ["6:30", "5:00"]),
           ("What's the restocking fee on a return?", ["20%"]),
           ("What's the delivery fee to Dunwoody?", ["$55"]),
           ("Who can approve a price below a customer's account level?", ["general manager"]),
           ("What deposit do we take on a special-order item?", ["50%"])]
TRIAGE = [("Need pricing on 40 pt 2x10x16 and 30 sheets of 3/4 cdx for a deck job Thursday.", "quote"),
          ("Truck was supposed to drop the framing package at our Dunwoody lot by 7. PO 2291, where is it?", "order_status"),
          ("Is the Okafor Builders order pulled and ready at the yard yet?", "will_call"),
          ("The 20 pt 2x6x12 you delivered yesterday are badly twisted. Want to send them back.", "returns"),
          ("Need a price and lead time on 14 vinyl single-hung windows 3/0 x 5/0 for a new build.", "millwork"),
          ("We'd like to get on the builder program. We started 30 homes this year.", "credit"),
          ("Our two fiberglass entry doors were ordered three weeks ago. Have they come in?", "millwork"),
          ("Are you hiring forklift drivers for the yard?", "other")]
UNKNOWN = ["Price 12 LVL beams, 1-3/4 x 11-7/8, 20 ft.",
           "What is the warranty on the vinyl windows?",
           "Price 10 of DL-21220 (2x12 x 20 ft).",
           "Quote 4 prehung exterior steel doors 3/0 x 6/8 (DW-EXT3068-ST).",
           "What does delivery cost to Athens?",
           "Do we sell metal roofing panels, and at what price?"]


def standard():
    r = random.Random(1015)
    stocked = [k for k, v in B.items() if v["stock"] == "stocked"]
    each = [k for k in stocked if k.startswith(("SG-", "FS-", "CM-")) and B[k]["unit"] not in ("lb", "bag")
            and not B[k]["unit"].startswith("pallet")]
    lumber = [k for k in stocked if k.startswith(("DL-", "PT-"))]
    bf = [k for k in stocked if k.startswith("HW-")]
    trim = [k for k in stocked if k.startswith("TR-")]
    bagged = [k for k in stocked if pallet_of(k) and B[pallet_of(k)]["stock"] == "stocked"]
    lb = [k for k in stocked if B[k]["unit"] == "lb"]
    plan = (["each"] * 4 + ["contr"] * 2 + ["builder"] * 2 + ["lumber"] * 3 +
            ["lumber_builder", "board_feet", "trim", "bags", "lb"])
    r.shuffle(plan)
    tests = []
    for i, kind in enumerate(plan, 1):
        level = {"contr": "contractor", "builder": "builder", "lumber_builder": "builder"}.get(kind)
        if kind in ("each", "contr", "builder"):
            sku = r.choice(each); q = r.choice([4, 6, 8, 10, 12, 20, 24, 30, 40, 50, 60, 75, 100])
            asks = EACH_ASKS if level is None else LEVEL_ASKS[level]
        elif kind in ("lumber", "lumber_builder"):
            sku = r.choice(lumber); q = r.choice([10, 24, 40, 60, 80, 96, 100, 128, 150, 208])
            asks = PIECE_ASKS if level is None else LEVEL_ASKS[level]
        elif kind == "board_feet":
            sku = r.choice(bf); q = r.choice([40, 60, 120, 200, 250])
            asks = BF_ASKS
        elif kind == "trim":
            sku = r.choice(trim); q = r.choice([48, 64, 100, 120, 150, 200])
            asks = LF_ASKS
        elif kind == "bags":
            sku = r.choice(bagged); q = r.choice([30, 50, 60, 90, 120])
            asks = BAG_ASKS
        else:
            sku = r.choice(lb); q = r.choice([10, 25, 50])
            asks = LB_ASKS
        expect = total(*bags(sku, q, level)) if kind == "bags" else line(sku, q, level)
        tests.append(dict(id=f"quote-{i:02d}", type="quote", tag=kind, prompt=r.choice(asks).format(q=q, d=B[sku]["desc"], sku=sku),
                          expect=expect))
    tests += [dict(id=f"lookup-{i+1:02d}", type="lookup", prompt=p, expect=e) for i, (p, e) in enumerate(LOOKUPS)]
    tests += [dict(id=f"triage-{i+1:02d}", type="triage", prompt=f"Route this email to one queue.\n\n\"{p}\"", expect=e) for i, (p, e) in enumerate(TRIAGE)]
    tests += [dict(id=f"unknown-{i+1:02d}", type="unknown", prompt=p, expect="NOT IN VAULT") for i, p in enumerate(UNKNOWN)]
    return tests


# ---------- messy 15: builder texts; yard shorthand, missing lengths, board feet vs pieces, pallets, delivery zones; 4 should ask or decline ----------
ASK = "NOT IN VAULT"
assert B["DW-EXT3068-ST"]["stock"] == "special order"                  # messy-11
assert "Gainesville" not in AREA                                        # messy-14
assert 1000 % pack("FS-DS3-350")                                       # messy-15: not whole boxes
MESSY = [
    ("multi-abbrev", "need 50 2x4x8 kd and 20 sheets 3/4 cdx. thx", total(("DL-2408", 50), ("SG-CDX34", 20))),
    ("pt-shorthand", "pt 4x4x10 x 12 + 700 3in deck screws", total(("PT-4410", 12), ("FS-DS3-350", boxes("FS-DS3-350", 700)))),
    ("board-feet-from-pieces", "12 pcs 1x6x8 poplar", total(("HW-POP-4", board_feet(1, 6, 8, 12)))),
    ("board-feet-builder", "220 bf 4/4 red oak, builder acct", total(("HW-ROAK-4", 220, "builder"))),
    ("missing-length", "need 60 2x6s and 10 lbs of 16d for the Ashford job", ASK),
    ("full-unit", "full unit of 2x4x10 kd, our acct", total(("DL-2410", BUNDLE["2x4"], "contractor"))),
    ("bags-to-pallet", "50 80s pls", total(*bags("CM-CON80", 50))),
    ("contractor-deck-lines", "contractor acct: 30 pt 2x6x12, 10 pt 2x10x12, 25 2x10 hangers, 25 lb 16d galv",
     total(("PT-2612", 30, "contractor"), ("PT-21012", 10, "contractor"), ("FS-JH210", 25, "contractor"), ("FS-16G-LB", 25, "contractor"))),
    ("trim-cut", "180 lf 3-1/4 base primed", total(("TR-BASE314", 180))),
    ("trim-sticks-builder", "6 sticks 2-1/4 casing, builder pricing", total(("TR-CAS214", 6 * stock_len("TR-CAS214"), "builder"))),
    ("special-order-door", "need 3 3/0 steel ext doors prehung, what's the price", ASK),
    ("door-no-hand", "4 2/8 6 panel prehung interior doors", ASK),
    ("delivered-zone-1", "drop to Chamblee: 40 studs + 10 sheets 7/16 osb", delivered("Chamblee", ("DL-24PC", 40), ("SG-OSB716", 10))),
    ("delivery-unknown-zone", "send 100 2x4x8 kd out to Gainesville tmrw", ASK),
    ("builder-pallets-delivered", "builder acct, 2 pallets 60lb concrete + 10 bags type s, deliver to Decatur",
     delivered("Decatur", ("CM-CON60-P", 2, "builder"), ("CM-MS80", 10, "builder"))),
]
assert sum(e == ASK for _, _, e in MESSY) == 4


def messy():
    return [dict(id=f"messy-{i:02d}", type="unknown" if e == ASK else "quote", tag=t, prompt=p, expect=e) for i, (t, p, e) in enumerate(MESSY, 1)]


if __name__ == "__main__":
    for t in {"standard": standard, "messy": messy}[sys.argv[1]]():
        print(json.dumps(t))
