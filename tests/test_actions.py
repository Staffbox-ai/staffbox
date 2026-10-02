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


if __name__ == "__main__":
    unittest.main()
