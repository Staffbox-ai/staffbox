# Scorecard: Ponce Electric Supply

Model `qwen3:8b` on Dell RTX 3090 · 2026-10-14 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+quote |
|---|---|---|---|
| quote | 0/16 (0%) | 5/16 (31%) | 8/16 (50%) |
| lookup | 2/10 (20%) | 10/10 (100%) | 10/10 (100%) |
| triage | 0/8 (0%) | 7/8 (87%) | 7/8 (87%) |
| unknown | 0/6 (0%) | 5/6 (83%) | 5/6 (83%) |
| **all** | 2/40 (5%) | 27/40 (67%) | 30/40 (75%) |

Average seconds per answer: none 30.7s · brain 164.3s · brain+quote 1.2s
90th-percentile seconds: none 45.6s · brain 443.4s · brain+quote 1.7s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| none | 12/16 (75%) | 0/12 (0%) | 0/16 |
| brain | 13/16 (81%) | 5/13 (38%) | 5/16 |
| brain+quote | 11/16 (68%) | 8/11 (72%) | 8/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 33.42 | $50. |
| none | quote-02 | 819.38 | $75. |
| none | quote-03 | 15.31 | Please provide the unit price and any additional details for accurate calculation. |
| none | quote-04 | 997.5 | $750. |
| none | quote-05 | 1140.48 | The price for CD-EMT-050 at the contractor level is $200. |
| none | quote-06 | 46.38 | Line total cannot be calculated without the cost per foot. |
| none | quote-07 | 130.62 | $12.50. |
| none | quote-08 | 997.5 | $750.00. |
| none | quote-09 | 25.6 | $48.00. |
| none | quote-10 | 5464.8 | The price for LT-EXC at the contractor level is $200. |
| none | quote-11 | 297.48 | $12.75. |
| none | quote-12 | 56.4 | Line total cannot be determined without the unit price. |
| none | quote-13 | 532.22 | Please provide the unit price per foot for W-NM12-3 at the contractor level. |
| none | quote-14 | 652.5 | $250. |
| none | quote-15 | 1339.5 | $150. |
| none | quote-16 | 11880.0 | $34.95. |
| none | lookup-01 | ['8%'] | The copper surcharge on wire is approximately $2.50 per pound. |
| none | lookup-02 | ['october'] | January 1, 2023. |
| none | lookup-03 | ['25 feet'] | 6 inches. |
| none | lookup-04 | ['$7.50'] | $2.50. |
| none | lookup-05 | ['12%'] | The off-list amount for a contractor account varies depending on the agreed terms between  |
| none | lookup-06 | ['6:30', '4:30'] | The will-call counter hours on weekdays are from 8:00 AM to 4:30 PM. |
| none | lookup-08 | ['$500'] | $50. |
| none | lookup-09 | ['branch manager'] | The Purchasing Manager or a higher-level supervisor. |
| none | triage-01 | quote | Sales Queue. |
| none | triage-02 | order_status | Delivery Queue. |
| none | triage-03 | will_call | Customer Service. |
| none | triage-04 | returns | Returns and Refunds. |
| none | triage-05 | credit | Accounts Receivable. |
| none | triage-06 | will_call | Order Pickup Queue. |
| none | triage-07 | credit | Accounts Payable. |
| none | triage-08 | other | Human Resources. |
| none | unknown-01 | NOT IN VAULT | $4,500. |
| none | unknown-02 | NOT IN VAULT | 5 years. |
| none | unknown-03 | NOT IN VAULT | $120. |
| none | unknown-04 | NOT IN VAULT | The total cost for 300 feet of W-THHN2-BK is $X.XX. |
| none | unknown-05 | NOT IN VAULT | $45.00. |
| none | unknown-06 | NOT IN VAULT | Yes, we sell solar inverters, and their prices range from $800 to $2,500 depending on the  |
| brain | quote-02 | 819.38 | $820.88 |
| brain | quote-04 | 997.5 | $1,050.00 |
| brain | quote-05 | 1140.48 | $7.20 × 10% discount = $6.48 per unit, then × 12% off = $5.69 per unit, total = $1,138.00. |
| brain | quote-06 | 46.38 | $46.62 |
| brain | quote-07 | 130.62 | $121.50 |
| brain | quote-08 | 997.5 | $1,050.00. |
| brain | quote-11 | 297.48 | ERROR HTTP Error 500: Internal Server Error |
| brain | quote-12 | 56.4 | ERROR timed out |
| brain | quote-14 | 652.5 | $72.50 |
| brain | quote-15 | 1339.5 | ERROR timed out |
| brain | quote-16 | 11880.0 | $12,540.00. |
| brain | triage-08 | other | other, ask the inside sales manager. |
| brain | unknown-05 | NOT IN VAULT | Ask the warehouse lead. |
| brain+quote | quote-01 | 33.42 | NOT IN VAULT: 100 ft of THHN is not on the price list (we stock: THHN 14 AWG stranded copp |
| brain+quote | quote-03 | 15.31 | $17.40 |
| brain+quote | quote-05 | 1140.48 | $1,296.00 |
| brain+quote | quote-06 | 46.38 | NOT IN VAULT: 150 ft of THHN is not on the price list (we stock: THHN 14 AWG stranded copp |
| brain+quote | quote-07 | 130.62 | NOT IN VAULT: 300 feet of W-THHN is not on the price list (we stock: THHN 14 AWG stranded  |
| brain+quote | quote-10 | 5464.8 | $6,210.00 |
| brain+quote | quote-11 | 297.48 | NOT IN VAULT: 150 feet of W-NM is not on the price list (we stock: NM-B 14/2 copper with g |
| brain+quote | quote-13 | 532.22 | NOT IN VAULT: 500 feet of W-NM is not on the price list (we stock: NM-B 14/2 copper with g |
| brain+quote | triage-08 | other | other, ask the inside sales manager. |
| brain+quote | unknown-03 | NOT IN VAULT | $472.00 |
