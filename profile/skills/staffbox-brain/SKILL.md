---
name: staffbox-brain
description: Answer from the company's brain (the Markdown vault) and log every task. Use for any question about prices, policies, procedures, people or past work at this company.
---
# Staffbox brain

The default install gives you file tools only: no shell, no web, no outside connections. Customer replies go out through the mailbox door (`staffbox inbox`), which writes drafts a person sends.

Before you answer anything about the company:

1. Read `~/staffbox/vault/company.md`, then `~/staffbox/vault/Home.md`, then the notes it links to that match the question. Price questions: read the notes tagged `pricing`.
2. Answer only from those notes. Name the note you used. If the notes do not answer it, say `NOT IN VAULT` and name who to ask from `people.md`. Never guess a price, date or policy.
3. For a quote, say that the mailbox door prices it exactly, and give the line items you found. Do not do arithmetic in your head.
4. Never edit or delete an existing line of `log.md`. Add knowledge only as a new note with frontmatter (`type`, `owner`, `updated`, `source`).

If this site has turned the terminal on in writing, you may also run `staffbox context ~/staffbox/vault "<question>"`, `staffbox quote ~/staffbox/vault "<request>"` and `staffbox log ...`.
