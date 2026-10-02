"""Offline tests for review, addtest, the pass-bar metrics and the draft-only inbox (no model: ask is faked)."""
import json, pathlib, shutil, tempfile, unittest
from staffbox import evals, inbox, review

FIELD = pathlib.Path(__file__).parent.parent / "examples/fieldstone-it/vault"


def row(id, ok, ans="$1.00", type="quote", mode="brain+quote"):
    return dict(id=id, ok=ok, answer=ans, type=type, mode=mode, expect=1.0, seconds=1.0)


class Review(unittest.TestCase):
    def test_diff_and_gate(self):
        prev = {r["id"]: r for r in [row("a", True), row("b", False), row("c", True)]}
        new = {r["id"]: r for r in [row("a", False), row("b", True), row("c", True), row("d", True)]}
        text, gate = review.review(new, prev, {"quote": 85})
        self.assertIn("1 fixed · **1 regressed** · 1 new tests", text)
        self.assertFalse(gate["quote"])  # 3/4 = 75% < 85%

    def test_addtest_never_edits(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "t.jsonl"
            review.add_test(p, "fix-01", "quote", "Quote 2 LT-14", "$2,488.00")
            self.assertEqual(json.loads(p.read_text())["expect"], 2488.0)
            with self.assertRaises(ValueError):
                review.add_test(p, "fix-01", "quote", "again", "1")


class PassBar(unittest.TestCase):
    def test_refusal_is_not_priced(self):
        rows = [row("a", True, "$10.00"), row("b", False, "NOT IN VAULT: ask"), row("c", False, "$9.00")]
        q = evals.quote_quality(rows)
        self.assertEqual((q["n"], q["priced"], q["right"]), (3, 2, 1))
        self.assertEqual(evals.p90([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 10)

    def test_spacing_is_not_an_error(self):
        self.assertTrue(evals.grade({"type": "lookup", "expect": ["25%"]}, "25 % of the order total"))
        self.assertTrue(evals.grade({"type": "lookup", "expect": ["sunday", "2 am"]}, "Sunday 2\u202fam to 5\u202fam."))

    def test_total_first_or_last(self):
        g = lambda a: evals.grade({"type": "quote", "expect": 5094.0}, a)
        self.assertTrue(g("$5,094.00 ($2,694.00 for the APs and $2,400.00 for the switch)"))
        self.assertTrue(g("unit $389.00, total $5,094.00"))
        self.assertFalse(g("$2,694.00 for the APs and $2,400.00 for the switch"))


class Inbox(unittest.TestCase):
    def test_drafts_only_and_cites_dated_pricing(self):
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            vault = d / "vault"; shutil.copytree(FIELD, vault)
            req = d / "in"; req.mkdir()
            (req / "r1.eml").write_text("From: Dana <dana@example.com>\nSubject: laptops\n\nPrice 2 LT-14 with setup?\n> old thread 99\n")
            seen = []
            def fake_ask(host, model, v, question, mode, company, num_ctx=None):
                seen.append(question)
                return "Quote action: 2 x LT-14.\nANSWER: $2,488.00", ["hardware-price-list.md"], 0, 1
            made = inbox.run(vault, req, d / "drafts", "h", "m", "Fieldstone IT", ask=fake_ask)
            draft = made[0].read_text()
            self.assertIn("To: Dana <dana@example.com>", draft)
            self.assertIn("Subject: Re: laptops", draft)
            self.assertIn("Total: $2,488.00", draft)
            self.assertIn("Hi Dana,", draft)
            self.assertIn("hardware-price-list.md (updated 2026-09-30)", draft)
            self.assertNotIn("99", seen[0])  # quoted history stripped
            self.assertTrue((req / "done" / "r1.eml").exists())
            self.assertIn("not sent: a person sends", (vault / "log.md").read_text())
            self.assertFalse(hasattr(inbox, "smtplib"))  # no sending code


if __name__ == "__main__":
    unittest.main()


class QuoteDesk(unittest.TestCase):
    def setUp(self):
        from staffbox import actions
        self.a, self.P = actions, actions.load_pricing(FIELD)

    def test_words_and_descriptions(self):
        self.assertIn("24", self.a.words_to_digits("two dozen monitors"))
        self.assertIn("25", self.a.words_to_digits("twenty-five screens"))
        self.assertEqual(self.a.match_description(self.P, "the 24 port poe switches"), "SW-24P")
        self.assertIsNone(self.a.match_description(self.P, "laptops"))  # two laptops on the list: ask, never guess
        self.assertIsNone(self.a.match_description(self.P, "MacBook Pros"))

    def test_no_setup(self):
        t, work = self.a.quote(self.P, "DOCK-C", 50, {"setup": "no"})
        self.assertEqual(t, 10183.5)
        self.assertIn("no setup", work)

    def test_multi_item_route(self):
        from unittest import mock
        reply = "QUOTE: sku=AP-6E; qty=5; setup=yes\nQUOTE: sku=24 port poe switch; qty=1; setup=yes"
        with mock.patch.object(evals, "chat", return_value=(reply, 10)):
            out, _, calls = evals.route_quote("h", "m", self.P, "Need 5 AP-6E and 1 switch, installed.")
        self.assertIn("ANSWER: $3,445.00 (2 lines)", out)
        self.assertEqual(calls, 2)

    def test_double_count_escalates(self):
        from unittest import mock
        reply = "QUOTE: sku=LT-14; qty=40; setup=yes\nQUOTE: sku=LT-14; qty=40; setup=no"
        with mock.patch.object(evals, "chat", return_value=(reply, 5)):
            out, _, _ = evals.route_quote("h", "m", self.P, "Quote 40 of the 14 inch laptops, half with setup and half without.")
        self.assertIn("NOT IN VAULT", out)

    def test_unclear_escalates(self):
        from unittest import mock
        with mock.patch.object(evals, "chat", return_value=("UNCLEAR", 3)):
            out, _, _ = evals.route_quote("h", "m", self.P, "Same laptops as last time, 8 of them.")
        self.assertIn("NOT IN VAULT", out)


class Guards(unittest.TestCase):
    def setUp(self):
        from staffbox import actions
        self.a, self.P = actions, actions.load_pricing(FIELD)

    def test_supported(self):
        s = lambda t, k: self.a.supported(self.P, t, k)
        self.assertTrue(s("hey can u price LT14 x 40", "LT-14"))
        self.assertTrue(s("40 of the 14 inch laptops", "LT-14"))
        self.assertFalse(s("Same laptops as last time, 8 of them", "LT-14"))
        self.assertTrue(s("price for 30 usb-c docks", "DOCK-C"))
        self.assertTrue(s("Pls quote 100 24in screens", "MON-24"))
        self.assertTrue(s("a firewall for the new office", "FW-SMB"))
        self.assertTrue(s("need 3 UPS units asap, installed", "UPS-1500"))
        self.assertTrue(s("Client wants 20 business laptop 16ins, set up", "LT-16"))
        PT = self.a.load_pricing(FIELD.parent.parent / "peachtree-cabinet-works/vault")
        self.assertTrue(self.a.supported(PT, "Customer wants 60 slab door 24x30s, cherry", "SL-2430"))
        self.assertTrue(self.a.supported(PT, "Quote 30 x shaker door 24x30 (SD-2430)", "SD-2430"))
        self.assertFalse(self.a.supported(PT, "Quote 30 doors in cherry", "SD-2430"))  # "ups" must not become "up"

    def test_setup_only_dropped_when_said(self):
        self.assertTrue(self.a.says_no_setup("We will image them ourselves, so no setup."))
        self.assertTrue(self.a.says_no_setup("Just the hardware please"))
        self.assertFalse(self.a.says_no_setup("price for 30 usb-c docks"))

    def test_route_restores_setup(self):
        from unittest import mock
        with mock.patch.object(evals, "chat", return_value=("QUOTE: sku=DOCK-C; qty=30; setup=no", 5)):
            out, _, _ = evals.route_quote("h", "m", self.P, "price for 30 usb-c docks")
        self.assertIn("$6,410.10", out)
