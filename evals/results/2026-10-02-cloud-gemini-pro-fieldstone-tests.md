# Scorecard: Fieldstone IT

Model `gemini-pro-latest` on Google cloud, Gemini Pro (comparison only) · 2026-10-02 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain |
|---|---|---|
| quote | 0/16 (0%) | 15/16 (93%) |
| lookup | 2/10 (20%) | 10/10 (100%) |
| triage | 3/8 (37%) | 8/8 (100%) |
| unknown | 0/6 (0%) | 6/6 (100%) |
| **all** | 5/40 (12%) | 39/40 (97%) |

Average seconds per answer: none 13.3s · brain 6.9s
90th-percentile seconds: none 21.5s · brain 11.8s

Quotes, the pilot pass bar (a refusal is a miss; "right" means the exact line total, no edits):

| Mode | Priced | Right of priced | Right of all |
|---|---|---|---|
| none | 4/16 (25%) | 0/4 (0%) | 0/16 |
| brain | 15/16 (93%) | 15/15 (100%) | 15/16 |

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 46542.8 | 40 x (LT-14 unit price + setup fee) |
| none | quote-02 | 28760.8 | The exact price depends on the specific laptop model and setup requirements, but an estima |
| none | quote-03 | 11496.48 | $4,800 |
| none | quote-04 | 5285.76 | Cannot be determined without the pricing sheet. |
| none | quote-05 | 16870.8 | $12,000 |
| none | quote-06 | 5405.76 | Cannot be determined without the unit prices for the MON-24 and setup. |
| none | quote-07 | 34907.1 | I need the current unit price and setup fee to calculate the total for 30 units. |
| none | quote-08 | 33795.0 | Insufficient information to provide a price. |
| none | quote-09 | 9779.1 | 30 x (UPS-1500 unit price + setup fee) |
| none | quote-10 | 42375.0 | I cannot calculate the price because the pricing information was not provided. |
| none | quote-11 | 1988.0 | Cannot be determined without the price list. |
| none | quote-12 | 34901.75 | The total cannot be calculated without the specific unit price and setup fee. |
| none | quote-13 | 2982.0 | The total cannot be determined without the current unit prices and setup fees. |
| none | quote-14 | 10402.56 | 24 x (AP-6E unit price + setup fee) |
| none | quote-15 | 29000.0 | $10,000 |
| none | quote-16 | 11952.0 | Cannot be determined without the pricing catalog/unit costs. |
| none | lookup-01 | ['15 minutes'] | Immediately (typically within 15 to 30 minutes as a Priority 1 issue). |
| none | lookup-03 | ['$165'] | $150 per hour |
| none | lookup-05 | ['sunday', '2 am'] | Sundays from 1:00 AM to 5:00 AM local time. |
| none | lookup-06 | ['call'] | Verify the user's identity. |
| none | lookup-07 | ['1 hour'] | Immediately upon termination or within 24 hours of the request. |
| none | lookup-08 | ['service director'] | The CEO |
| none | lookup-09 | ['3 business days'] | 5 business days. |
| none | lookup-10 | ['change ticket'] | A formal support ticket and written authorization from an approved contact. |
| none | triage-01 | service_desk | Hardware |
| none | triage-02 | quote | Sales |
| none | triage-06 | service_desk | Helpdesk |
| none | triage-07 | onboarding | Access Management |
| none | triage-08 | other | Marketing |
| none | unknown-01 | NOT IN VAULT | $450.00 |
| none | unknown-02 | NOT IN VAULT | No, we do not support Linux desktops for clients. |
| none | unknown-03 | NOT IN VAULT | One year |
| none | unknown-04 | NOT IN VAULT | Yes. |
| none | unknown-05 | NOT IN VAULT | $10,000 |
| none | unknown-06 | NOT IN VAULT | 24 hours. |
| brain | quote-15 | 29000.0 | NOT IN VAULT, ask the service director. |
