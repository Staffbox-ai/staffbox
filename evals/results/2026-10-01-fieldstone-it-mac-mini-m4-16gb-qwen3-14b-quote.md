# Scorecard: Fieldstone IT

Model `qwen3:14b` on Mac mini M4 16 GB (Staffbox unit zero) · 2026-10-01 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote | brain |
|---|---|---|
| quote | 14/16 (87%) | 8/16 (50%) |
| lookup | 10/10 (100%) | 10/10 (100%) |
| triage | 3/8 (37%) | 8/8 (100%) |
| unknown | 2/6 (33%) | 6/6 (100%) |
| **all** | 29/40 (72%) | 32/40 (80%) |

Average seconds per answer: brain+quote 199.9s · brain 205.1s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-01 | 46542.8 | $46,434.80. |
| brain+quote | quote-09 | 9779.1 | $9,764.10. |
| brain+quote | triage-03 | security | ERROR timed out |
| brain+quote | triage-04 | onboarding | ERROR timed out |
| brain+quote | triage-05 | billing | ERROR timed out |
| brain+quote | triage-06 | service_desk | ERROR timed out |
| brain+quote | triage-07 | onboarding | ERROR timed out |
| brain+quote | unknown-01 | NOT IN VAULT | $234.00 |
| brain+quote | unknown-04 | NOT IN VAULT | ERROR timed out |
| brain+quote | unknown-05 | NOT IN VAULT | ERROR timed out |
| brain+quote | unknown-06 | NOT IN VAULT | ERROR timed out |
| brain | quote-01 | 46542.8 | ERROR timed out |
| brain | quote-02 | 28760.8 | ERROR timed out |
| brain | quote-03 | 11496.48 | ERROR timed out |
| brain | quote-05 | 16870.8 | $16,858.80 (needs service director's approval). |
| brain | quote-07 | 34907.1 | $34,881.10. |
| brain | quote-09 | 9779.1 | $9,764.10. |
| brain | quote-14 | 10402.56 | $10,401.60. |
| brain | quote-15 | 29000.0 | $30,000.00. |
