# Staffbox

[![ci](https://github.com/Staffbox-ai/staffbox/actions/workflows/ci.yml/badge.svg)](https://github.com/Staffbox-ai/staffbox/actions/workflows/ci.yml)

**Your first agentic worker. One box, on your network, with a brain you own and a score you can check.**

Staffbox is an open stack for running an agentic AI worker on a Mac mini inside a small company's own network. It runs an open-source agent on local open-weight models. Its memory is a **brain**: a plain Markdown vault the company owns and can open in Obsidian. The company's existing IT provider installs and manages the box. The worker goes live on a workflow only after a **scorecard** shows it answering that company's own past requests correctly.

This repository is the stack. The managed service, the hardware program and the partner channel are what Staffbox, Inc. sells around it.

## See it in two minutes

```sh
git clone https://github.com/Staffbox-ai/staffbox && cd staffbox
bin/staffbox check examples/peachtree-cabinet-works/vault          # is the brain healthy?
bin/staffbox context examples/peachtree-cabinet-works/vault "How long does a painted order take?"   # what the worker reads
bin/staffbox quote examples/peachtree-cabinet-works/vault "30 shaker doors 24x30 in maple, painted"   # the quote action, no model
bin/staffbox ask examples/fieldstone-it/vault "A user is locked out of MFA. What do we do first?" --model qwen3:8b
bin/staffbox eval examples/fieldstone-it/vault examples/fieldstone-it/tests.jsonl --model qwen3:8b --modes brain,brain+quote
```

Python 3 standard library only, so there's nothing to install. `ask` and `eval` need [Ollama](https://ollama.com) running a model.

Two demo brains, both fictional, each with a 40-question test set (16 quotes, 10 policy or runbook questions, 8 emails to route, and 6 questions the brain *cannot* answer, where the right answer is "not in the vault" plus who to ask):
- `examples/peachtree-cabinet-works`: a Georgia cabinet-door maker. Price list, species and finish surcharges, volume discounts, five policies, three SOPs.
- `examples/fieldstone-it`: an IT provider. Hardware price list with setup fees, labor rates, response times, backups, patching, approvals, onboarding, offboarding and MFA runbooks, three client notes with their own rules, and inbox queues.

## Scorecard

Both demo test sets, 40 questions each, graded by machine, 30 September 2026, on a Dell Precision 5820 with an RTX 3090 through Ollama. `qwen3:8b` is the model a 16 GB Mac mini runs; accuracy depends on the model, speed on the box (see [docs/measurements.md](docs/measurements.md)).

| Model | Brain | Alone | + brain | + brain + calculator | + brain + quote action |
|---|---|---|---|---|---|
| `qwen3:8b` | Fieldstone IT | 1/40 | 33/40 | 31/40 | **40/40** |
| `qwen3:8b` | Peachtree Cabinet Works | 1/40 | 31/40 | 33/40 | **39/40** |
| `qwen3.8:27b` | Fieldstone IT | 2/40 | 39/40 | 39/40 | **40/40** |
| `qwen3.8:27b` | Peachtree Cabinet Works | 2/40 | 39/40 | 37/40 | **39/40** |

**On the Mac mini itself** (M4, 16 GB, the unit we leave at a pilot; overnight 30 Sep to 1 Oct, same harness): `qwen3:8b` with the quote action scored **40/40** on Fieldstone IT and **39/40** on Peachtree, the same as on the Dell. Speed varied a lot on this box: median 19 s per answer on Fieldstone and 112 s on Peachtree, with some answers over 3 minutes. `qwen3:14b` does not fit comfortably in 16 GB: 32 of its answers hit the 10-minute timeout, so its scorecard measures the box, not the model. Files: [Fieldstone 8B](evals/results/2026-10-01-fieldstone-it-mac-mini-m4-16gb-qwen3-8b-quote.md) · [Peachtree 8B](evals/results/2026-10-01-peachtree-cabinet-works-mac-mini-m4-16gb-qwen3-8b-quote.md) · [Fieldstone 14B](evals/results/2026-10-01-fieldstone-it-mac-mini-m4-16gb-qwen3-14b-quote.md).

What this shows:
- **The brain is most of the gain.** Alone, both models refused most questions or made answers up. With the brain they answered the policy and runbook questions and declined the ones the brain does not cover.
- **Quotes were the weak spot, and the quote action fixes them.** The 8B model found the right numbers but picked the wrong discount tier or skipped a step; a calculator did not help. With the quote action, a short routing call reads the item, quantity and options, and code prices the line from the vault's own price list, surcharge and discount tables (`staffbox/actions.py`). Every quote in both sets was then exact, and unpriced items (walnut, a 30x36 door, iPads) were declined instead of guessed.
- **The remaining miss** is the same in both models: "Are you hiring?" was answered "not in vault" instead of being routed to the `other` queue.
- The test prompts are templated and the data is fictional. A real site's scorecard uses 30 to 50 of its own past requests.

Full scorecards with every miss and every raw answer: Fieldstone [8B](evals/results/2026-09-30-fieldstone-it-dell-3090-qwen3-8b.md) · [27B](evals/results/2026-09-30-fieldstone-it-dell-3090-qwen3.8-27b-64k.md); Peachtree [8B](evals/results/2026-09-30-peachtree-cabinet-works-dell-3090-qwen3-8b.md) · [27B](evals/results/2026-09-30-peachtree-cabinet-works-dell-3090-qwen3.8-27b-64k.md). The first Peachtree runs (30 September, before the quote action) are kept unedited next to them.

## The stack

| Layer | Component | License |
|---|---|---|
| Hardware | Three tiers, see [docs/hardware.md](docs/hardware.md): **mini** (Mac mini, 32 GB recommended, 16 GB measured), **Studio** (Mac Studio, for 27B+ models or many sites on one box), **custom** (Linux + NVIDIA GPU, measured on an RTX 3090) | n/a |
| Agent | [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research, with the `staffbox-brain` skill | MIT |
| Models | Open-weight models served by Ollama. Cloud burst is optional and runs on the customer's own key | Ollama MIT; model licenses vary |
| Brain | A Markdown vault with frontmatter and `[[links]]`, checked by `staffbox check`, with an append-only log. See [docs/brain.md](docs/brain.md) | Your content |
| Scorecard | `staffbox eval`: the site's own test set, run and graded before go-live and again every month | MIT (this repo) |
| Persona | `profile/SOUL.md.example`, the worker's standing instructions | MIT (this repo) |

## What is in this repo

| Path | What it is |
|---|---|
| `staffbox/`, `bin/staffbox` | The CLI: `check`, `context`, `ask`, `quote`, `log`, `eval`; `actions.py` holds the quote action |
| `examples/peachtree-cabinet-works/`, `examples/fieldstone-it/` | The two demo brains and their test sets (`make_tests.py` rebuilds each; CI checks that they match) |
| `profile/vault/` | The empty brain a new site starts from, Obsidian-ready |
| `profile/skills/staffbox-brain/` | The Hermes skill: read context, answer only from it, log every task |
| `scripts/install.sh` | Sets up Ollama, the Hermes profile, the brain, the skill, the demo brains and a `zero` shortcut on a Mac mini |
| `scripts/bench.py` | Tokens per second at 1, 2 and 4 concurrent requests |
| `scripts/hooks/pre-commit` | Stops a broken brain or an edited log line from being committed |
| `evals/results/` | Every published scorecard, with raw answers |
| `docs/` | [install](docs/install.md), [connect from your computer](docs/connect.md), [hardware](docs/hardware.md), [brain](docs/brain.md), [architecture](docs/architecture.md), [data policy](docs/data-policy.md), [measurements](docs/measurements.md) |

## How a site goes live

1. Collect 30 to 50 of the site's real past requests and their right answers. That is the test set.
2. Seed the brain from the site's own price sheets, terms and procedures.
3. Run the scorecard. Fix in this order: the brain first, then a tool, then a bigger model, and re-run each time.
4. Go live only on the workflows that pass. Each month's review hour re-runs the test, and every correction becomes a new test.

## Data policy in one paragraph

Inference and the brain stay on the customer's LAN. Connected tools such as email and the CRM behave exactly as they do today. Cloud burst to a frontier model is off until the customer turns it on with their own API key. Remote access by the managing IT provider or by Staffbox is logged and consented. On cancellation the customer keeps the box and the brain, and Staffbox deletes its copies. Full text in `docs/data-policy.md`.

## Status

30 September 2026: v0.1. One unit runs inside Staffbox itself ("Zero"). No customer site is live yet; the first trial install is planned for October.

## License

MIT for everything in this repository. Hermes Agent and Ollama carry their own MIT licenses. Model weights carry their own licenses, so check them before you ship.

Staffbox, Inc. (in formation, Delaware). Founder: Hadi Irvani. [staffbox.ai](https://staffbox.ai)
