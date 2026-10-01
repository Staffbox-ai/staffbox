# Scorecard: Peachtree Cabinet Works

Model `qwen3:8b` on Mac mini M4 16 GB (Staffbox unit zero) · 2026-10-01 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote | brain |
|---|---|---|
| quote | 16/16 (100%) | 9/16 (56%) |
| lookup | 10/10 (100%) | 10/10 (100%) |
| triage | 7/8 (87%) | 7/8 (87%) |
| unknown | 6/6 (100%) | 6/6 (100%) |
| **all** | 39/40 (97%) | 32/40 (80%) |

Average seconds per answer: brain+quote 93.7s · brain 21.0s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | triage-05 | other | NOT IN VAULT plus ask the office manager. |
| brain | quote-02 | 2691.0 | $2,685.00 |
| brain | quote-04 | 1155.96 | $1,156.00 |
| brain | quote-05 | 3946.8 | $4,224.00 |
| brain | quote-06 | 1610.4 | $1,535.81 |
| brain | quote-07 | 5202.6 | $5,372.25 |
| brain | quote-08 | 540.0 | $33.75. |
| brain | quote-15 | 5369.3 | $5,369.20 |
| brain | triage-05 | other | NOT IN VAULT plus ask the office manager. |
