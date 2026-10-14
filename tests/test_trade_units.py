"""Offline tests for trade price books: per-length units and cuts, account price levels, the synonyms note,
the special-order flag, and pack units. No model needed. Run: python3 -m unittest discover -s tests

Ponce Electric Supply is a DEV set from 14 Oct 2026 on (these features were built against its misses), so the
generic rules are also tested on a made-up rope-and-chain vault below that shares no words with it."""
import datetime, json, pathlib, re, tempfile, textwrap, unittest
from staffbox import actions, evals

EX = pathlib.Path(__file__).parent.parent / "examples"
PONCE = EX / "ponce-electric-supply"


def route(pricing, request, model_reply):
    """route_quote with the model's reply fixed, so only code is tested."""
    real = evals.chat
    try:
        evals.chat = lambda *a, **k: (model_reply, 0)
        out, _, _ = evals.route_quote("", "", pricing, request)
        return out
    finally:
        evals.chat = real


def vault(files):
    d = pathlib.Path(tempfile.mkdtemp())
    for name, body in files.items():
        (d / name).write_text(textwrap.dedent(body).lstrip())
    return d


HEAD = "---\ntype: reference\nowner: office\nupdated: 2026-10-01\nsource: test\n{extra}---\n"
ROPE = vault({
    "company.md": HEAD.format(extra="") + "# Harbor Rope and Chain\n",
    "log.md": HEAD.format(extra="") + "# Log\n",
    "price-list.md": HEAD.format(extra="tags: [pricing]\n") + """
        # Price list

        | SKU | Description | Price | Stock | Notes |
        |---|---|---|---|---|
        | RP-10 | polyester rope 10mm, 200 m spool | $1.20/m | yes | cut charge $3.00 under 50 m |
        | CH-8 | galvanized chain 8mm | $9.50/m | special order | |
        | SH-6 | bow shackle 6mm, pack of 20 | $30.00 | yes | |
        | TB-1 | turnbuckle | $4.00 | yes | |
        """.replace("        ", ""),
    "levels.md": HEAD.format(extra="tags: [pricing]\n") + """
        # Price levels

        | Level | Discount |
        |---|---|
        | marina | 15% |
        """.replace("        ", ""),
    "synonyms.md": HEAD.format(extra="tags: [synonyms]\n") + """
        # Synonyms

        | Customers write | We mean |
        |---|---|
        | poly, polyester line | polyester rope |
        | shackle | bow shackle |
        """.replace("        ", ""),
    "pier-9-marina.md": HEAD.format(extra="price_level: marina\naliases: [Pier 9]\n") + "# Pier 9 Marina\n",
})


class PerLength(unittest.TestCase):
    def setUp(self):
        self.p = actions.load_pricing(PONCE / "vault")

    def test_a_length_of_a_per_foot_item_is_a_line_not_unstocked(self):
        self.assertFalse(actions.unstocked(self.p, "Quote 100 ft of THHN 12 AWG stranded copper, black, 500 ft reel (W-THHN12-BK)."))
        self.assertEqual(actions.quote(self.p, "W-THHN12-BK", 100)[0], 33.42)  # 24.00 +8% copper = 25.92 + 7.50 cut

    def test_whole_reels_have_no_cut_charge(self):
        total, work = actions.quote(self.p, "W-THHN12-BK", 1000)
        self.assertEqual(total, 259.20)
        self.assertNotIn("cut", work)
        self.assertEqual(actions.to_unit(self.p, "W-THHN12-BK", 2, "2 reels of #12 thhn")[0], 1000)

    def test_minimum_cut_is_asked_not_priced(self):
        self.assertIsNone(actions.quote(self.p, "W-NM12-2", 10)[0])
        self.assertIsNone(actions.quote(self.p, "W-NM12-2", 260)[0])  # one coil + a 10 ft cut
        self.assertEqual(actions.quote(self.p, "W-NM12-2", 25)[0], round(round(25 * 0.78 * 1.08, 2) + 7.5, 2))

    def test_a_group_named_no_cut_charge_pays_none(self):
        total, work = actions.quote(self.p, "CD-FMC-050", 150)  # flex: per foot, no cut charge, not copper
        self.assertEqual(total, 102.00)

    def test_other_length_unit_is_asked(self):
        self.assertIsNone(actions.to_unit(self.p, "W-THHN12-BK", 30, "30 m of thhn")[0])

    def test_surcharge_row_in_effect_on_the_day(self):
        old = actions.load_pricing(PONCE / "vault", today=datetime.date(2026, 9, 15))
        self.assertEqual(actions.quote(old, "W-THHN12-BK", 500)[0], round(120 * 1.05, 2))
        self.assertEqual(actions.quote(self.p, "PB1-20", 6)[0], 40.80)  # breakers: no surcharge

    def test_per_meter_price_and_cut_under_rule_from_the_notes_column(self):
        r = actions.load_pricing(ROPE)
        self.assertEqual(r["skus"]["RP-10"]["unit"], "m")
        self.assertEqual(r["skus"]["RP-10"]["full"], 200)
        self.assertEqual(actions.quote(r, "RP-10", 30)[0], 39.00)  # 36.00 + $3 cut under 50 m
        self.assertEqual(actions.quote(r, "RP-10", 60)[0], 72.00)  # 50 m or more: no cut charge


