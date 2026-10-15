# Scorecard: Brookhaven Lumber & Building Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 0/11 (0%) |
| unknown | 3/4 (75%) |
| **all** | 3/15 (20%) |

Average seconds per answer: brain+quote 0.3s
90th-percentile seconds: brain+quote 0.5s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 0/11 (0%) | 0/0 (0%) | 0/11 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-01 | 1140.78 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-02 | 253.96 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-03 | 232.8 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-04 | 1333.42 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-06 | 1050.17 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-07 | 298.0 | NOT IN VAULT: item or quantity unclear. Ask the customer which model and how many. |
| brain+quote | messy-08 | 732.66 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-09 | 214.4 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-10 | 82.79 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-11 | NOT IN VAULT | $1,167.00 |
| brain+quote | messy-13 | 396.54 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-15 | 681.76 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
