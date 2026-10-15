# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 9/10 (90%) |
| unknown | 5/5 (100%) |
| **all** | 14/15 (93%) |

Average seconds per answer: brain+quote 0.5s
90th-percentile seconds: brain+quote 0.8s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 9/10 (90%) | 9/9 (100%) | 9/10 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-09 | 104.75 | NOT IN VAULT: quantities unclear (possible double count). Ask the customer to confirm the  |