class PriceLevels(unittest.TestCase):
    def setUp(self):
        self.p = actions.load_pricing(PONCE / "vault")

    def test_levels_parsed_from_the_note(self):
        self.assertEqual(self.p["levels"], {"list": 0.0, "contractor": 0.12})
        self.assertEqual(actions.load_pricing(ROPE)["levels"], {"marina": 0.15, "list": 0.0})

    def test_the_request_names_the_level(self):
        for t in ["Contractor account: price 12 of CV-4SQ-MR1", "contractor acct - 60 of the 6in can retrofits",
                  "on our contractor account: 12 GFCI", "price 5 at contractor level"]:
            self.assertEqual(actions.account_level(self.p, t), "contractor", t)
        for t in ["my contractor wants 10 of the 2x4 panels", "Price 6 of FT-LB075 please."]:
            self.assertIsNone(actions.account_level(self.p, t), t)

    def test_contractor_after_the_break_before_the_surcharge(self):
        self.assertEqual(actions.quote(self.p, "CD-EMT-050", 200, level="contractor")[0], 1140.48)
        self.assertEqual(actions.quote(self.p, "W-NM12-2", 300, level="contractor")[0], 229.89)  # SOP worked example 2

    def test_answer_says_which_level_was_used(self):
        out = route(self.p, "Price 6 of FT-LB075 please.", "QUOTE: sku=FT-LB075; qty=6")
        self.assertIn("ANSWER: $56.40", out)
        self.assertIn("list price, no account level named", out)
        out = route(self.p, "Contractor account: price 12 of CV-4SQ-MR1 at contractor level.", "QUOTE: sku=CV-4SQ-MR1; qty=12")
        self.assertIn("ANSWER: $15.31", out)
        self.assertIn("contractor level", evals.final_answer(out))

    def test_a_customer_note_names_the_level(self):
        r = actions.load_pricing(ROPE)
        self.assertEqual(actions.account_level(r, "Pier 9 needs 4 turnbuckles"), "marina")
        out = route(r, "Pier 9 needs 4 turnbuckles", "QUOTE: sku=TB-1; qty=4")
        self.assertIn("ANSWER: $13.60", out)  # 16.00 - 15%

    def test_an_unknown_level_is_not_priced(self):
        self.assertIsNone(actions.quote(self.p, "PB1-20", 6, level="platinum")[0])


