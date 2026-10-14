# Scorecard: Ponce Electric Supply

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 0/11 (0%) |
| unknown | 2/4 (50%) |
| **all** | 2/15 (13%) |

Average seconds per answer: brain+quote 0.3s
90th-percentile seconds: brain+quote 0.4s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 2/11 (18%) | 0/2 (0%) | 0/11 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-01 | 251.4 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-02 | 32.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-03 | 262.0 | NOT IN VAULT: 200 ft of is not on the price list (we stock: EMT conduit 1/2in, 10 ft stick |
| brain+quote | messy-04 | 576.84 | $655.50 |
| brain+quote | messy-05 | 259.2 | NOT IN VAULT: 1000ft is not on the price list (we stock: THHN 14 AWG stranded copper, blac |
| brain+quote | messy-07 | 29.4 | $2,646.00 |
| brain+quote | messy-08 | 565.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-09 | 700.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-10 | 107.94 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-11 | NOT IN VAULT | $413.25 |
| brain+quote | messy-12 | 106.7 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-13 | NOT IN VAULT | $13,680.00 |
| brain+quote | messy-14 | 324.19 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
