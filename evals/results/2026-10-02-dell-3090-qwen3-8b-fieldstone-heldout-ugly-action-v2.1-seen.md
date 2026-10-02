# Scorecard: Fieldstone IT

Model `qwen3:8b` on Dell RTX 3090 running the 8B model a 16 GB Mac mini runs · 2026-10-02 · 20 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 15/17 (88%) |
| unknown | 3/3 (100%) |
| **all** | 18/20 (90%) |

Average seconds per answer: brain+quote 6.4s
90th-percentile seconds: brain+quote 60.6s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 16/17 (94%) | 15/16 (93%) | 15/17 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | ugly-16 | 44642.8 | $46,542.80 |
| brain+quote | ugly-17 | 1047.0 | NOT IN VAULT: item unclear. Ask the customer which model. |
