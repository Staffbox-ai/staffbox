# Scorecard: Peachtree Cabinet Works

Model `qwen3:8b` on Mac mini M4 16 GB (Staffbox-Zero, day) · 2026-10-05 · 156 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 135/142 (95%) |
| unknown | 12/14 (85%) |
| **all** | 147/156 (94%) |

Average seconds per answer: brain+quote 3.4s
90th-percentile seconds: brain+quote 4.3s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 136/142 (95%) | 135/136 (99%) | 135/142 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | gen-020 | 1450.08 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | gen-023 | 1278.22 | $1,343.77 (2 lines) |
| brain+quote | gen-040 | NOT IN VAULT | $1,382.70 (2 lines) |
| brain+quote | gen-054 | 875.2 | NOT IN VAULT: species not stated or not offered (offered: poplar, maple, white oak, cherry |
| brain+quote | gen-055 | 692.0 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | gen-057 | 2553.6 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
| brain+quote | gen-091 | 1640.06 | NOT IN VAULT: finish not stated or not offered (offered: unfinished, stained, painted): as |
| brain+quote | gen-099 | NOT IN VAULT | $512.40 (2 lines) |
| brain+quote | gen-109 | 1941.6 | NOT IN VAULT: the request does not name one stocked item exactly. Ask the customer which m |
