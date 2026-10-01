# Scorecard: Fieldstone IT

Model `qwen3:8b` on Dell RTX 3090 · 2026-09-30 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+calc | brain+quote |
|---|---|---|---|---|
| quote | 0/16 (0%) | 9/16 (56%) | 8/16 (50%) | 16/16 (100%) |
| lookup | 1/10 (10%) | 10/10 (100%) | 9/10 (90%) | 10/10 (100%) |
| triage | 0/8 (0%) | 8/8 (100%) | 8/8 (100%) | 8/8 (100%) |
| unknown | 0/6 (0%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| **all** | 1/40 (2%) | 33/40 (82%) | 31/40 (77%) | 40/40 (100%) |

Average seconds per answer: none 0.5s · brain 0.9s · brain+calc 1.0s · brain+quote 0.4s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 46542.8 | Cannot calculate line total without the unit price. |
| none | quote-02 | 28760.8 | Please provide more details about the laptops and configurations to determine the cost. |
| none | quote-03 | 11496.48 | $12. |
| none | quote-04 | 5285.76 | Please contact Fieldstone IT's sales team for the latest pricing and setup costs for DOCK- |
| none | quote-05 | 16870.8 | $1,600. |
| none | quote-06 | 5405.76 | Cannot calculate line total without the unit price. |
| none | quote-07 | 34907.1 | $30. |
| none | quote-08 | 33795.0 | $30. |
| none | quote-09 | 9779.1 | Line total cannot be determined without pricing details. |
| none | quote-10 | 42375.0 | $30. |
| none | quote-11 | 1988.0 | $299. |
| none | quote-12 | 34901.75 | Please provide more details about the laptops and configurations to determine the cost. |
| none | quote-13 | 2982.0 | $1,050. |
| none | quote-14 | 10402.56 | The line total cannot be determined without the unit price of the AP-6E. |
| none | quote-15 | 29000.0 | Please provide specific details about the firewall models and features for an accurate quo |
| none | quote-16 | 11952.0 | Please provide more details about the laptops and configurations to determine the cost. |
| none | lookup-01 | ['15 minutes'] | You should respond immediately and notify the IT department or on-call support as soon as  |
| none | lookup-02 | ['$225'] | $150 per hour. |
| none | lookup-03 | ['$165'] | $150 per hour. |
| none | lookup-05 | ['sunday', '2 am'] | The server maintenance window is every Sunday from 2:00 AM to 4:00 AM. |
| none | lookup-06 | ['call'] | Contact Fieldstone IT Support to report the lost phone and request assistance with regaini |
| none | lookup-07 | ['1 hour'] | Within 24 hours. |
| none | lookup-08 | ['service director'] | The Director of Operations. |
| none | lookup-09 | ['3 business days'] | Two weeks' notice. |
| none | lookup-10 | ['change ticket'] | Review the current firewall rule configuration and assess the impact of the proposed chang |
| none | triage-01 | service_desk | Technical Support. |
| none | triage-02 | quote | Sales Queue. |
| none | triage-03 | security | Phishing and Social Engineering. |
| none | triage-04 | onboarding | Onboarding Queue. |
| none | triage-05 | billing | Billing Support. |
| none | triage-06 | service_desk | Microsoft Office Support. |
| none | triage-07 | onboarding | Account Management. |
| none | triage-08 | other | Client Relations. |
| none | unknown-01 | NOT IN VAULT | The price of a 34-inch ultrawide monitor typically ranges from $300 to $800. |
| none | unknown-02 | NOT IN VAULT | Yes. |
| none | unknown-03 | NOT IN VAULT | The LT-14 laptop has a 1-year limited warranty. |
| none | unknown-04 | NOT IN VAULT | I don't have access to real-time information about Morrow & Pike's internet infrastructure |
| none | unknown-05 | NOT IN VAULT | Please provide the model of the iPads and any additional requirements for an accurate quot |
| none | unknown-06 | NOT IN VAULT | 24 hours. |
| brain | quote-01 | 46542.8 | $47,921.60 |
| brain | quote-02 | 28760.8 | $28,861.20. |
| brain | quote-05 | 16870.8 | $17,337.60 (requires service director approval). |
| brain | quote-07 | 34907.1 | $34,850.10. |
| brain | quote-12 | 34901.75 | $34,803.75. |
| brain | quote-15 | 29000.0 | $30,000 (needs service director approval). |
| brain | quote-16 | 11952.0 | $11,398.28. |
| brain+calc | quote-01 | 46542.8 | $47,921.60 |
| brain+calc | quote-03 | 11496.48 | $11,928.00 |
| brain+calc | quote-04 | 5285.76 | $3,496.00 |
| brain+calc | quote-05 | 16870.8 | $16,864.80 (requires service director approval). |
| brain+calc | quote-06 | 5405.76 | $5,356.00 |
| brain+calc | quote-12 | 34901.75 | $34,906.25 |
| brain+calc | quote-14 | 10402.56 | $9,235.20 |
| brain+calc | quote-15 | 29000.0 | $30,000.00. |
| brain+calc | lookup-02 | ['$225'] | $226.88 per hour for after-hours work. |
