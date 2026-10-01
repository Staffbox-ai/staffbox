# Scorecard: Fieldstone IT

Model `qwen3.8-27b-64k` on Dell RTX 3090 · 2026-09-30 · 40 tests per mode · graded automatically, no human edits.

| Task type | none | brain | brain+calc | brain+quote |
|---|---|---|---|---|
| quote | 0/16 (0%) | 15/16 (93%) | 15/16 (93%) | 16/16 (100%) |
| lookup | 0/10 (0%) | 10/10 (100%) | 10/10 (100%) | 10/10 (100%) |
| triage | 2/8 (25%) | 8/8 (100%) | 8/8 (100%) | 8/8 (100%) |
| unknown | 0/6 (0%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| **all** | 2/40 (5%) | 39/40 (97%) | 39/40 (97%) | 40/40 (100%) |

Average seconds per answer: none 4.5s · brain 4.6s · brain+calc 5.2s · brain+quote 2.8s

Modes: `none` = the model alone. `brain` = plus the notes retrieved from the vault. `brain+calc` = plus a calculator tool.

Read `none` as a general-purpose assistant with no company knowledge. It cannot pass routing (it does not know the queue names) or "not in vault" (it was never told the rule). What matters there is what it does instead: refuse, or invent an answer.

## Misses

| Mode | Test | Expected | Got |
|---|---|---|---|
| none | quote-01 | 46542.8 | $54,000.00 (based on assumed prices of $1,200/unit for laptop and $150/unit for setup) |
| none | quote-02 | 28760.8 | Please consult the current Fieldstone IT price list or client agreement for accurate prici |
| none | quote-03 | 11496.48 | Please contact your Fieldstone IT account manager for current pricing and setup fees. |
| none | quote-04 | 5285.76 | I cannot provide specific pricing as I do not have access to Fieldstone IT's internal sale |
| none | quote-05 | 16870.8 | Please contact your Fieldstone IT account manager for a specific quote. |
| none | quote-06 | 5405.76 | Insufficient data to calculate line total |
| none | quote-07 | 34907.1 | I cannot provide specific pricing; please contact your Fieldstone IT account manager for a |
| none | quote-08 | 33795.0 | Please contact your Fieldstone IT account manager for current pricing. |
| none | quote-09 | 9779.1 | Insufficient data to calculate |
| none | quote-10 | 42375.0 | Please contact your Fieldstone IT account manager for a specific quote. |
| none | quote-11 | 1988.0 | Please contact your Fieldstone IT account manager for current pricing. |
| none | quote-12 | 34901.75 | Please consult the current Fieldstone IT price list or client agreement for accurate prici |
| none | quote-13 | 2982.0 | I cannot provide a specific price without the hardware model, configuration, and client co |
| none | quote-14 | 10402.56 | $18,000 |
| none | quote-15 | 29000.0 | I cannot provide a specific price; please consult Fieldstone IT sales for a formal quote. |
| none | quote-16 | 11952.0 | Please consult the current Fieldstone IT price list or client agreement for accurate prici |
| none | lookup-01 | ['15 minutes'] | Check the specific client SLA and internal incident management policy, but typically a Cri |
| none | lookup-02 | ['$225'] | Please check your specific Service Level Agreement (SLA) or contact your account manager f |
| none | lookup-03 | ['$165'] | Please consult the internal rate sheet or Sales team for the current business-hours projec |
| none | lookup-04 | ['30 days'] | Please consult internal IT policies or your IT manager. |
| none | lookup-05 | ['sunday', '2 am'] | I don't know |
| none | lookup-06 | ['call'] | Verify the user's identity |
| none | lookup-07 | ['1 hour'] | Immediately (or within 24 hours, per standard best practice) |
| none | lookup-08 | ['service director'] | Information not available |
| none | lookup-09 | ['3 business days'] | Typically 2 weeks, but please verify with your specific contract or HR policy. |
| none | lookup-10 | ['change ticket'] | A formally submitted and approved Change Request (CR) with specific technical details and  |
| none | triage-01 | service_desk | IT Support |
| none | triage-02 | quote | Procurement |
| none | triage-04 | onboarding | HR |
| none | triage-06 | service_desk | IT Support |
| none | triage-07 | onboarding | IT |
| none | triage-08 | other | Business Development |
| none | unknown-01 | NOT IN VAULT | Price varies by brand and model; please specify the exact monitor for a quote. |
| none | unknown-02 | NOT IN VAULT | No, we do not generally support Linux desktops for clients. |
| none | unknown-03 | NOT IN VAULT | Unknown |
| none | unknown-04 | NOT IN VAULT | I don't have that information. |
| none | unknown-05 | NOT IN VAULT | Please contact the Fieldstone IT sales team for a specific quote. |
| none | unknown-06 | NOT IN VAULT | I do not have access to Fieldstone IT's specific client SLAs or internal policies. |
| brain | quote-15 | 29000.0 | NOT IN VAULT, ask the Service Director |
| brain+calc | quote-15 | 29000.0 | NOT IN VAULT, ask the Service director |
