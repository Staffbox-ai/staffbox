# Scorecard: Brookhaven Lumber & Building Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 4/16 (25%) |
| lookup | 9/10 (90%) |
| triage | 5/8 (62%) |
| unknown | 6/6 (100%) |
| **all** | 24/40 (60%) |

Average seconds per answer: brain+quote 0.6s
90th-percentile seconds: brain+quote 1.0s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 15/16 (93%) | 4/15 (26%) | 4/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-01 | 1261.95 | $1,342.50 (1 line; list price, no account level named) |
| brain+quote | quote-02 | 6439.0 | $6,850.00 (1 line; list price) |
| brain+quote | quote-03 | 1000.5 | $1,074.00 (1 line; list price, no account level named) |
| brain+quote | quote-06 | 283.78 | $292.56 (1 line; contractor level) |
| brain+quote | quote-07 | 415.43 | $395.65 (1 line; builder level) |
| brain+quote | quote-08 | 2331.72 | $2,387.84 (1 line; list price, no account level named) |
| brain+quote | quote-10 | 1340.06 | $1,425.60 (1 line; builder level) |
| brain+quote | quote-11 | 940.8 | $896.00 (1 line; list price, no account level named) |
| brain+quote | quote-12 | 173.04 | $164.80 (1 line; list price, no account level named) |
| brain+quote | quote-13 | 961.84 | $991.58 (1 line; builder level) |
| brain+quote | quote-14 | 305.03 | $321.08 (1 line; contractor level) |
| brain+quote | quote-15 | 290.0 | NOT IN VAULT: 1 inch thick S is not on the price list (we stock: ). Ask the customer wheth |
| brain+quote | lookup-06 | ['6:30', '5:00'] | Monday to Friday 6:30 am to 5,00 pm. |
| brain+quote | triage-03 | will_call | order_status |
| brain+quote | triage-07 | millwork | order_status |
| brain+quote | triage-08 | other | other, ask the inside sales manager. |
