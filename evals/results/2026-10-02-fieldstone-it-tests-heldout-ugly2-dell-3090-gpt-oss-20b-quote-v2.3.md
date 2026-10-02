# Scorecard: Fieldstone IT

Model `gpt-oss-20b-64k` on Dell RTX 3090 (gpt-oss-20b, OpenAI open-weight, Apache 2.0) · 2026-10-02 · 15 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 13/13 (100%) |
| unknown | 2/2 (100%) |
| **all** | 15/15 (100%) |

Average seconds per answer: brain+quote 29.4s
90th-percentile seconds: brain+quote 193.7s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 13/13 (100%) | 13/13 (100%) | 13/13 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
