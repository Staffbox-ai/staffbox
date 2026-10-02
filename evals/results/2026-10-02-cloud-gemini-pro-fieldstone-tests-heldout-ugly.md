# Scorecard: Fieldstone IT

Model `gemini-pro-latest` on Google cloud, Gemini Pro (comparison only) · 2026-10-02 · 20 tests per mode · graded automatically, no human edits. Re-graded 2 Oct 2026: a quote now passes when the stated total is the first or last $ figure (a total followed by its breakdown was being failed).

| Task type | none | brain |
|---|---|---|
| quote | 0/17 (0%) | 11/17 (64%) |
| unknown | 0/3 (0%) | 3/3 (100%) |
| **all** | 0/20 (0%) | 14/20 (70%) |

Average seconds per answer: none 13.3s · brain 12.5s
90th-percentile seconds: none 21.0s · brain 26.7s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| none | 7/17 (41%) | 0/7 (0%) | 0/17 |
| brain | 10/17 (58%) | 10/10 (100%) | 10/17 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | ugly-01 | 46542.8 | $40,000 |
| none | ugly-02 | 7018.56 | Request logged for 24 27-inch monitors and setup. |
| none | ugly-03 | 21570.6 | Yes, we can get 15 of the 16in laptops set up for the new team. |
| none | ugly-04 | 10356.48 | Quote requested for 12 DT-MINI units (setup fees excluded); pending current unit price to  |
| none | ugly-05 | 3445.0 | Request received and service ticket created for the warehouse installation. |
| none | ugly-06 | 6410.1 | $4,500 |
| none | ugly-07 | NOT IN VAULT | I will check your account history for the previous laptop model and prepare a quote for 8  |
| none | ugly-08 | NOT IN VAULT | Approximately $21,490 (based on standard configurations and a $150 per-device setup fee),  |
| none | ugly-09 | 1500.0 | Please provide your network size and internet speed so I can send a quote and schedule you |
| none | ugly-10 | 8149.25 | I will need to check with our sales manager to see if we can honor last year's price for a |
| none | ugly-11 | 21867.0 | The quote for 100 24-inch screens and setup is $17,500.00. |
| none | ugly-12 | 5094.0 | $5,000.00 |
| none | ugly-13 | NOT IN VAULT | ~$21,600 to $25,000 |
| none | ugly-14 | 13446.0 | The total quote for 9 LT-16 units is $7,650.00. |
| none | ugly-15 | 17244.72 | $9,000 |
| none | ugly-16 | 44642.8 | A quote for 20 14-inch laptops with setup and 20 14-inch laptops without setup (pending un |
| none | ugly-17 | 1047.0 | Request acknowledged; please provide the installation address and power requirements so we |
| none | ugly-18 | 4496.0 | Quote request received and being processed for 1 x FW-SMB, 1 x SW-24P, and 4 x AP-6E for t |
| none | ugly-19 | 4504.8 | I cannot provide the exact price because the pricing list/catalog is missing from the prom |
| none | ugly-20 | 11980.4 | The total quote is $9,350, which includes a 15% nonprofit discount applied to the 10 LT-14 |
| brain | ugly-02 | 7018.56 | NOT IN VAULT, ask the service desk lead. |
| brain | ugly-03 | 21570.6 | NOT IN VAULT service desk lead (or service director if over $10,000) |
| brain | ugly-04 | 10356.48 | NOT IN VAULT, ask the service director. |
| brain | ugly-09 | 1500.0 | NOT IN VAULT. Ask the service director. |
| brain | ugly-10 | 8149.25 | NOT IN VAULT. Ask the service desk lead. |
| brain | ugly-16 | 44642.8 | NOT IN VAULT. Ask the service director. |
