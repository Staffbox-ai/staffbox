DRAFT for counsel, 2 Oct 2026. Not legal advice. Bracketed items are decisions still open.

# Staffbox data handling and security

What happens to a customer's data, where it lives, who can reach it, and what we have not done yet. Plain language first; the contract terms that implement it are at the end.

## 1. Where the work happens

- A Staffbox unit is a Mac mini (or Mac Studio) on the customer's own network.
- The AI models run on that box through Ollama, which listens on `127.0.0.1` only.
- The company's knowledge (the "brain") is a folder of Markdown files on that box. The customer owns it.
- Cloud AI is **off**. It is turned on only if the customer asks in writing and supplies its own provider key. Then only the request that needs it is sent, under the customer's own provider terms.

## 2. What the worker can do by default

| Path | What it can do | How that is enforced |
|---|---|---|
| Mailbox door (`staffbox inbox`) | Reads request files from one folder; writes draft replies to another; appends one line per draft to the log | There is no sending code in Staffbox. A person opens the drafts and sends them. If the folders are synced with the customer's mail system, the mail stays where that system already keeps it; Staffbox adds no new copy outside the box. |
| Chat assistant (Hermes Agent profile) | Reads files; writes new notes and its own task list | The installer turns off shell, code execution, browser, computer control, web access, outside connections, delegation and scheduled jobs. A site can turn any of them on, in writing. |
| The brain | Read by both paths | Kept in git; every change is versioned and can be undone. `log.md` is append-only and `staffbox check` fails if an old line changes. |

## 3. The box itself (security baseline)

| Control | Default | Status |
|---|---|---|
| Disk encryption | FileVault on before any customer data is loaded | The installer stops if FileVault is off (a demo box with no customer data can override with DEMO_UNIT=1) and records the status in the unit's install proof; the IT provider turns it on and keeps the recovery key |
| Firewall | macOS firewall on, stealth mode on | Set at install |
| Remote access | SSH with keys only, one key per named person; password login off | Set at install; sessions agreed with the customer's IT contact in advance; macOS records each SSH login |
| Model server | Listens on 127.0.0.1 only | Set at install |
| Updates | macOS and model updates monthly, applied by the IT provider after the test set still passes | Process |
| Backups | Nightly copy of the brain to customer-chosen storage | [planned: not in the installer yet] |
| Secrets | No cloud keys on the box unless the customer adds its own | Installer reports any keys it finds |

## 4. The free test (before a site signs)

Requests sent through the staffbox.ai form go to a private, encrypted (AES-256) store in Staffbox's AWS account with all public access blocked, and to Hadi's email. They are used only to run the test. We delete them within 14 days of sending the results and confirm in writing. [Today deletion is a manual step; an automatic expiry rule is open.] Send redacted examples if you prefer.

## 5. Remote access by Staffbox or the IT provider

Only by named key, only for a session the customer's IT contact has agreed, and logged by macOS. We do not access a unit proactively.

## 6. Leaving

On cancellation the customer keeps the brain. During a free pilot the box is collected or wiped in front of the customer; once the first month is paid, the box is the customer's. Staffbox deletes its own copies within 14 days and confirms in writing.

## 7. What we have not done yet

No SOC 2 or other certification. No cyber or errors-and-omissions insurance confirmed. No single sign-on. No accessibility conformance report (VPAT). Staffbox, Inc. is in formation. We say so before anyone signs.

## 8. Contract terms (outline for counsel)

1. **Parties.** Staffbox, Inc. and the customer on the order form.
2. **Order form.** Units, site, install date, IT provider of record, and price: founding sites (first 100 units company-wide) $0 onboarding and $595 a month per unit for as long as the unit is live; from unit 101, $1,800 onboarding and $695 a month per unit. Mac Studio sites quoted per site.
3. **Hardware title.** Staffbox's during a free pilot; passes to the customer when the first monthly fee is paid.
4. **Term.** Month to month; the customer may end at any time (the site promises "cancel any time"); Staffbox gives [30] days' notice before ending service.
5. **Service.** Software and model updates, monitoring through the IT provider, and one hour a month of review that re-runs the test set.
6. **Outputs.** Drafts for a person to check. No warranty that outputs are accurate.
7. **Liability.** Mutual cap of [fees paid in the prior 12 months, or a fixed amount]; exclusions and carve-outs per counsel.
8. **Data.** The customer owns its data and brain. Sections 1 to 6 above are incorporated.
9. **Deletion.** 14 days, confirmed in writing, subject only to records the law requires us to keep.
10. **Changes to this policy.** [30] days' notice of material changes.
11. **Law.** [Georgia or Delaware; counsel to confirm].
