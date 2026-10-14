# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 2/10 (20%) |
| unknown | 3/5 (60%) |
| **all** | 5/15 (33%) |

Average seconds per answer: brain+quote 0.6s
90th-percentile seconds: brain+quote 1.3s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 6/10 (60%) | 2/6 (33%) | 2/10 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-01 | 299.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-02 | 372.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-04 | 2119.05 | $2,493.00 (2 lines; list price, no account level named) |
| brain+quote | messy-06 | NOT IN VAULT | $19,520.00 (1 line; list price, no account level named) |
| brain+quote | messy-07 | 872.5 | $681.60 (1 line; list price, no account level named) |
| brain+quote | messy-08 | NOT IN VAULT | $619.20 (1 line; list price, no account level named) |
| brain+quote | messy-09 | 104.75 | $100.70 (1 line; list price, no account level named) |
| brain+quote | messy-11 | 194.4 | $415.20 (4 lines; list price, no account level named) |
| brain+quote | messy-13 | 213.84 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-14 | 127.7 | NOT IN VAULT: CP-L075-30 is not on the price list: special or custom order, not priced her |
