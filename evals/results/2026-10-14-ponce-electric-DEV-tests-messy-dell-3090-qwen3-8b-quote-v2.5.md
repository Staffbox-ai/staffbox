# Scorecard: Ponce Electric Supply

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 10/11 (90%) |
| unknown | 3/4 (75%) |
| **all** | 13/15 (86%) |

Average seconds per answer: brain+quote 0.4s
90th-percentile seconds: brain+quote 0.5s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 10/11 (90%) | 10/10 (100%) | 10/11 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-08 | 565.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | messy-15 | NOT IN VAULT | $519.20 (2 lines; list price, no account level named) |
