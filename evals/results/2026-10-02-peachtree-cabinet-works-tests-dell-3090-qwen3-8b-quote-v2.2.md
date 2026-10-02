# Scorecard: Peachtree Cabinet Works

Model `qwen3:8b` on Dell RTX 3090 running the 8B model a 16 GB Mac mini runs · 2026-10-02 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 16/16 (100%) |
| lookup | 10/10 (100%) |
| triage | 7/8 (87%) |
| unknown | 6/6 (100%) |
| **all** | 39/40 (97%) |

Average seconds per answer: brain+quote 1.1s
90th-percentile seconds: brain+quote 1.7s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 16/16 (100%) | 16/16 (100%) | 16/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | triage-05 | other | NOT IN VAULT. Ask the office manager. |
