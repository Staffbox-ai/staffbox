# Scorecard: Fieldstone IT

Model `qwen3:8b` on Dell RTX 3090 running the 8B model a 16 GB Mac mini runs · 2026-10-02 · 20 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 16/17 (94%) |
| unknown | 3/3 (100%) |
| **all** | 19/20 (95%) |

Average seconds per answer: brain+quote 0.6s
90th-percentile seconds: brain+quote 1.1s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 17/17 (100%) | 16/17 (94%) | 16/17 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | ugly-16 | 44642.8 | $93,085.60 (2 lines) |
