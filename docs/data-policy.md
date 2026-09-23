DRAFT TEMPLATE, 23 Sep 2026. Not legal advice. Counsel to review before use.

# Staffbox, Inc. — Customer MSA and Data Handling Policy: Outline

This is an outline for two customer-facing documents: (A) the Master Services Agreement ("MSA") governing the sale and subscription of Hermes Agent, and (B) a plain-language data handling policy. Both are outlines only; full text requires counsel drafting.

## Part A: Master Services Agreement (Outline)

1. **Parties and structure.** Staffbox, Inc. ("Staffbox") and the customer named on the Order Form ("Customer"). The MSA is the master terms; each Order Form incorporates it by reference and specifies unit count, pricing, and site address.

2. **Order Form.** Each Order Form specifies: number of Hermes Agent units, onboarding fee ($0 for the first 100 units company-wide, $1,800/unit thereafter), monthly subscription fee ($595/unit/month), install site(s), install date, and any Partner (VAR) of record.

3. **Hardware title.** Title to the Mac mini hardware transfers to Customer upon [delivery / payment of onboarding fee — SPECIFY]. Staffbox retains no security interest in the hardware absent a separate financing arrangement. Software and models remain licensed, not sold (see Section 8).

4. **Subscription services.** The monthly subscription fee covers: software updates, Tier 2/3 support, model updates, and continued access to the Hermes Agent software license. Subscription is billed monthly in advance/arrears [SPECIFY] and may be paid by [ACH / credit card / invoice].

5. **Cancellation — "keep the box."** Customer may cancel the subscription at any time with [30] days' notice. Upon cancellation, Customer keeps the Mac mini hardware (no return required), but loses access to software updates, hosted support, and any cloud-connected features. Local data already stored on the unit remains under Customer's control, subject to the data handling policy (Part B).

6. **Fees and payment terms.** Standard payment terms (e.g., net 15/30), late payment consequences, and price-change notice period (e.g., 30/60 days for renewal terms) [SPECIFY].

7. **Term.** Initial subscription term (e.g., month-to-month after onboarding, or 12-month initial term) and renewal mechanics [SPECIFY].

8. **License grant.** Staffbox grants Customer a non-exclusive, non-transferable license to use the Hermes Agent software for Customer's internal business purposes for the subscription term. No source code or model weights are transferred; local models run under Staffbox's or third-party (e.g., Ollama-distributed open-weight model) license terms as applicable.

9. **Warranty.** Hardware warranty of [1 year, manufacturer pass-through plus Staffbox support]; software provided "as is" except for a limited warranty that the service will perform materially as documented; no warranty of uninterrupted or error-free operation; AI-generated outputs are not warranted to be accurate and require human review for consequential decisions.

10. **Limitation of liability.** Mutual cap on liability (e.g., fees paid in the prior 12 months), exclusion of indirect/consequential damages, carve-outs typically for confidentiality breaches, IP infringement, and gross negligence/willful misconduct [SPECIFY CAP AND CARVE-OUTS WITH COUNSEL].

11. **Indemnification.** Mutual indemnities for IP infringement (Staffbox) and misuse/unlawful use (Customer) [SPECIFY].

12. **Data ownership.** Customer retains ownership of all data processed or stored on its Hermes Agent unit, including its Obsidian vault contents and conversation history.

13. **Termination for cause.** Either party may terminate for uncured material breach; Staffbox may suspend service for non-payment after notice.

14. **General terms.** Governing law (Delaware), assignment, notices, entire agreement, amendment, force majeure — standard boilerplate [TO BE DRAFTED BY COUNSEL].

## Part B: Customer-Facing Data Handling Policy (Outline)

15. **Where inference happens.** By default, all AI inference (model reasoning) and memory storage (the Obsidian vault) run locally on the Hermes Agent Mac mini at Customer's site. No customer data leaves the local network by default.

16. **Connected tools.** When Customer connects Hermes Agent to other tools or services it already uses (e.g., email, calendar, internal systems), those integrations behave the same as if Customer had connected them directly — Staffbox does not add new data flows beyond what the integration itself requires, and access follows the permissions Customer grants to that integration.

17. **Cloud burst — off by default.** Hermes Agent may optionally use cloud-hosted models for tasks that exceed local model capability ("cloud burst"). This feature is **off by default** and must be affirmatively enabled by Customer. When enabled, only the specific request data needed is sent, using an API key that Customer controls (Customer's own cloud AI provider account/key), not a shared Staffbox key, so Customer retains visibility into and control over any cloud usage and its own provider's data terms apply.

18. **Remote access by Staffbox staff.** If Staffbox support staff need remote access to a Customer's unit for troubleshooting, that access is: (a) logged (who accessed, when, what was viewed or changed), and (b) either initiated by Customer (e.g., a support request) or explicitly consented to by Customer in advance for a specific session. Staffbox does not access Customer units proactively or without consent.

19. **Partner (VAR) access.** If Customer's unit is supported by a channel partner, the same logging-and-consent rules in Section 18 apply to the partner's remote access, per the VAR Program Terms.

20. **Data deletion on cancellation.** Upon subscription cancellation, Customer may request that Staffbox delete any data Staffbox holds about the account (e.g., billing and support records) within [30] days, subject to legal retention requirements. Because inference and memory run locally, most Customer data (the Obsidian vault and local model state) remains solely on the Customer-owned hardware and is deleted only if and when Customer chooses to wipe the device.

21. **Security.** Local-first architecture reduces the attack surface for customer data. [ADD: encryption at rest, network isolation defaults, patching cadence — SPECIFY WITH ENGINEERING AND COUNSEL.]

22. **Policy updates.** Staffbox will notify Customers of material changes to this data handling policy at least [30] days before they take effect.

**Note:** This is a structural outline only. Full MSA and policy text, including all bracketed terms, must be drafted and reviewed by counsel before use with any customer.
