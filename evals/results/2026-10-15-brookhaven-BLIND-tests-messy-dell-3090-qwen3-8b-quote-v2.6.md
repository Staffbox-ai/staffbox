# Scorecard: Brookhaven Lumber & Building Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 1/11 (9%) |
| unknown | 3/4 (75%) |
| **all** | 4/15 (26%) |

Average seconds per answer: brain+quote 0.4s
90th-percentile seconds: brain+quote 0.8s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 5/11 (45%) | 1/5 (20%) | 1/11 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-01 | 1140.78 | $1,158.00 (2 lines; list price, no account level named) |
| brain+quote | messy-02 | 253.96 | $248.60 (2 lines; list price, no account level named) |
| brain+quote | messy-03 | 232.8 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-04 | 1333.42 | NOT IN VAULT: 1 inch thick red is not on the price list (we stock: ). Ask the customer whe |
| brain+quote | messy-06 | 1050.17 | NOT IN VAULT: item or quantity unclear. Ask the customer which model and how many. |
| brain+quote | messy-07 | 298.0 | $322.50 (1 line; list price, no account level named) |
| brain+quote | messy-08 | 732.66 | NOT IN VAULT: 0 in wide door is not on the price list (we stock: pressure-treated plywood  |
| brain+quote | messy-10 | 82.79 | NOT IN VAULT: item or quantity unclear. Ask the customer which model and how many. |
| brain+quote | messy-13 | 396.54 | $333.30 (2 lines; list price, no account level named) |
| brain+quote | messy-14 | NOT IN VAULT | $438.00 (1 line; list price, no account level named) |
| brain+quote | messy-15 | 681.76 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
