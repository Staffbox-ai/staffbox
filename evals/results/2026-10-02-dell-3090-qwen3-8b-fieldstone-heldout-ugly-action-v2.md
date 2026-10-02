# Scorecard: Fieldstone IT

Model `qwen3:8b` on Dell RTX 3090 running the 8B model a 16 GB Mac mini runs · 2026-10-02 · 20 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 10/17 (58%) |
| unknown | 1/3 (33%) |
| **all** | 11/20 (55%) |

Average seconds per answer: brain+quote 47.2s
90th-percentile seconds: brain+quote 351.9s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 17/17 (100%) | 10/17 (58%) | 10/17 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | ugly-06 | 6410.1 | $6,110.10 |
| brain+quote | ugly-07 | NOT IN VAULT | $9,192.00 |
| brain+quote | ugly-10 | 8149.25 | $7,649.25 |
| brain+quote | ugly-12 | 5094.0 | $4,434.00 (2 lines) |
| brain+quote | ugly-13 | NOT IN VAULT | $27,463.68 (4 lines) |
| brain+quote | ugly-14 | 13446.0 | $12,591.00 |
| brain+quote | ugly-15 | 17244.72 | $15,534.72 |
| brain+quote | ugly-16 | 44642.8 | $42,742.80 |
| brain+quote | ugly-18 | 4496.0 | $3,856.00 (3 lines) |
