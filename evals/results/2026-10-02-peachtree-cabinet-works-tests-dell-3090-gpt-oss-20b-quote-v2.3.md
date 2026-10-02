# Scorecard: Peachtree Cabinet Works

Model `gpt-oss-20b-64k` on Dell RTX 3090 (gpt-oss-20b, OpenAI open-weight, Apache 2.0) · 2026-10-02 · 40 tests per mode · graded automatically, no human edits. Re-graded 2 Oct 2026: spacing differences ('25 %', non-breaking spaces) no longer count as errors.

| Task type | brain+quote |
|---|---|
| quote | 16/16 (100%) |
| lookup | 10/10 (100%) |
| triage | 8/8 (100%) |
| unknown | 6/6 (100%) |
| **all** | 40/40 (100%) |

Average seconds per answer: brain+quote 13.9s
90th-percentile seconds: brain+quote 9.2s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 16/16 (100%) | 16/16 (100%) | 16/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
