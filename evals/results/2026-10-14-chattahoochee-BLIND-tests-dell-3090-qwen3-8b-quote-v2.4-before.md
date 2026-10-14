# Scorecard: Chattahoochee Plumbing & HVAC Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+quote |
|---|---|---|---|
| quote | 0/16 (0%) | 5/16 (31%) | 6/16 (37%) |
| lookup | 0/10 (0%) | 9/10 (90%) | 9/10 (90%) |
| triage | 0/8 (0%) | 7/8 (87%) | 7/8 (87%) |
| unknown | 0/6 (0%) | 5/6 (83%) | 4/6 (66%) |
| **all** | 0/40 (0%) | 26/40 (65%) | 26/40 (65%) |

Average seconds per answer: none 0.4s · brain 1.1s · brain+quote 0.5s
90th-percentile seconds: none 0.8s · brain 1.8s · brain+quote 0.9s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| none | 13/16 (81%) | 0/13 (0%) | 0/16 |
| brain | 15/16 (93%) | 5/15 (33%) | 5/16 |
| brain+quote | 13/16 (81%) | 6/13 (46%) | 6/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 174.0 | $150.00. |
| none | quote-02 | 1702.0 | Line total cannot be determined without the unit price. |
| none | quote-03 | 552.0 | Line total cannot be determined without the price per foot. |
| none | quote-04 | 133.06 | $500.00. |
| none | quote-05 | 8070.24 | The price for VL-PRV075 at the Trade Pro level is $120. |
| none | quote-06 | 7040.0 | $2,500.00. |
| none | quote-07 | 2682.0 | $349.99. |
| none | quote-08 | 62.02 | $500.00. |
| none | quote-09 | 112.0 | $180.00. |
| none | quote-10 | 532.5 | $375.00. |
| none | quote-11 | 120.6 | $120. |
| none | quote-12 | 407.38 | $120. |
| none | quote-13 | 14904.0 | $450. |
| none | quote-14 | 496.8 | Line total cannot be determined without the unit price. |
| none | quote-15 | 1821.6 | $1,875.00. |
| none | quote-16 | 118.08 | $14.95. |
| none | lookup-01 | ['$3.25'] | $2.50 per pound. |
| none | lookup-02 | ['october'] | January 1, 2023. |
| none | lookup-03 | ['$3.50'] | $15 per foot. |
| none | lookup-04 | ['15%'] | 5%. |
| none | lookup-05 | ['10%'] | The off-list amount for a contractor account is determined by the specific terms outlined  |
| none | lookup-06 | ['6:00', '5:00'] | The will-call counter is open from 8:00 AM to 5:00 PM on weekdays. |
| none | lookup-07 | ['15%'] | 20%. |
| none | lookup-08 | ['$750'] | $50. |
| none | lookup-09 | ['branch manager'] | The manager or higher-level authorized personnel. |
| none | lookup-10 | ['30%'] | 50% deposit. |
| none | triage-01 | quote | Sales Queue. |
| none | triage-02 | order_status | Delivery Delay Queue. |
| none | triage-03 | will_call | Orders Queue. |
| none | triage-04 | returns | Product Error/Correction Queue. |
| none | triage-05 | warranty | warranty/repair. |
| none | triage-06 | credit | Sales Queue. |
| none | triage-07 | will_call | Order Pickup Queue. |
| none | triage-08 | other | Sales Queue. |
| none | unknown-01 | NOT IN VAULT | $12,500. |
| none | unknown-02 | NOT IN VAULT | The warranty term on the air handlers ranges from 5 to 10 years, depending on the model an |
| none | unknown-03 | NOT IN VAULT | $1,299.99. |
| none | unknown-04 | NOT IN VAULT | $245.00. |
| none | unknown-05 | NOT IN VAULT | Delivery costs to Gainesville vary based on order specifics; contact us for a detailed quo |
| none | unknown-06 | NOT IN VAULT | Yes, we carry boilers, and a 100,000 BTU boiler typically costs between $2,500 and $4,500. |
| brain | quote-03 | 552.0 | $27.60 |
| brain | quote-04 | 133.06 | $138.60 |
| brain | quote-05 | 8070.24 | $73.10. |
| brain | quote-08 | 62.02 | $64.60 |
| brain | quote-09 | 112.0 | NOT IN VAULT, ask customer. |
| brain | quote-10 | 532.5 | $50.59 |
| brain | quote-11 | 120.6 | $9.53 |
| brain | quote-12 | 407.38 | $425.30. |
| brain | quote-14 | 496.8 | $513.00 |
| brain | quote-15 | 1821.6 | $1,881.00. |
| brain | quote-16 | 118.08 | $123.00 |
| brain | lookup-06 | ['6:00', '5:00'] | Monday to Friday 6:00 am to 5,00 pm. |
| brain | triage-08 | other | NOT IN VAULT. Ask the inside sales manager. |
| brain | unknown-02 | NOT IN VAULT | warranty coordinator |
| brain+quote | quote-01 | 174.0 | $160.08 |
| brain+quote | quote-03 | 552.0 | NOT IN VAULT: 120 ft of type is not on the price list (we stock: type L hard copper pipe 1 |
| brain+quote | quote-04 | 133.06 | $147.84 |
| brain+quote | quote-05 | 8070.24 | $9,494.40 |
| brain+quote | quote-07 | 2682.0 | $2,373.60 |
| brain+quote | quote-08 | 62.02 | $72.96 |
| brain+quote | quote-10 | 532.5 | NOT IN VAULT: 150 ft of type is not on the price list (we stock: type M hard copper pipe 1 |
| brain+quote | quote-11 | 120.6 | NOT IN VAULT: 40 feet of CP-M is not on the price list (we stock: type M hard copper pipe  |
| brain+quote | quote-12 | 407.38 | $452.64 |
| brain+quote | quote-13 | 14904.0 | $16,560.00 |
| brain+quote | lookup-06 | ['6:00', '5:00'] | Monday to Friday 6:00 am to 5,00 pm. |
| brain+quote | triage-08 | other | NOT IN VAULT. Ask the inside sales manager. |
| brain+quote | unknown-02 | NOT IN VAULT | warranty coordinator |
| brain+quote | unknown-03 | NOT IN VAULT | $1,749.00 |
