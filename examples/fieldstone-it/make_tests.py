"""Build tests.jsonl for the Fieldstone IT demo brain. Answers are computed from the same numbers as the vault.

A real IT provider's test set is 30 to 50 of its own past requests with the right answers; this is the fictional stand-in.
Usage: python3 make_tests.py > tests.jsonl
"""
import json, random

SKUS = {"LT-14": ("business laptop 14in", 1149.00, 95.00), "LT-16": ("business laptop 16in", 1399.00, 95.00),
        "DT-MINI": ("small desktop", 899.00, 95.00), "MON-24": ("monitor 24in", 219.00, 15.00), "MON-27": ("monitor 27in", 289.00, 15.00),
        "DOCK-C": ("USB-C dock", 219.00, 10.00), "AP-6E": ("Wi-Fi 6E access point", 389.00, 60.00), "SW-24P": ("24-port PoE switch", 1050.00, 150.00),
        "FW-SMB": ("small-business firewall", 1250.00, 250.00), "UPS-1500": ("battery backup 1500VA", 329.00, 20.00)}
QUOTE_ASKS = ["Quote {q} x {d} ({sku}) with setup. What is the line total?",
              "Client wants {q} {d}s, set up and ready. How much for the line?",
              "Price {q} of {sku} including setup please."]
LOOKUPS = [("A whole office is down. How fast do we have to respond?", ["15 minutes"]),
           ("What do we charge per hour for after-hours work?", ["$225"]),
           ("What's our business-hours project rate?", ["$165"]),
           ("How long do we keep backups?", ["30 days"]),
           ("When is the server maintenance window?", ["sunday", "2 am"]),
           ("A user lost their phone and is locked out of MFA. What is the first step?", ["call"]),
           ("How quickly must we disable an account after a leaver request?", ["1 hour"]),
           ("Who approves a quote over $10,000?", ["service director"]),
           ("How much notice do we need for a new starter?", ["3 business days"]),
           ("Brightwater Dental wants a firewall rule changed today. What do we need first?", ["change ticket"])]
TRIAGE = [("The printer on the second floor keeps jamming and now shows an error.", "service_desk"),
          ("Can you price 8 new laptops and docks for our new hires?", "quote"),
          ("I clicked a link in an email that said my mailbox was full and entered my password.", "security"),
          ("We have a new paralegal starting Monday, Ana Ruiz.", "onboarding"),
          ("Our September invoice looks like it charged us twice.", "billing"),
          ("Outlook won't open on my laptop since this morning.", "service_desk"),
          ("Jim left the company today, please shut off his access.", "onboarding"),
          ("Do you sponsor the chamber of commerce golf day?", "other")]
UNKNOWN = ["What is the price of a 34in ultrawide monitor?",
           "Do we support Linux desktops for clients?",
           "What is the warranty on the LT-14 laptop?",
           "Does Morrow & Pike have a backup internet line?",
           "Price 20 iPads with setup.",
           "What response time do we promise clients outside Georgia?"]


def quote(r, i):
    sku = r.choice(list(SKUS)); d, p, setup = SKUS[sku]
    q = r.choice([2, 3, 5, 6, 8, 10, 12, 15, 20, 24, 25, 30, 40, 50])
    disc = 0.07 if q >= 25 else 0.04 if q >= 10 else 0.0
    hw = round(q * p * (1 - disc), 2)
    return dict(id=f"quote-{i:02d}", type="quote", prompt=r.choice(QUOTE_ASKS).format(q=q, d=d, sku=sku), expect=round(hw + q * setup, 2))


r = random.Random(1001)
tests = [quote(r, i + 1) for i in range(16)]
tests += [dict(id=f"lookup-{i+1:02d}", type="lookup", prompt=p, expect=e) for i, (p, e) in enumerate(LOOKUPS)]
tests += [dict(id=f"triage-{i+1:02d}", type="triage", prompt=f"Route this email to one queue.\n\n\"{p}\"", expect=e) for i, (p, e) in enumerate(TRIAGE)]
tests += [dict(id=f"unknown-{i+1:02d}", type="unknown", prompt=p, expect="NOT IN VAULT") for i, p in enumerate(UNKNOWN)]
for t in tests:
    print(json.dumps(t))
