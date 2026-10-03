"""Offline tests: no model needed. Run: python3 -m unittest discover -s tests"""
import pathlib, shutil, subprocess, tempfile, unittest
from staffbox import brain, evals

DEMO = pathlib.Path(__file__).parent.parent / "examples/peachtree-cabinet-works/vault"


class Brain(unittest.TestCase):
    def test_demo_brain_is_healthy(self):
        self.assertEqual(brain.check(DEMO), [])

    def test_fieldstone_brain_is_healthy(self):
        self.assertEqual(brain.check(DEMO.parent.parent / "fieldstone-it/vault"), [])

    def test_template_brain_is_healthy(self):
        self.assertEqual(brain.check(DEMO.parent.parent.parent / "profile/vault"), [])

    def test_retrieval_finds_the_right_note(self):
        cases = {"How long does a painted order take?": "policies/lead-times.md",
                 "What is our minimum order?": "policies/orders-and-deposits.md",
                 "Price 20 of DB-1822 in poplar, stained please.": "price-list.md",
                 "Route this email: please send the FSC certificate": "sops/route-an-email.md"}
        for q, want in cases.items():
            _, picked = brain.context(DEMO, q)
            self.assertIn(want, picked, q)

    def test_company_note_always_first(self):
        _, picked = brain.context(DEMO, "anything at all")
        self.assertEqual(picked[0], "company.md")

    def test_check_catches_broken_link_and_missing_fields(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(DEMO, d, dirs_exist_ok=True)
            (pathlib.Path(d) / "bad.md").write_text("---\ntype: sop\n---\nSee [[nowhere]].\n")
            problems = "\n".join(brain.check(d))
            self.assertIn("broken link [[nowhere]]", problems)
            self.assertIn("missing 'owner'", problems)

    def test_obsidian_block_list_frontmatter(self):
        meta, body, err = brain.parse_frontmatter("---\ntype: sop\naliases:\n  - Home\n  - Index\nowner: ops\n---\nBody\n")
        self.assertIsNone(err)
        self.assertEqual(meta["aliases"], ["Home", "Index"])
        self.assertEqual(meta["owner"], "ops")
        self.assertEqual(body, "Body\n")
        _, _, err = brain.parse_frontmatter("---\ntype: sop\n  - stray\n---\n")
        self.assertIn("bad frontmatter line", err)

    def test_log_is_append_only_under_git(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copytree(DEMO, d, dirs_exist_ok=True)
            git = lambda *a: subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
            git("init", "-q"); git("add", "."); git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "seed")
            brain.append_log(d, "quote 20 DB-1822", "answered $985.60")
            self.assertEqual(brain.check_log_append_only(d), [])
            log = pathlib.Path(d) / "log.md"
            log.write_text(log.read_text().replace("vault created", "vault rewritten"))
            self.assertTrue(brain.check_log_append_only(d))


class Grading(unittest.TestCase):
    def test_calculator(self):
        self.assertEqual(evals.calc("55 * (1 + 0.10 + 0.20)"), 71.5)
        self.assertEqual(evals.calc("$2,145.00 * 0.95"), 2037.75)
        with self.assertRaises(Exception):
            evals.calc("__import__('os')")

    def test_grade(self):
        self.assertTrue(evals.grade({"type": "quote", "expect": 2037.75}, "$2,037.75"))
        self.assertFalse(evals.grade({"type": "quote", "expect": 2037.75}, "$2,145.00"))
        self.assertTrue(evals.grade({"type": "quote", "expect": 985.6}, "$985.60 (including 12% surcharge for stained finish)."))
        self.assertTrue(evals.grade({"type": "triage", "expect": "cert_request"}, "cert_request"))
        self.assertTrue(evals.grade({"type": "unknown", "expect": "NOT IN VAULT"}, "NOT IN VAULT, ask the plant manager"))
        self.assertTrue(evals.grade({"type": "lookup", "expect": ["20 business days"]}, "20 business days (painted)"))


if __name__ == "__main__":
    unittest.main()
