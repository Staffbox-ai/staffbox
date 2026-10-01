# Scorecard: Fieldstone IT

Model `qwen3:8b` on Mac mini M4 16 GB (Staffbox unit zero) · 2026-10-01 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote | brain |
|---|---|---|
| quote | 16/16 (100%) | 8/16 (50%) |
| lookup | 10/10 (100%) | 6/10 (60%) |
| triage | 8/8 (100%) | 8/8 (100%) |
| unknown | 6/6 (100%) | 6/6 (100%) |
| **all** | 40/40 (100%) | 28/40 (70%) |

Average seconds per answer: brain+quote 60.2s · brain 157.8s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain | quote-01 | 46542.8 | $47,921.60 |
| brain | quote-02 | 28760.8 | $27,879.40. |
| brain | quote-03 | 11496.48 | $11,502.72. |
| brain | quote-05 | 16870.8 | $17,337.60 (requires service director approval). |
| brain | quote-07 | 34907.1 | $34,856.10. |
| brain | quote-12 | 34901.75 | $34,903.75. |
| brain | quote-15 | 29000.0 | The line total is $30,000.00 and requires the service director's approval. |
| brain | quote-16 | 11952.0 | ERROR timed out |
| brain | lookup-01 | ['15 minutes'] | ERROR timed out |
| brain | lookup-02 | ['$225'] | ERROR timed out |
| brain | lookup-03 | ['$165'] | ERROR timed out |
| brain | lookup-04 | ['30 days'] | ERROR timed out |
