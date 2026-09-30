"""Build tests.jsonl for the Peachtree demo brain. Answers are computed from the same numbers as the vault.

A real site's test set is 30 to 50 of its own past requests with the right answers; this is the fictional stand-in.
Usage: python3 make_tests.py > tests.jsonl
"""
import json, random

SKUS = {"SD-1824": ("shaker door 18x24", 42.00), "SD-2430": ("shaker door 24x30", 55.00), "SD-1530": ("shaker door 15x30", 47.50),
        "SL-1824": ("slab door 18x24", 31.00), "SL-2430": ("slab door 24x30", 39.00), "RP-1824": ("raised panel door 18x24", 58.00),
        "RP-2430": ("raised panel door 24x30", 71.00), "DB-1216": ("dovetail drawer box 12x16", 36.00), "DB-1822": ("dovetail drawer box 18x22", 44.00),
        "DF-0624": ("drawer front 6x24", 18.50), "DF-0830": ("drawer front 8x30", 22.00), "CM-0896": ("crown moulding 8ft", 27.00)}
SPECIES = {"poplar": 0.00, "maple": 0.10, "white oak": 0.18, "cherry": 0.25}
FINISH = {"unfinished": 0.00, "stained": 0.12, "painted": 0.20}
QUOTE_ASKS = ["Quote {q} x {d} ({sku}) in {s}, {f}. What is the line total?",
              "Customer wants {q} {d}s, {s}, {f}. How much for the line?",
              "Price {q} of {sku} in {s}, {f} please."]
LOOKUPS = [("How long does a painted order take?", ["20 business days"]),
           ("What's the lead time if the doors are unfinished?", ["10 business days"]),
           ("What is our minimum order?", ["$250"]),
           ("How much deposit do we take on a custom order?", ["50%"]),
           ("Who can approve a special price for a big customer?", ["plant manager"]),
           ("Can a customer return stock items, and within how long?", ["30 days"]),
           ("A contractor wants it faster. What does a rush cost?", ["25%"]),
           ("How far do we deliver for free?", ["50 miles"]),
           ("Which wood species do we stock?", ["poplar", "maple", "white oak", "cherry"]),
           ("An order has stained doors and painted drawer fronts. What lead time do we quote?", ["20 business days"])]
TRIAGE = [("Can you price 24 slab doors 18x24 in maple, stained?", "quote"),
          ("Where is PO-48213? It was due last week.", "order_status"),
          ("Order PO-55120 arrived with 4 cracked doors.", "complaint"),
          ("Our GC needs the CARB compliance cert for PO-31877.", "cert_request"),
          ("Are you hiring for the finishing line?", "other"),
          ("The finish on PO-60412 does not match the sample.", "complaint"),
          ("Checking ship date for PO-22904, customer is asking.", "order_status"),
          ("Please send the FSC certificate for PO-70155.", "cert_request")]
UNKNOWN = ["What is the price of a 30x36 shaker door?",
           "What warranty do we give on painted finishes?",
           "Can we ship an order to Toronto, and what does it cost?",
           "Is the plant open on Saturdays?",
           "Price 12 walnut shaker doors 18x24, stained.",
           "What does delivery cost to Savannah, 250 miles away?"]


def quote(r, i):
    sku = r.choice(list(SKUS)); d, p = SKUS[sku]; s = r.choice(list(SPECIES)); f = r.choice(list(FINISH))
    q = r.choice([6, 8, 12, 16, 20, 24, 25, 30, 40, 48, 50, 60, 75, 100])
    unit = round(p * (1 + SPECIES[s] + FINISH[f]), 2); line = round(unit * q, 2)
    disc = 0.08 if q >= 50 else 0.05 if q >= 25 else 0.0
    return dict(id=f"quote-{i:02d}", type="quote", prompt=r.choice(QUOTE_ASKS).format(q=q, d=d, sku=sku, s=s, f=f), expect=round(line * (1 - disc), 2))


r = random.Random(930)
tests = [quote(r, i + 1) for i in range(16)]
tests += [dict(id=f"lookup-{i+1:02d}", type="lookup", prompt=p, expect=e) for i, (p, e) in enumerate(LOOKUPS)]
tests += [dict(id=f"triage-{i+1:02d}", type="triage", prompt=f"Route this email to one queue.\n\n\"{p}\"", expect=e) for i, (p, e) in enumerate(TRIAGE)]
tests += [dict(id=f"unknown-{i+1:02d}", type="unknown", prompt=p, expect="NOT IN VAULT") for i, p in enumerate(UNKNOWN)]
for t in tests:
    print(json.dumps(t))
