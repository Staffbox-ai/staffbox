"""Quote action v2.6: the explicit rule order (break -> level -> surcharge -> cut) read from the vault, per-weight and
pack units, whole-package-only items, package sizes, matched sets. No model needed.
Run: python3 -m unittest discover -s tests

Ponce and Chattahoochee are DEV sets (these rules were built against their misses), so every rule is also tested on a
made-up feed-and-rope yard below that shares no item words with either."""
import datetime, json, pathlib, random, re, subprocess, sys, tempfile, textwrap, unittest
from staffbox import actions, evals

ROOT = pathlib.Path(__file__).parent.parent
EX = ROOT / "examples"
CHATT, PONCE = EX / "chattahoochee-plumbing-hvac" / "vault", EX / "ponce-electric-supply" / "vault"
D = datetime.date


def route(pricing, request, model_reply):
    real = evals.chat
    try:
        evals.chat = lambda *a, **k: (model_reply, 0)
        return evals.route_quote("", "", pricing, request)[0]
    finally:
        evals.chat = real


HEAD = "---\ntype: reference\nowner: {owner}\nupdated: 2026-10-01\nsource: test\ntags: [pricing]\n---\n"


def yard(order_notes=None):
    """A fictional feed-and-rope yard. order_notes replaces the sentences that set the rule order."""
    notes = order_notes or {
        "levels": "- **Farm level**: 10% off list.\n- A price level applies after the quantity break and before the levy and the cut charge.\n",
        "levy": "The levy is added after any price level.\n",
        "cuts": "Cut charge: $4.00 per cut, added after the levy. Minimum cut: 3 m.\n",
        "breaks": "Accounts get the break first, then their price level.\n",
    }
    files = {
        "price-yard.md": HEAD.format(owner="yard manager") + textwrap.dedent("""
            # Price book

            Oats are sold by the full drum only. Rope is cut from the spool.

            | SKU | Description | Unit | Price | Stock |
            |---|---|---|---|---|
            | OT-25 | rolled oats, 25 kg drum | kg | $2.00 | stocked |
            | RP-12-100 | hemp rope 12mm, 100 m spool | m | $1.50 | stocked |
            | RP-12-50 | hemp rope 12mm, 50 m spool | m | $1.60 | stocked |
            | HK-1 | iron hook | ea | $3.00 | stocked |
            | LN-10 | leather strap, bag of 10 | bag of 10 | $20.00 | stocked |
            | WG-4 | wagon kit 4 wheel: FR-4 frame + WH-4 wheel set | set | $500.00 | stocked |
            | FR-4 | wagon frame 4 | ea | $300.00 | stocked |
            | FR-6 | wagon frame 6 | ea | $380.00 | stocked |
            | WH-4 | wheel set 4 | ea | $260.00 | stocked |
            | WH-6 | wheel set 6 | ea | $300.00 | stocked |
            | GT-9 | gilded hook | ea | $90.00 | special order |

            ## Wagon sets

            | Set | Frame | Wheels |
            |---|---|---|
            | WG-4 | FR-4 | WH-4 |
            """).lstrip(),
        "breaks.md": HEAD.format(owner="yard manager") + "# Quantity breaks\n\nNo quantity break on items sold by the kilo, or on kits (WG-).\n\n"
                     "| Quantity on the line | Discount |\n|---|---|\n| 20 or more | 5% |\n| under 20 | none |\n\n"
                     "| Metres on the line | Discount |\n|---|---|\n| 200 or more | 2% |\n| under 200 | none |\n\n" + notes["breaks"],
        "levels.md": HEAD.format(owner="office") + "# Price levels\n\n" + notes["levels"],
        "levy.md": HEAD.format(owner="office") + "# Levy\n\n" + notes["levy"] + "\n| Product group | Surcharge per kg | Effective |\n|---|---|---|\n"
                   "| oats | $0.30 | 1 October 2026 until further notice |\n| oats, before that | $0.10 | 1 July 2026 to 30 September 2026 |\n\n"
                   "| Product group | Surcharge | Effective |\n|---|---|---|\n| hemp rope | 5% | 1 October 2026 until further notice |\n",
        "cuts.md": HEAD.format(owner="office") + "# Cuts\n\n" + notes["cuts"] +
                   "If the customer does not say 50 m or 100 m spools, quote the 100 m spool.\n",
    }
    d = pathlib.Path(tempfile.mkdtemp())
    for k, v in files.items():
        (d / k).write_text(v)
    return actions.load_pricing(d, today=D(2026, 10, 15))


