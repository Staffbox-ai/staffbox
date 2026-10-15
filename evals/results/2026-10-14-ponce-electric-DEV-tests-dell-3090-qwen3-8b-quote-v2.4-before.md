# Scorecard: Ponce Electric Supply

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 40 tests per mode · graded automatically, no human edits.

| Task type | brain+quote |
|---|---|
| quote | 8/16 (50%) |
| lookup | 10/10 (100%) |
| triage | 7/8 (87%) |
| unknown | 5/6 (83%) |
| **all** | 30/40 (75%) |

Average seconds per answer: brain+quote 0.5s
90th-percentile seconds: brain+quote 1.0s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| brain+quote | 11/16 (68%) | 8/11 (72%) | 8/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| brain+quote | quote-01 | 33.42 | NOT IN VAULT: 100 ft of THHN is not on the price list (we stock: THHN 14 AWG stranded copp |
| brain+quote | quote-03 | 15.31 | $17.40 |
| brain+quote | quote-05 | 1140.48 | $1,296.00 |
| brain+quote | quote-06 | 46.38 | NOT IN VAULT: 150 ft of THHN is not on the price list (we stock: THHN 14 AWG stranded copp |
| brain+quote | quote-07 | 130.62 | NOT IN VAULT: 300 feet of W-THHN is not on the price list (we stock: THHN 14 AWG stranded  |
| brain+quote | quote-10 | 5464.8 | $6,210.00 |
| brain+quote | quote-11 | 297.48 | NOT IN VAULT: 150 feet of W-NM is not on the price list (we stock: NM-B 14/2 copper with g |
| brain+quote | quote-13 | 532.22 | NOT IN VAULT: 500 feet of W-NM is not on the price list (we stock: NM-B 14/2 copper with g |
| brain+quote | triage-08 | other | other, ask the HR department. |
| brain+quote | unknown-03 | NOT IN VAULT | $472.00 |
