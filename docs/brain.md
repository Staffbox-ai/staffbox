# The brain

The brain is a folder of Markdown notes: the company's own knowledge, readable by people in Obsidian (or any editor) and by the worker through `staffbox`. People own it. The worker reads it before it acts, appends to the log after, and never rewrites what a person wrote.

## The rules a note follows

```markdown
---
type: policy            # index | company | sop | policy | reference | person | log | note
owner: plant manager    # the role that answers for this note
updated: 2026-09-30     # YYYY-MM-DD, never in the future
source: terms of sale   # where the facts came from
aliases: [lead time, turnaround]   # optional: words people use for this, helps search
tags: [pricing]                    # optional
---
# Lead times
... plain text, tables, and [[links]] to other notes ...
```

- `company.md` is required and is read before every task. It says who the worker reports to, and the rule "not in the vault means say so".
- `log.md` is required and append-only. `staffbox log` writes one line per task; `staffbox check` fails if an existing line changed (when the vault is in git).
- Links use Obsidian's `[[note-name]]`. A broken link fails the check.
- Note names are unique across folders, so links never guess.

## How the worker reads it

`staffbox context VAULT "question"` picks what the worker reads, in this order, inside a character budget:

1. `company.md`, always.
2. The best four notes by BM25 over the body, with the title, aliases and tags counted three times.
3. The notes the best hit links to. An SOP that links to the price list pulls the price list in.

This is deliberately simple. Small local models do badly when asked to call a search tool themselves (measured 23 to 27 September 2026 on an 8B model: invented files, wrong tool calls), and well when the right notes are placed in front of them. It needs no embedding model and no index to rebuild, and the answer to "why did it say that" is a list of files.

## Price notes the quote action reads

Notes tagged `pricing` hold the price book; code reads them, the model never does the arithmetic. Beyond the SKU table, option surcharges and volume discounts, a trade price book can use (all optional; examples in `examples/ponce-electric-supply/vault`):

| In the vault | What code does |
|---|---|
| `Unit` column: `ft`, `m`, `ea`, `box of 100`, `stick` with "10 ft stick" in the row | quantities converted to the item's unit (pieces to boxes, feet to sticks, reels to feet) only when whole; otherwise it asks |
| "500 ft reel", "Minimum cut: 25 feet", "Cut charge: $7.50 per cut" (or "cut charge $3 under 50 m" in a row's notes cell) | per-length lines with a cut charge, and a decline below the minimum cut |
| `Stock` column: `stocked` or anything else (`special order`) | special-order items are declined and sent to a person, never priced or substituted |
| `- **Contractor level**: 12% off list` (or a Level / Discount table); a customer note with `price_level: contractor` | applied only when the request or the customer's note names it; otherwise list, and the answer says which level was used |
| A table "Product group (TERMS) / Surcharge / Effective" | surcharge on items whose description names a bracketed term, using the row in effect today |
| `synonyms.md`: "Customers write / We mean" | the shop's shorthand ("2p", "12-2 nm") rewritten into price-book words before the request is read |

Order on a line: goods, quantity break, price level, group surcharge, cut charge, rounding to the cent at each step.

## The checks

`staffbox check VAULT` reports: missing frontmatter fields, unknown `type`, bad or future `updated` dates, broken links, duplicate note names, a missing `company.md` or `log.md`, and any edit to an existing log line. Install `scripts/hooks/pre-commit` in the vault's git repo and a broken brain cannot be committed.

## The scorecard

`staffbox eval VAULT TESTS.jsonl` runs a site's test set (30 to 50 of its own past requests, with the right answers) three ways and grades every answer automatically:

| Mode | What the model gets |
|---|---|
| `none` | the question and the company name |
| `brain` | plus the notes `staffbox context` retrieves |
| `brain+calc` | plus a calculator: the model writes `CALC:` lines and gets exact results back |

Each rung is one step of the fix ladder (vault, then tool, then a bigger model), so a site sees what each step bought. Results go to `<out>.md` (the scorecard) and `<out>.jsonl` (every answer, raw). See `evals/`.