class RuleOrderFromNotes(unittest.TestCase):
    def test_dev_vaults_state_break_level_surcharge_cut(self):
        for v in (CHATT, PONCE):
            p = actions.load_pricing(v)
            self.assertEqual(p["order"], ["break", "level", "surcharge", "cut"], v)
            self.assertIsNone(p["order_conflict"])
        pairs = {(a, b) for a, b, _ in actions.load_pricing(PONCE)["constraints"]}
        self.assertIn(("surcharge", "cut"), pairs)  # "Cut charge ... added after the copper surcharge"
        self.assertIn(("break", "level"), pairs)    # "get the break first, then their price level"

    def test_sentence_patterns(self):
        c = actions.order_constraints("price-levels", "It applies after the quantity break and before the surcharge and the cut charge.")
        self.assertEqual({(a, b) for a, b, _ in c}, {("break", "level"), ("level", "surcharge"), ("level", "cut")})
        c = actions.order_constraints("breaks", "Accounts get the break first, then their price level.")
        self.assertEqual({(a, b) for a, b, _ in c}, {("break", "level")})
        self.assertEqual(actions.order_constraints("x", "A quote written before 1 October is honored."), [])

    def test_notes_can_reorder(self):
        p = yard({"levels": "- **Farm level**: 10% off list. It applies after the levy.\n",
                  "levy": "The levy is added before the price level.\n", "cuts": "Cut charge: $4.00 per cut. Minimum cut: 3 m.\n",
                  "breaks": ""})
        self.assertEqual(p["order"], ["break", "surcharge", "level", "cut"])

    def test_contradiction_stops_the_quote(self):
        p = yard({"levels": "- **Farm level**: 10% off list. It applies after the levy.\n",
                  "levy": "The levy is added after any price level.\n", "cuts": "Cut charge: $4.00 per cut.\n", "breaks": ""})
        self.assertIsNone(p["order"])
        total, why = actions.quote(p, "HK-1", 5)
        self.assertIsNone(total)
        self.assertIn("conflicting rule orders", why)

    def test_topological_order_with_default_ties(self):
        self.assertEqual(actions.rule_order([])[0], list(actions.STEPS))
        self.assertEqual(actions.rule_order([("cut", "break", "s")])[0], ["level", "surcharge", "cut", "break"])
        self.assertIsNone(actions.rule_order([("cut", "break", "s"), ("break", "cut", "t")])[0])


def reference(order, base, qty, brk, lvl, sur_pct, sur_per, cut):
    """The pipeline written out by hand, for the property tests."""
    x = round(base * qty, 2)
    for s in order:
        if s == "break":
            x = round(x * (1 - brk), 2)
        elif s == "level":
            x = round(x * (1 - lvl), 2)
        elif s == "surcharge":
            x = round(x * (1 + sur_pct), 2) + round(sur_per * qty, 2)
            x = round(x, 2)
        elif s == "cut":
            x = round(x + cut, 2)
    return x


