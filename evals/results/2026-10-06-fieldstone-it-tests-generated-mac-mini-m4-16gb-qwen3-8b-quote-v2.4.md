# Scorecard: Fieldstone IT

Model `qwen3:8b` on Mac mini M4 16 GB (Staffbox-Zero) · 2026-10-06 · 204 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 183/186 (98%) |
| unknown | 18/18 (100%) |
| **all** | 201/204 (98%) |

Average seconds per answer: brain+quote 1.6s
90th-percentile seconds: brain+quote 2.1s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 183/186 (98%) | 183/183 (100%) | 183/186 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | gen-040 | 1006.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | gen-145 | 1166.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | gen-159 | 30295.31 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
