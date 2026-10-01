# Scorecard: Peachtree Cabinet Works

Model `qwen3:8b` on Dell RTX 3090 · 2026-09-30 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+calc | brain+quote |
|---|---|---|---|---|
| quote | 0/16 (0%) | 8/16 (50%) | 9/16 (56%) | 16/16 (100%) |
| lookup | 1/10 (10%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) |
| triage | 0/8 (0%) | 7/8 (87%) | 8/8 (100%) | 7/8 (87%) |
| unknown | 0/6 (0%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| **all** | 1/40 (2%) | 31/40 (77%) | 33/40 (82%) | 39/40 (97%) |

Average seconds per answer: none 0.4s · brain 0.7s · brain+calc 1.0s · brain+quote 0.4s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 985.6 | $480. |
| none | quote-02 | 2691.0 | Please check the current pricing list or contact the sales department for an accurate quot |
| none | quote-03 | 1821.6 | $1,250. |
| none | quote-04 | 1155.96 | Line total cannot be calculated without the unit price. |
| none | quote-05 | 3946.8 | $60. |
| none | quote-06 | 1610.4 | $1,560.00. |
| none | quote-07 | 5202.6 | $75. |
| none | quote-08 | 540.0 | $16. |
| none | quote-09 | 1775.0 | $4,800. |
| none | quote-10 | 2403.5 | Line total cannot be calculated without the unit price. |
| none | quote-11 | 1818.3 | $1,260. |
| none | quote-12 | 5869.6 | Line total cannot be calculated without the unit price. |
| none | quote-13 | 387.2 | $16. |
| none | quote-14 | 313.2 | $256. |
| none | quote-15 | 5369.3 | Line total cannot be determined without the unit price. |
| none | quote-16 | 3312.0 | Line total cannot be calculated without the unit price. |
| none | lookup-01 | ['20 business days'] | 5 to 7 business days. |
| none | lookup-02 | ['10 business days'] | 5 business days. |
| none | lookup-03 | ['$250'] | 100 units. |
| none | lookup-04 | ['50%'] | 30%. |
| none | lookup-05 | ['plant manager'] | The Sales Manager or higher management can approve a special price for a big customer. |
| none | lookup-07 | ['25%'] | The rush cost is an additional fee to expedite the project, covering increased labor and s |
| none | lookup-08 | ['50 miles'] | Free delivery is available within a 50-mile radius of our showroom. |
| none | lookup-09 | ['poplar', 'maple', 'white oak', 'cherry'] | oak, maple, cherry, hickory, and walnut. |
| none | lookup-10 | ['20 business days'] | 14 business days. |
| none | triage-01 | quote | Pricing queue. |
| none | triage-02 | order_status | Accounts Payable. |
| none | triage-03 | complaint | Quality Control. |
| none | triage-04 | cert_request | Compliance Certification. |
| none | triage-05 | other | HR |
| none | triage-06 | complaint | Quality Control. |
| none | triage-07 | order_status | Order Tracking. |
| none | triage-08 | cert_request | Quality Assurance. |
| none | unknown-01 | NOT IN VAULT | $249.99. |
| none | unknown-02 | NOT IN VAULT | A limited lifetime warranty against peeling, chipping, and cracking under normal use and p |
| none | unknown-03 | NOT IN VAULT | Yes, we can ship to Toronto, and the cost typically ranges from $15 to $35 for standard gr |
| none | unknown-04 | NOT IN VAULT | No, the plant is closed on Saturdays. |
| none | unknown-05 | NOT IN VAULT | $360. |
| none | unknown-06 | NOT IN VAULT | $125. |
| brain | quote-02 | 2691.0 | $2,685.00 |
| brain | quote-03 | 1821.6 | $1,800.00 |
| brain | quote-04 | 1155.96 | $1,156.00 |
| brain | quote-05 | 3946.8 | $3,894.00. |
| brain | quote-07 | 5202.6 | $5,372.25 |
| brain | quote-08 | 540.0 | $33.75. |
| brain | quote-14 | 313.2 | $270.00. |
| brain | quote-15 | 5369.3 | $5,369.20 |
| brain | triage-05 | other | NOT IN VAULT. Ask the office manager. |
| brain+calc | quote-02 | 2691.0 | $2,925.00. |
| brain+calc | quote-04 | 1155.96 | $1,118.83 |
| brain+calc | quote-05 | 3946.8 | $4,290.00. |
| brain+calc | quote-06 | 1610.4 | $1,530.00. |
| brain+calc | quote-07 | 5202.6 | $5372.25 |
| brain+calc | quote-08 | 540.0 | $33.75 |
| brain+calc | quote-15 | 5369.3 | $5,368.20 |
| brain+quote | triage-05 | other | NOT IN VAULT. Ask the office manager. |