class OrderProperties(unittest.TestCase):
    """Property-style: random lines priced by the code equal the hand pipeline in the vault's order, and order matters."""

    def test_code_equals_reference_in_note_order(self):
        p, rnd = yard(), random.Random(1015)
        for _ in range(200):
            qty = rnd.choice([25, 50, 75, 100, 150, 200, 250])  # whole drums of 25 kg
            lvl = rnd.choice([None, "farm"])
            got = actions.quote(p, "OT-25", qty, level=lvl)[0]
            want = reference(p["order"], 2.00, qty, 0.0, 0.10 if lvl else 0.0, 0.0, 0.30, 0.0)
            self.assertEqual(got, want, (qty, lvl))
            m = rnd.choice([30, 45, 120, 230, 260, 310])
            got = actions.quote(p, "RP-12-100", m, level=lvl)[0]
            cut = 4.0 if m % 100 else 0.0
            want = reference(p["order"], 1.50, m, 0.02 if m >= 200 else 0.0, 0.10 if lvl else 0.0, 0.05, 0.0, cut)
            self.assertEqual(got, want, (m, lvl))

    def test_order_matters(self):
        """A per-unit levy before the level gets discounted; after it, it does not. A fixed cut charge before a percent
        step changes with it. So the same line has different totals under different orders."""
        rnd, diff = random.Random(7), 0
        for _ in range(100):
            qty, lvl, per, cut = rnd.randint(1, 400), rnd.choice([0.05, 0.1, 0.12, 0.15]), rnd.choice([0.25, 0.85, 3.25]), 3.5
            a = reference(["break", "level", "surcharge", "cut"], 1.0, qty, 0, lvl, 0, per, cut)
            b = reference(["break", "surcharge", "level", "cut"], 1.0, qty, 0, lvl, 0, per, cut)
            c = reference(["break", "level", "cut", "surcharge"], 1.0, qty, 0, lvl, 0.08, 0, cut)
            d = reference(["break", "level", "surcharge", "cut"], 1.0, qty, 0, lvl, 0.08, 0, cut)
            self.assertGreater(a, b)  # level after the levy discounts the levy: lower total
            self.assertNotEqual(c, d)  # a percent surcharge on the cut charge vs not
            diff += a != b
        self.assertEqual(diff, 100)

    def test_reordered_vault_prices_differently(self):
        normal = yard()
        swapped = yard({"levels": "- **Farm level**: 10% off list. It applies after the levy.\n",
                        "levy": "The levy is added before the price level.\n", "cuts": "Cut charge: $4.00 per cut. Minimum cut: 3 m.\n",
                        "breaks": ""})
        a, b = actions.quote(normal, "OT-25", 100, level="farm")[0], actions.quote(swapped, "OT-25", 100, level="farm")[0]
        self.assertEqual(a, 180.00 + 30.00)          # 200 -10% = 180, + 100 kg x 0.30
        self.assertEqual(b, round((200 + 30) * 0.9, 2))  # levy first, then the level discounts it
        work = actions.quote(swapped, "OT-25", 100, level="farm")[1]
        self.assertLess(work.index("levy"), work.index("farm level"))  # the working shows the order used


class EachRule(unittest.TestCase):
    def setUp(self):
        self.p = yard()

    def test_break_skips_units_and_prefixes_the_notes_name(self):
        self.assertEqual(self.p["no_break_units"], {"kg"})
        self.assertEqual(self.p["no_break_prefixes"], {"WG-"})
        self.assertEqual(actions.quote(self.p, "HK-1", 20)[0], 57.00)  # 60 -5%
        self.assertIn("no quantity break on WG- items", actions.quote(self.p, "WG-4", 20)[1])
        self.assertEqual(actions.quote(self.p, "WG-4", 20)[0], 10000.00)
        c = actions.load_pricing(CHATT)
        self.assertEqual(c["no_break_units"], {"ft", "lb"})
        self.assertTrue({"WH-", "AC-", "AH-", "SYS-"} <= c["no_break_prefixes"])

    def test_a_break_table_scoped_to_a_unit(self):
        self.assertEqual(self.p["unit_tiers"]["m"], [(200, float("inf"), 0.02), (0, 199, 0.0)])
        w = actions.quote(self.p, "RP-12-100", 200)[1]
        self.assertIn("less 2% quantity break", w)

    def test_level_only_when_named_and_said(self):
        self.assertIn("list price (no account level named)", actions.quote(self.p, "HK-1", 2)[1])
        self.assertIn("farm level -10%", actions.quote(self.p, "HK-1", 2, level="farm")[1])
        c = actions.load_pricing(CHATT)
        self.assertEqual(actions.account_level(c, actions.expand_synonyms(c, "we're trade pro - 3 heaters")), "trade pro")
        self.assertIsNone(actions.account_level(c, "3 of the 50 gal gas heaters"))

    def test_dated_surcharge_uses_the_request_date(self):
        self.assertEqual(actions.quote(self.p, "OT-25", 50)[0], 115.00)  # 100 + 50 x 0.30
        self.assertEqual(actions.quote(self.p, "OT-25", 50, on=D(2026, 9, 1))[0], 105.00)  # old rate 0.10
        self.assertEqual(actions.quote(self.p, "OT-25", 50, on=D(2026, 6, 1))[0], 100.00)  # no rate in effect
        self.assertIn("rate on 15 Oct 2026", actions.quote(self.p, "OT-25", 50)[1])

    def test_per_unit_surcharge_applies_only_to_that_unit(self):
        c = actions.load_pricing(CHATT)
        self.assertEqual(actions.quote(c, "RF-454B-20", 120)[0], 2682.00)  # 2,580 + 120 x 0.85
        self.assertNotIn("surcharge", actions.quote(c, "AC-36-14", 1)[1])  # names the same gas, sold each

    def test_cut_charge_minimum_and_package(self):
        self.assertIn("4 m cut", actions.quote(self.p, "RP-12-100", 104)[1].replace("4.00", ""))
        self.assertIsNone(actions.quote(self.p, "RP-12-100", 102)[0])  # 2 m cut, under the 3 m minimum
        self.assertNotIn("cut charge", actions.quote(self.p, "RP-12-100", 300)[1])  # whole spools

    def test_whole_package_only(self):
        self.assertEqual(self.p["whole_only"], {"drum"})
        total, why = actions.quote(self.p, "OT-25", 30)
        self.assertIsNone(total)
        self.assertIn("whole 25 kg drum only", why)
        c = actions.load_pricing(CHATT)
        self.assertEqual(c["whole_only"], {"coil", "cylinder"})
        self.assertIsNone(actions.quote(c, "RF-454B-20", 30)[0])
        self.assertIsNone(actions.quote(c, "PX-A050-500", 750)[0])


