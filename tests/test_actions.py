"""Offline tests for the quote action: no model needed. Run: python3 -m unittest discover -s tests"""
import json, pathlib, re, unittest
from staffbox import actions

EX = pathlib.Path(__file__).parent.parent / "examples"


class Quote(unittest.TestCase):
    def test_engine_matches_every_expected_quote_in_both_demo_brains(self):
        for ex in ("peachtree-cabinet-works", "fieldstone-it"):
            pricing = actions.load_pricing(EX / ex / "vault")
            for t in map(json.loads, open(EX / ex / "tests.jsonl")):
                if t["type"] != "quote":
                    continue
                sku, qty, opts = actions.resolve(pricing, t["prompt"], "", 0, {})
                total, work = actions.quote(pricing, sku, qty, opts)
                self.assertAlmostEqual(total, t["expect"], places=2, msg=f"{ex} {t['id']}: {work}")

    def test_worked_examples_in_the_sops(self):
        p = actions.load_pricing(EX / "peachtree-cabinet-works/vault")
        self.assertEqual(actions.quote(p, "SD-2430", 30, {"species": "maple", "finish": "painted"})[0], 2037.75)
        f = actions.load_pricing(EX / "fieldstone-it/vault")
        self.assertEqual(actions.quote(f, "MON-27", 12)[0], 3509.28)

    def test_refuses_what_is_not_priced(self):
        p = actions.load_pricing(EX / "peachtree-cabinet-works/vault")
        self.assertIsNone(actions.quote(p, "SD-3036", 4)[0])
        self.assertIsNone(actions.quote(p, "SD-1824", 12, {"species": "walnut"})[0])
        sku, qty, opts = actions.resolve(p, "Price 12 walnut shaker doors 18x24, stained.", "", 0, {})
        self.assertIsNone(actions.quote(p, sku, qty, opts)[0])  # walnut is not a stocked species: never priced as poplar

    def test_resolve_ignores_sizes_and_fixes_a_missing_label(self):
        p = actions.load_pricing(EX / "peachtree-cabinet-works/vault")
        self.assertEqual(actions.resolve(p, "Customer wants 24 shaker door 24x30s, maple, stained.", "SD-2430", 2, {})[1], 24)
        self.assertEqual(actions.parse_quote_line("AP-6E; qty=40")[:2], ("AP-6E", 40))


class Unstocked(unittest.TestCase):
    """5 Oct Mac mini run: all 6 wrong totals were an unstocked spec priced as the nearest stocked item."""
    MISSES = {"fieldstone-it": ["gen-028", "gen-078", "gen-081"], "peachtree-cabinet-works": ["gen-023", "gen-040", "gen-099"]}

    def test_flags_every_substitution_miss_and_no_priced_test(self):
        for ex, ids in self.MISSES.items():
            pricing = actions.load_pricing(EX / ex / "vault")
            for f in sorted((EX / ex).glob("tests*.jsonl")):
                for t in map(json.loads, open(f)):
                    hit = actions.unstocked(pricing, t["prompt"])
                    if f.name == "tests-generated.jsonl" and t["id"] in ids:
                        self.assertTrue(hit, f"{ex} {t['id']} not flagged")
                    elif isinstance(t["expect"], (int, float)):
                        self.assertFalse(hit, f"{ex} {f.name} {t['id']} flagged: {hit}")

    def test_examples(self):
        f = actions.load_pricing(EX / "fieldstone-it/vault")
        p = actions.load_pricing(EX / "peachtree-cabinet-works/vault")
        self.assertEqual(actions.unstocked(f, "Do you have a 1000VA battery backup?")[0][1], ["battery backup 1500VA"])
        self.assertFalse(actions.unstocked(f, "5 of the 16 inch laptops and 5 of the 27 inch monitors"))
        self.assertTrue(actions.unstocked(p, "Can you do 10 ft crown moulding, maple?"))
        self.assertFalse(actions.unstocked(p, "20 shaker doors 15x30, cherry, painted"))  # shaker 15x30 is stocked; slab is not
        self.assertTrue(actions.unstocked(p, "20 slab doors 15x30, cherry, painted"))

    def test_route_quote_flags_instead_of_substituting(self):
        from staffbox import evals
        f = actions.load_pricing(EX / "fieldstone-it/vault")
        p = actions.load_pricing(EX / "peachtree-cabinet-works/vault")
        real = evals.chat
        try:
            evals.chat = lambda *a, **k: ("QUOTE: sku=LT-16; qty=5; setup=yes\nQUOTE: sku=UPS-1500; qty=2; setup=yes", 0)
            out, _, _ = evals.route_quote("", "", f, "We need 5 of the 16 inch laptops. Also, do you have a 1000VA battery backup? We need 2.")
            self.assertIn("NOT IN VAULT: 1000VA battery backup is not on the price list", out)
            self.assertNotIn("UPS-1500 at", out)
            evals.chat = lambda *a, **k: ("QUOTE: sku=SL-2430; qty=25; species=white oak; finish=painted; setup=yes\n"
                                          "QUOTE: sku=SD-1530; qty=1; species=white oak; finish=painted; setup=yes", 0)
            out, _, _ = evals.route_quote("", "", p, "I need 25 slab doors 24x30, white oak, painted. Also, any 15x30 slab doors? "
                                                       "If not, just quote the 24x30s.")
            self.assertTrue(evals.grade({"type": "quote", "expect": 1278.22}, evals.final_answer(out)), out)
            self.assertIn("not quoted, not stocked: 15x30 slab doors", out)
        finally:
            evals.chat = real


if __name__ == "__main__":
    unittest.main()
