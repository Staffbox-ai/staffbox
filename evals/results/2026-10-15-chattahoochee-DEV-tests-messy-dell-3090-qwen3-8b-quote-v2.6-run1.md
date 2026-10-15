# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 7/10 (70%) |
| unknown | 4/5 (80%) |
| **all** | 11/15 (73%) |

Average seconds per answer: brain+quote 0.7s
90th-percentile seconds: brain+quote 1.2s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 10/10 (100%) | 7/10 (70%) | 7/10 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | messy-02 | 372.0 | $198.00 (2 lines; list price, no account level named) |
| brain+quote | messy-06 | NOT IN VAULT | $9,760.00 (2 lines; list price, no account level named) |
| brain+quote | messy-09 | 104.75 | $67.50 (2 lines; list price, no account level named) |
| brain+quote | messy-11 | 194.4 | $415.20 (4 lines; list price, no account level named) |
