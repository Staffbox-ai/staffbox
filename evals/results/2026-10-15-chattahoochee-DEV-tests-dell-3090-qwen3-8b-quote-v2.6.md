# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 16/16 (100%) |
| lookup | 9/10 (90%) |
| triage | 8/8 (100%) |
| unknown | 5/6 (83%) |
| **all** | 38/40 (95%) |

Average seconds per answer: brain+quote 0.6s
90th-percentile seconds: brain+quote 1.0s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 16/16 (100%) | 16/16 (100%) | 16/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | lookup-06 | ['6:00', '5:00'] | Monday to Friday 6:00 am to 5,00 pm. |
| brain+quote | unknown-02 | NOT IN VAULT | warranty coordinator |
