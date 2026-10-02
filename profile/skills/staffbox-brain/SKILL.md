---
name: staffbox-brain
description: Answer from the company's brain (the Markdown vault) and log every task. Use for any question about prices, policies, procedures, people or past work at this company.
---
# Staffbox brain

Before you answer anything about the company:

1. Run `staffbox context ~/staffbox/vault "<the question>"` and read every note it prints. `company.md` is always first.
2. Answer only from those notes. Name the note you used. If the notes do not answer it, say `NOT IN VAULT` and name who to ask from `people.md`. Never guess a price, date or policy.
3. To price a line, run `staffbox quote ~/staffbox/vault "<the request>"` and use its line total exactly; add `--sku`, `--qty` or `--opt species=maple` if it picked the wrong item. If it says the item is not priced, the answer is NOT IN VAULT. For any other arithmetic, use the terminal (`python3 -c "print(...)"`), not your head.
4. After the task, append one line: `staffbox log ~/staffbox/vault "<what was asked>" "<what you did>" --could-not "<what you could not do>"`. Never edit `log.md` directly; old lines are never changed.
5. To add knowledge, write a new note with frontmatter (`type`, `owner`, `updated`, `source`) and run `staffbox check ~/staffbox/vault`. Fix every problem it lists before you finish.