class Synonyms(unittest.TestCase):
    def setUp(self):
        self.p = actions.load_pricing(PONCE / "vault")

    def test_shop_shorthand_from_the_note(self):
        x = lambda s: actions.expand_synonyms(self.p, s)
        self.assertEqual(x("6 sp 20a breakers"), "6 1-pole 20a plug-on breaker")
        self.assertEqual(x("75' of 10/2 nm w/ground"), "75' of 10/2 NM-B w/ground")
        self.assertEqual(x("qty 40 2p 30a breakers"), "qty 40 2-pole 30a plug-on breaker")
        self.assertEqual(x("pls price 200 ft of 3/4 emt"), "pls price 200 ft of EMT conduit 3/4in")
        self.assertEqual(x("12 plug-on breakers"), "12 plug-on breakers")  # never rewrites inside a word or twice

    def test_separators_are_loose_and_longest_first(self):
        r = actions.load_pricing(ROPE)
        self.assertEqual(actions.expand_synonyms(r, "40 m polyester-line"), "40 m polyester rope")
        self.assertEqual(actions.expand_synonyms(r, "40 m poly"), "40 m polyester rope")

    def test_empty_template_and_no_trade_words_in_code(self):
        self.assertEqual(actions.load_pricing(EX.parent / "profile/vault")["synonyms"], [])
        code = " ".join((EX.parent / "staffbox" / f).read_text().lower() for f in ("actions.py", "evals.py"))
        code = re.sub(r"#.*", "", re.sub(r'"""[\s\S]*?"""', "", code))  # docstrings and comments may give examples
        for w in ["thhn", "romex", "nm-b", "breaker", "emt", "conduit", "receptacle", "wire nut", "copper", "contractor"]:
            self.assertNotRegex(code, rf"\b{re.escape(w)}\b", w)

    def test_multi_line_shorthand_is_supported(self):
        out = route(self.p, "need 250' 12-2 nm-b and 6 sp 20a breakers. thx", "QUOTE: sku=W-NM12-2; qty=250\nQUOTE: sku=PB1-20; qty=6")
        self.assertIn("ANSWER: $251.40", out)


class SpecialOrder(unittest.TestCase):
    def setUp(self):
        self.p = actions.load_pricing(PONCE / "vault")

    def test_flag_column(self):
        self.assertFalse(self.p["skus"]["PG2-50"]["stock"])
        self.assertTrue(self.p["skus"]["PB2-50"]["stock"])
        self.assertIsNone(actions.quote(self.p, "PG2-50", 4)[0])
        self.assertFalse(actions.load_pricing(ROPE)["skus"]["CH-8"]["stock"])

    def test_declined_and_asked_never_priced(self):
        out = route(self.p, "price a 200A 40 space panel, outdoor (rainproof)", "QUOTE: sku=LC-200-40-OD; qty=1")
        self.assertIn("NOT IN VAULT", evals.final_answer(out))
        self.assertIn("special order", out)
        self.assertNotIn("$", evals.final_answer(out))
        out = route(self.p, "Quote 300 ft of 2 AWG THHN, black (W-THHN2-BK).", "QUOTE: sku=W-THHN2-BK; qty=300")
        self.assertIn("NOT IN VAULT", evals.final_answer(out))

    def test_router_sees_the_flag(self):
        seen = []
        real = evals.chat
        try:
            evals.chat = lambda h, m, msgs, *a, **k: (seen.append(msgs[0]["content"]) or "NONE", 0)
            evals.route_quote("", "", self.p, "price 4 PG2-50")
        finally:
            evals.chat = real
        self.assertIn("PG2-50 = 2-pole 50A GFCI plug-on breaker [ea] (special order)", seen[0])


class PackUnits(unittest.TestCase):
    def setUp(self):
        self.p = actions.load_pricing(PONCE / "vault")

    def test_pieces_to_boxes(self):
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 300, "300 yellow wire nuts")[0], 3)
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 3, "300 yellow wire nuts")[0], 3)  # model already converted
        self.assertEqual(actions.to_unit(self.p, "RC-15TR-10", 50, "50 15a TR duplex recepts")[0], 5)
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 300, "300 pcs yellow")[0], 3)

    def test_boxes_stay_boxes(self):
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 2, "2 boxes yellow wire nuts")[0], 2)
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 4, "Price 4 of WN-YL-100")[0], 4)  # the code names the box item

    def test_ambiguous_or_broken_box_is_asked(self):
        self.assertIsNone(actions.to_unit(self.p, "WN-YL-100", 25, "25 yellow wire nuts")[0])
        self.assertIsNone(actions.to_unit(self.p, "WN-YL-100", 250, "250 pcs yellow wire nuts")[0])
        self.assertIsNone(actions.to_unit(self.p, "RC-GF20", 2, "2 boxes of GFCI")[0])  # sold each

    def test_model_unit_hint_never_makes_a_box_from_a_product_name(self):
        self.assertEqual(actions.to_unit(self.p, "WN-YL-100", 300, "300 yellow wire nuts", "box")[0], 3)
        self.assertEqual(actions.to_unit(self.p, "BX-1G-NW", 50, "50 single gang new work boxes + 50 recepts", "box")[0], 50)
        self.assertEqual(actions.to_unit(self.p, "W-THHN12-BK", 2, "2 reels #12 thhn", "reel")[0], 1000)

    def test_feet_to_sticks(self):
        self.assertEqual(actions.to_unit(self.p, "CD-EMT-075", 200, "200 ft of 3/4 emt")[0], 20)
        self.assertEqual(actions.to_unit(self.p, "CD-EMT-075", 20, "200 ft of 3/4 emt")[0], 20)
        self.assertEqual(actions.to_unit(self.p, "CD-EMT-075", 20, "20 sticks of 3/4 emt")[0], 20)
        self.assertIsNone(actions.to_unit(self.p, "CD-EMT-075", 205, "205 ft of 3/4 emt")[0])

    def test_quantity_break_counts_boxes(self):
        out = route(self.p, "300 yellow wire nuts", "QUOTE: sku=WN-YL-100; qty=300")
        self.assertIn("ANSWER: $29.40", out)  # 3 boxes, under 50: no break (was 300 boxes, $2,646.00)

    def test_other_trades_pack(self):
        r = actions.load_pricing(ROPE)
        self.assertEqual(actions.to_unit(r, "SH-6", 40, "40 shackles")[0], 2)
        self.assertIsNone(actions.to_unit(r, "SH-6", 30, "30 shackles")[0])


