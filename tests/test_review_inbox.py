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
