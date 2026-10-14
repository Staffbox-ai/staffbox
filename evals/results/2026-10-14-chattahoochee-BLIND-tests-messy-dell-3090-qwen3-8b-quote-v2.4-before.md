# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 0/10 (0%) |
| unknown | 3/5 (60%) |
| **all** | 3/15 (20%) |

Average seconds per answer: brain+quote 0.3s
90th-percentile seconds: brain+quote 0.6s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 1/10 (10%) | 0/1 (0%) | 0/10 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-01 | 299.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-02 | 372.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-03 | 42.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-04 | 2119.05 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-05 | 3681.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-06 | NOT IN VAULT | $19,520.00 |
| brain+quote | messy-07 | 872.5 | $681.60 |
| brain+quote | messy-09 | 104.75 | NOT IN VAULT: 45 ft is not on the price list (we stock: type M hard copper pipe 1/2in, 10  |
| brain+quote | messy-11 | 194.4 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-12 | NOT IN VAULT | $3,498.00 |
| brain+quote | messy-13 | 213.84 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-14 | 127.7 | NOT IN VAULT: item or quantity unclear. Ask the customer which model and how many. |
