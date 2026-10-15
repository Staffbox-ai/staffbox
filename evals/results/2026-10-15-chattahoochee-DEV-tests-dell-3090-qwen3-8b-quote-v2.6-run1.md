# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 13/16 (81%) |
| lookup | 9/10 (90%) |
| triage | 8/8 (100%) |
| unknown | 5/6 (83%) |
| **all** | 35/40 (87%) |

Average seconds per answer: brain+quote 0.7s
90th-percentile seconds: brain+quote 1.2s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 13/16 (81%) | 13/13 (100%) | 13/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-06 | 7040.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | quote-10 | 532.5 | NOT IN VAULT: quantities unclear (possible double count). Ask the customer to confirm the  |
| brain+quote | quote-14 | 496.8 | NOT IN VAULT: quantities unclear (possible double count). Ask the customer to confirm the  |
| brain+quote | lookup-06 | ['6:00', '5:00'] | Monday to Friday 6:00 am to 5,00 pm. |
| brain+quote | unknown-02 | NOT IN VAULT | warranty coordinator |
