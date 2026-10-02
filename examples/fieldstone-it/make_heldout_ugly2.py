"""Second held-out set, written and committed BEFORE the quote action learned multi-item, no-setup and word
quantities (2 Oct 2026), so it measures that change without having been tuned to it. Same rules as
make_heldout_ugly.py: expected totals computed from the vault's price list.
Usage: python3 make_heldout_ugly2.py > tests-heldout-ugly2.jsonl
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from staffbox import actions

P = actions.load_pricing(pathlib.Path(__file__).parent / "vault")
q = lambda sku, n: actions.quote(P, sku, n)[0]
hw = lambda sku, n: round(round(P["skus"][sku]["price"] * n, 2) * (1 - next(d for lo, hi, d in P["tiers"] if lo <= n <= hi)), 2)

CASES = [
  ("dozen", "Could you price a dozen small desktops with setup?", q("DT-MINI", 12)),
  ("words-items", "We'd like three of the 24-port PoE switches and eight wifi 6E access points, installed.", round(q("SW-24P", 3) + q("AP-6E", 8), 2)),
  ("no-setup-2", "Just the hardware please, no setup: 30 MON-27.", hw("MON-27", 30)),
  ("battery", "need pricing on 6 battery backups (the 1500VA ones)", q("UPS-1500", 6)),
  ("desk-kit", "For each of 4 desks: one 27in monitor and one USB-C dock. Total?", round(q("MON-27", 4) + q("DOCK-C", 4), 2)),
  ("ticket-noise", "Ticket #48213 - Hi, please quote 11 LT-14 with setup. Our PO will reference 2026-118.", q("LT-14", 11)),
  ("not-stocked-2", "Do you have a 32in 4K monitor? Need 5.", "NOT IN VAULT"),
  ("vague", "Can we get some new laptops for the front desk?", "NOT IN VAULT"),
  ("hardware-only-words", "Price 50 docks, hardware only, we'll plug them in ourselves.", hw("DOCK-C", 50)),
  ("one-each", "One firewall and one switch (24 port PoE) for the clinic, set up.", round(q("FW-SMB", 1) + q("SW-24P", 1), 2)),
  ("dash-qty", "LT-16 - qty 26 - with setup", q("LT-16", 26)),
  ("spelled", "twenty-five 24in monitors with setup please", q("MON-24", 25)),
  ("model-number-noise", "Quote 7 AP-6E for building 3, floor 2.", q("AP-6E", 7)),
  ("mixed-setup", "10 LT-14 with setup and 10 DOCK-C without setup.", round(q("LT-14", 10) + hw("DOCK-C", 10), 2)),
  ("price-check-qty", "What would 2 FW-SMB cost installed? Last quote said $2,600.", q("FW-SMB", 2)),
]
for i, (tag, prompt, exp) in enumerate(CASES, 1):
    print(json.dumps(dict(id=f"ugly2-{i:02d}", type="unknown" if exp == "NOT IN VAULT" else "quote", tag=tag, prompt=prompt, expect=exp)))
