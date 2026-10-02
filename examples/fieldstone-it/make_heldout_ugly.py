"""Held-out "ugly" requests for the Fieldstone brain: the way quote requests really arrive.

Never used while building the quote action. Expected totals are computed by code from the vault's own price
list (staffbox.actions.quote), not typed by hand. Some cases are beyond the current product on purpose
(two items in one request, "no setup", half-and-half): they stay in the set so the score shows it.
Usage: python3 make_heldout_ugly.py > tests-heldout-ugly.jsonl
"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from staffbox import actions

P = actions.load_pricing(pathlib.Path(__file__).parent / "vault")
q = lambda sku, n: actions.quote(P, sku, n)[0]
hw = lambda sku, n: round(round(P["skus"][sku]["price"] * n, 2) * (1 - next(d for lo, hi, d in P["tiers"] if lo <= n <= hi)), 2)

CASES = [
  ("typo-sku", "hey can u price LT14 x 40 w/ setup thx", q("LT-14", 40)),
  ("word-qty", "Need two dozen 27 inch monitors, set up please.", q("MON-27", 24)),
  ("forwarded", "---------- Forwarded message ---------\nFrom: Dana Ruiz\nDate: Tue, Sep 29, 2026\nSubject: RE: refresh\n\nWe bought 10 laptops in 2024.\n\nCan we get 15 of the 16in laptops set up for the new team?", q("LT-16", 15)),
  ("no-setup", "Quote 12 DT-MINI. We will image them ourselves, so no setup.", hw("DT-MINI", 12)),
  ("two-items", "Need 5 AP-6E and 1 SW-24P for the warehouse, installed.", round(q("AP-6E", 5) + q("SW-24P", 1), 2)),
  ("plain-words", "price for 30 usb-c docks", q("DOCK-C", 30)),
  ("ambiguous", "Same laptops as last time, 8 of them please.", "NOT IN VAULT"),
  ("not-stocked", "How much for 10 MacBook Pros, set up?", "NOT IN VAULT"),
  ("one-unit", "We need a firewall for the new office, just the one, installed.", q("FW-SMB", 1)),
  ("old-price", "Can you do 25 x UPS-1500 at last year's price of $299?", q("UPS-1500", 25)),
  ("screens", "Pls quote 100 24in screens + setup", q("MON-24", 100)),
  ("two-items-words", "Need a quote: 6 access points (the wifi 6e ones) and 2 of the 24 port poe switches.", round(q("AP-6E", 6) + q("SW-24P", 2), 2)),
  ("bundle", "Ballpark for outfitting 12 new hires with a laptop, a dock and 2 monitors each?", "NOT IN VAULT"),
  ("lowercase", "quote 9 lt-16", q("LT-16", 9)),
  ("thread", "Re: Re: Re: order\n\nAll good on our side. What's the total for the 18 small desktops we discussed?\n\nThanks, M", q("DT-MINI", 18)),
  ("half-half", "Quote 40 of the 14 inch laptops, half with setup and half without.", round(hw("LT-14", 40) + 20 * P["skus"]["LT-14"]["setup"], 2)),
  ("rush", "need 3 UPS units asap, installed", q("UPS-1500", 3)),
  ("three-items", "Quote: 1 x FW-SMB, 1 x SW-24P, 4 x AP-6E for the Buckhead office", round(q("FW-SMB", 1) + q("SW-24P", 1) + q("AP-6E", 4), 2)),
  ("signature-numbers", "Can you price 20 MON-24 with setup?\n\nMarcus Bell | Office Manager\nPeachtree Dental, Suite 300\n404-555-0142", q("MON-24", 20)),
  ("discount-ask", "Quote 10 x LT-14 with setup. Client is a nonprofit, any extra discount?", q("LT-14", 10)),
]
for i, (tag, prompt, exp) in enumerate(CASES, 1):
    kind = "unknown" if exp == "NOT IN VAULT" else "quote"
    print(json.dumps(dict(id=f"ugly-{i:02d}", type=kind, tag=tag, prompt=prompt, expect=exp)))