class Units(unittest.TestCase):
    def setUp(self):
        self.p = yard()

    def test_weight_and_full_packages(self):
        self.assertEqual(actions.to_unit(self.p, "OT-25", 75, "75 kg of oats")[0], 75)
        self.assertEqual(actions.to_unit(self.p, "OT-25", 3, "3 drums of oats")[0], 75)
        c = actions.load_pricing(CHATT)
        self.assertEqual(actions.to_unit(c, "RF-410A-25", 50, "50# of 410a")[0], 50)
        self.assertEqual(actions.to_unit(c, "RF-410A-25", 2, "2 jugs of 410a")[0], 50)
        self.assertEqual(actions.to_unit(c, "CP-L075-20", 3, "3 sticks of 3/4 L")[0], 60)

    def test_packs(self):
        self.assertEqual(actions.to_unit(self.p, "LN-10", 30, "30 leather straps")[0], 3)
        self.assertEqual(actions.to_unit(self.p, "LN-10", 2, "price 2 of the leather strap, bag of 10")[0], 2)
        self.assertEqual(actions.to_unit(self.p, "LN-10", 1, "a bag of leather straps")[0], 1)
        self.assertIsNone(actions.to_unit(self.p, "LN-10", 15, "15 leather straps")[0])

    def test_package_size_siblings(self):
        self.assertEqual(self.p["default_packages"], [(100, "spool")])
        self.assertEqual(actions.pick_package(self.p, "RP-12-50", 60, "60 m of 12mm hemp rope")[0], "RP-12-100")  # default
        self.assertEqual(actions.pick_package(self.p, "RP-12-100", 60, "60 m of 12mm hemp rope, 50 m spool")[0], "RP-12-50")
        self.assertEqual(actions.pick_package(self.p, "HK-1", 3, "3 hooks")[0], "HK-1")


class MatchedSets(unittest.TestCase):
    def setUp(self):
        self.p = yard()

    def test_parts_of_one_row_are_the_set(self):
        out = route(self.p, "wagon frame 4 and wheel set 4", "QUOTE: sku=FR-4; qty=2\nQUOTE: sku=WH-4; qty=2")
        self.assertIn("ANSWER: $1,000.00", out)
        self.assertIn("FR-4 + WH-4 = WG-4", out)

    def test_parts_not_on_one_row_are_declined_to_the_owner(self):
        out = route(self.p, "wagon frame 6 with wheel set 4", "QUOTE: sku=FR-6; qty=1\nQUOTE: sku=WH-4; qty=1")
        self.assertIn("NOT IN VAULT", evals.final_answer(out))
        self.assertIn("yard manager", out)
        self.assertNotIn("$", evals.final_answer(out))

    def test_one_part_alone_is_a_replacement(self):
        self.assertIn("ANSWER: $300.00", route(self.p, "one wheel set 6", "QUOTE: sku=WH-6; qty=1"))

    def test_different_quantities_are_asked(self):
        out = route(self.p, "2 wagon frame 4 and 3 wheel set 4", "QUOTE: sku=FR-4; qty=2\nQUOTE: sku=WH-4; qty=3")
        self.assertIn("NOT IN VAULT", evals.final_answer(out))

    def test_special_order_declined(self):
        out = route(self.p, "price 2 gilded hooks", "QUOTE: sku=GT-9; qty=2")
        self.assertIn("NOT IN VAULT", evals.final_answer(out))