class PonceDevSet(unittest.TestCase):
    """With a correct model extraction, code prices every Ponce quote right and declines every ask (DEV set)."""
    MESSY = {"messy-01": "QUOTE: sku=W-NM12-2; qty=250; unit=ft\nQUOTE: sku=PB1-20; qty=6",
             "messy-02": "QUOTE: sku=WN-YL-100; qty=2; unit=box\nQUOTE: sku=WN-RD-100; qty=1; unit=box",
             "messy-03": "QUOTE: sku=CD-EMT-075; qty=200; unit=ft", "messy-04": "QUOTE: sku=LT-DL6; qty=60",
             "messy-05": "QUOTE: sku=W-THHN12-BK; qty=1000; unit=ft", "messy-06": "QUOTE: sku=W-NM12-2; qty=0\nQUOTE: sku=BX-1G-OW; qty=10",
             "messy-07": "QUOTE: sku=WN-YL-100; qty=300", "messy-08": "QUOTE: sku=LT-FP24; qty=8\nQUOTE: sku=LT-EXC; qty=2",
             "messy-09": "QUOTE: sku=PB2-30; qty=40", "messy-10": "QUOTE: sku=W-NM10-2; qty=75; unit=ft",
             "messy-11": "QUOTE: sku=W-SER4/0-AL; qty=150; unit=ft", "messy-12": "QUOTE: sku=BX-1G-NW; qty=50\nQUOTE: sku=RC-15TR-10; qty=50",
             "messy-13": "QUOTE: sku=LC-200-40-OD; qty=1", "messy-14": "QUOTE: sku=RC-GF20; qty=12\nQUOTE: sku=CV-WP-INUSE; qty=12",
             "messy-15": "QUOTE: sku=LT-HB150; qty=4\nQUOTE: sku=CD-EMT-050; qty=0"}

    def test_every_quote_and_ask(self):
        p = actions.load_pricing(PONCE / "vault")
        for t in map(json.loads, (PONCE / "tests-messy.jsonl").read_text().splitlines()):
            out = route(p, t["prompt"], self.MESSY[t["id"]])
            self.assertTrue(evals.grade(t, evals.final_answer(out)), f"{t['id']}: {out}")
        for t in map(json.loads, (PONCE / "tests.jsonl").read_text().splitlines()):
            if t["type"] != "quote":
                continue
            sku = re.search(r"\(([A-Z0-9/-]+)\)|of ([A-Z]{1,3}-[A-Z0-9/-]+)", t["prompt"])
            sku = (sku.group(1) or sku.group(2)) if sku else next(k for k, v in p["skus"].items() if v["desc"] in t["prompt"])
            qty = re.search(r"(\d+)\s*(?:ft|feet|x|of)\b", t["prompt"]).group(1)
            out = route(p, t["prompt"], f"QUOTE: sku={sku}; qty={qty}")
            self.assertTrue(evals.grade(t, evals.final_answer(out)), f"{t['id']}: {out}")


if __name__ == "__main__":
    unittest.main()
