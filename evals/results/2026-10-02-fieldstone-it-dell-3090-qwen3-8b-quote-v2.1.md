# Scorecard: Fieldstone IT

Model `qwen3:8b` on Dell RTX 3090 running the 8B model a 16 GB Mac mini runs · 2026-10-02 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 13/16 (81%) |
| lookup | 10/10 (100%) |
| triage | 8/8 (100%) |
| unknown | 6/6 (100%) |
| **all** | 37/40 (92%) |

Average seconds per answer: brain+quote 1.4s
90th-percentile seconds: brain+quote 1.9s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 13/16 (81%) | 13/13 (100%) | 13/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-02 | 28760.8 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | quote-12 | 34901.75 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | quote-16 | 11952.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