class DevSetsOffline(unittest.TestCase):
    """Ponce + Chattahoochee (DEV): with the model's item and quantity fixed, code reproduces every expected value."""

    def test_offline_check(self):
        r = subprocess.run([sys.executable, str(ROOT / "scripts/offline_check.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_no_trade_words_in_code(self):
        code = " ".join((ROOT / "staffbox" / f).read_text().lower() for f in ("actions.py", "evals.py"))
        code = re.sub(r"#.*", "", re.sub(r'"""[\s\S]*?"""', "", code))
        for w in ["refrigerant", "condenser", "handler", "pex", "copper", "plumbing", "hvac", "filter", "merv", "heater", "pipe", "valve"]:
            self.assertNotRegex(code, rf"\b{re.escape(w)}\b", w)


class ObservedModelSlips(unittest.TestCase):
    """Router replies qwen3:8b actually wrote on the Chattahoochee DEV set (Dell, 15 Oct 2026, first v2.6 run).
    Each one priced wrong or refused a good line; code now prices it right or asks. Never a wrong price."""
    SLIPS = {
        "quote-06": ("QUOTE: sku=AC-60-14; qty=2; setup=no; unit=ea\nQUOTE: sku=RF-454B-20; qty=2; setup=no; unit=lb", 7040.00),
        "quote-10": ("QUOTE: sku=CP-M075-10; qty=15; unit=ft", 532.50),
        "quote-14": ("QUOTE: sku=FC-TE075; qty=150; setup=no; unit=ea\nQUOTE: sku=FC-TE075; qty=150; setup=no; unit=ea", 496.80),
        "messy-06": ("QUOTE: sku=SYS-48; qty=1; unit=system\nQUOTE: sku=AH-48-V; qty=1; unit=ea\nQUOTE: sku=AC-48-14; qty=1; unit=ea", None),
        "messy-09": ("QUOTE: sku=CP-M050-10; qty=10; unit=ft\nQUOTE: sku=CP-M050-20; qty=20; unit=ft", None),
        "messy-02": ("QUOTE: sku=PX-A050-300; qty=300; unit=ft\nQUOTE: sku=PF-EXR050-50; qty=1; unit=bag", None),
    }

    def test_each_slip(self):
        p = actions.load_pricing(CHATT)
        tests = {json.loads(l)["id"]: json.loads(l) for f in ("tests.jsonl", "tests-messy.jsonl")
                 for l in (CHATT.parent / f).read_text().splitlines()}
        for tid, (reply, want) in self.SLIPS.items():
            ans = evals.final_answer(route(p, tests[tid]["prompt"], reply))
            if want is None:  # the right answer was to ask, or the slip cannot be told from a right reading: ask
                self.assertTrue("NOT IN VAULT" in ans or evals.grade(tests[tid], ans), f"{tid}: {ans}")
            else:
                self.assertIn(f"${want:,.2f}", ans, tid)

    def test_synonym_row_with_several_meanings_expands_to_the_matching_one(self):
        p = actions.load_pricing(CHATT)
        self.assertEqual(actions.expand_synonyms(p, "12 20x25x1 m11"), "12 20x25x1 MERV 11 filter")

    def test_rating_conflict(self):
        p = actions.load_pricing(CHATT)
        t = "3.5 ton condenser w/ the 4 ton air handler (AH-48-V)"
        self.assertIn("4 ton", actions.spec_conflict(p, t, "AC-48-14"))
        self.assertEqual(actions.spec_conflict(p, t, "AH-48-V"), "")
        self.assertEqual(actions.spec_conflict(p, t, "AC-42-14"), "")


if __name__ == "__main__":
    unittest.main()
