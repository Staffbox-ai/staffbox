# Scorecard: Brookhaven Lumber & Building Supply (fictional)

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-15 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+quote |
|---|---|---|---|
| quote | 0/16 (0%) | 6/16 (37%) | 4/16 (25%) |
| lookup | 1/10 (10%) | 9/10 (90%) | 9/10 (90%) |
| triage | 0/8 (0%) | 6/8 (75%) | 5/8 (62%) |
| unknown | 0/6 (0%) | 6/6 (100%) | 4/6 (66%) |
| **all** | 1/40 (2%) | 27/40 (67%) | 22/40 (55%) |

Average seconds per answer: none 0.4s · brain 1.1s · brain+quote 0.5s
90th-percentile seconds: none 0.8s · brain 1.9s · brain+quote 1.0s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| none | 12/16 (75%) | 0/12 (0%) | 0/16 |
| brain | 16/16 (100%) | 6/16 (37%) | 6/16 |
| brain+quote | 16/16 (100%) | 4/16 (25%) | 4/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 1261.95 | $1,121.25. |
| none | quote-02 | 6439.0 | $2,200.00. |
| none | quote-03 | 1000.5 | The total is 9,600 pounds. |
| none | quote-04 | 182.5 | $17.50. |
| none | quote-05 | 3.92 | $10.00. |
| none | quote-06 | 283.78 | $24. |
| none | quote-07 | 415.43 | $288. |
| none | quote-08 | 2331.72 | I will prepare a quote for 208 pieces of DL-2810. |
| none | quote-09 | 399.5 | $450. |
| none | quote-10 | 1340.06 | $50. |
| none | quote-11 | 940.8 | Cannot calculate total without unit price. |
| none | quote-12 | 173.04 | Line total cannot be calculated without the unit price. |
| none | quote-13 | 961.84 | $24. |
| none | quote-14 | 305.03 | $425.00. |
| none | quote-15 | 290.0 | $50.00. |
| none | quote-16 | 112.5 | $24.95. |
| none | lookup-01 | ['5%'] | The market adjustment on dimensional lumber is currently a small decrease. |
| none | lookup-02 | ['october'] | January 1, 2024. |
| none | lookup-03 | ['$2.00'] | $0.50 per linear foot. |
| none | lookup-04 | ['12%'] | 5%. |
| none | lookup-05 | ['8%'] | The discount off list for a contractor account typically ranges from 5% to 15%, depending  |
| none | lookup-06 | ['6:30', '5:00'] | The will-call yard hours on weekdays are from 7:00 AM to 5:00 PM. |
| none | lookup-07 | ['20%'] | There is no restocking fee for returns at Brookhaven Lumber & Building Supply. |
| none | lookup-08 | ['$55'] | $50. |
| none | lookup-09 | ['general manager'] | The sales manager or a designated supervisor. |
| none | triage-01 | quote | Decking & Pricing Queue. |
| none | triage-02 | order_status | Delivered to Delivery Tracking queue. |
| none | triage-03 | will_call | Sales and Order Tracking. |
| none | triage-04 | returns | Returns and Damages. |
| none | triage-05 | millwork | Sales Queue. |
| none | triage-06 | credit | Route to Builder Program Queue. |
| none | triage-07 | millwork | Order Tracking Queue. |
| none | triage-08 | other | Human Resources. |
| none | unknown-01 | NOT IN VAULT | $1,296.00 per bundle. |
| none | unknown-02 | NOT IN VAULT | The warranty on the vinyl windows typically ranges from 10 to 20 years, depending on the p |
| none | unknown-03 | NOT IN VAULT | $1,250.00. |
| none | unknown-04 | NOT IN VAULT | $1,298.00 each. |
| none | unknown-05 | NOT IN VAULT | Delivery costs to Athens vary based on order size and details; contact our sales team for  |
| none | unknown-06 | NOT IN VAULT | Yes, we sell metal roofing panels at $12.50 per square foot. |
| brain | quote-01 | 1261.95 | $1,263.15 |
| brain | quote-02 | 6439.0 | $6,644.50 |
| brain | quote-03 | 1000.5 | $893.10 |
| brain | quote-06 | 283.78 | $283.33 |
| brain | quote-07 | 415.43 | $444.51 |
| brain | quote-08 | 2331.72 | $2,233.03 |
| brain | quote-09 | 399.5 | $397.50. |
| brain | quote-10 | 1340.06 | $1,331.11 |
| brain | quote-13 | 961.84 | $964.89 |
| brain | quote-14 | 305.03 | $305.22. |
| brain | lookup-06 | ['6:30', '5:00'] | Monday to Friday 6:30 am to 5,00 pm. |
| brain | triage-03 | will_call | order_status |
| brain | triage-07 | millwork | order_status |
| brain+quote | quote-01 | 1261.95 | $1,342.50 |
| brain+quote | quote-02 | 6439.0 | $6,850.00 |
| brain+quote | quote-03 | 1000.5 | $1,074.00 |
| brain+quote | quote-06 | 283.78 | $318.00 |
| brain+quote | quote-07 | 415.43 | $449.60 |
| brain+quote | quote-08 | 2331.72 | $2,387.84 |
| brain+quote | quote-09 | 399.5 | $397.50 |
| brain+quote | quote-10 | 1340.06 | $1,620.00 |
| brain+quote | quote-11 | 940.8 | $896.00 |
| brain+quote | quote-12 | 173.04 | $164.80 |
| brain+quote | quote-13 | 961.84 | $1,126.80 |
| brain+quote | quote-14 | 305.03 | $349.00 |
| brain+quote | lookup-06 | ['6:30', '5:00'] | Monday to Friday 6:30 am to 5,00 pm. |
| brain+quote | triage-03 | will_call | order_status |
| brain+quote | triage-07 | millwork | order_status |
| brain+quote | triage-08 | other | other, ask the inside sales manager. |
| brain+quote | unknown-03 | NOT IN VAULT | $418.00 |
| brain+quote | unknown-04 | NOT IN VAULT | $1,556.00 |
