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
            self.assertIn("$2,488.00", draft)
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

    def test_unclear_escalates(self):
        from unittest import mock
        with mock.patch.object(evals, "chat", return_value=("UNCLEAR", 3)):
            out, _, _ = evals.route_quote("h", "m", self.P, "Same laptops as last time, 8 of them.")
        self.assertIn("NOT IN VAULT", out)
