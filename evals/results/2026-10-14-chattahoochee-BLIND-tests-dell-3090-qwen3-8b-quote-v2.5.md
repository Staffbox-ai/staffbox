# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 10/16 (62%) |
| lookup | 9/10 (90%) |
| triage | 7/8 (87%) |
| unknown | 5/6 (83%) |
| **all** | 31/40 (77%) |

Average seconds per answer: brain+quote 0.6s
90th-percentile seconds: brain+quote 1.0s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 15/16 (93%) | 10/15 (66%) | 10/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-01 | 174.0 | $160.08 (1 line; list price, no account level named) |
| brain+quote | quote-03 | 552.0 | $511.34 (1 line; list price, no account level named) |
| brain+quote | quote-07 | 2682.0 | $2,373.60 (1 line; list price, no account level named) |
| brain+quote | quote-09 | 112.0 | NOT IN VAULT: FC-CP050-50 is sold by the box of 50 only; 4 is not a whole number of boxes, |
| brain+quote | quote-10 | 532.5 | $56.75 (1 line; list price, no account level named) |
| brain+quote | quote-11 | 120.6 | $119.28 (1 line; contractor level) |
| brain+quote | lookup-06 | ['6:00', '5:00'] | Monday to Friday 6:00 am to 5,00 pm. |
| brain+quote | triage-08 | other | NOT IN VAULT. Ask the inside sales manager. |
| brain+quote | unknown-02 | NOT IN VAULT | warranty coordinator |
