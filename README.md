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
bin/staffbox ask examples/peachtree-cabinet-works/vault "Quote 30 shaker doors 24x30 in maple, painted" --model qwen3:8b
bin/staffbox eval examples/peachtree-cabinet-works/vault examples/peachtree-cabinet-works/tests.jsonl --model qwen3:8b
```

Python 3 standard library only, so there's nothing to install. `ask` and `eval` need [Ollama](https://ollama.com) running a model.

`examples/peachtree-cabinet-works` is a fictional Georgia cabinet-door maker. It has a price list, surcharges, volume discounts, five policies, three SOPs and a 40-question test set: 16 quotes, 10 policy questions, 8 emails to route, and 6 questions the brain *cannot* answer, where the right answer is "not in the vault, ask the plant manager".

## Scorecard

Peachtree test set, 40 questions, graded by machine, 30 September 2026. Both models ran on a Dell Precision 5820 with an RTX 3090 through Ollama. `qwen3:8b` is the model a 16 GB Mac mini runs; accuracy depends on the model and speed depends on the box (the mini runs about 20 tokens a second, see [docs/measurements.md](docs/measurements.md)).

| Task | 8B alone | 8B + brain | 8B + brain + calc | 27B alone | 27B + brain | 27B + brain + calc |
|---|---|---|---|---|---|---|
| Quote a line (16) | 0% | 56% | 62% | 0% | 93% | 81% |
| Policy question (10) | 10% | 100% | 100% | 20% | 100% | 100% |
| Route an email (8) | 0% | 87% | 100% | 0% | 100% | 100% |
| Say "not in vault" (6) | 0% | 100% | 100% | 0% | 100% | 100% |
| **All 40** | **2%** | **80%** | **85%** | **5%** | **97%** | **92%** |

What this shows:
- **The brain is most of the gain.** On their own, both models refused most questions and made some up: a "1-year limited warranty", and a $2,408.70 price for walnut, which Peachtree does not sell. With the brain, both answered every policy question and declined all six questions the brain does not cover.
- **Quotes on the 8B model are the weak spot.** It picks the right numbers from the notes but gets the arithmetic wrong, and sometimes copies the worked example from the SOP. The calculator added one quote. The next rungs of the fix ladder are a quote tool that does the whole calculation, or the bigger model; the 27B already gets 15 of 16 with the brain alone.
- **The calculator did not help the 27B.** It lost two quotes when the model fed the tool its own rounding. We report that as measured.

Full scorecards with every miss: [8B](evals/results/2026-09-30-dell-3090-qwen3-8b.md) · [27B](evals/results/2026-09-30-dell-3090-qwen3.8-27b.md). Two harness bugs were found and fixed while producing them; both are noted in the files.

Every row was produced by `staffbox eval` and graded automatically. Every answer, raw, is in [`evals/results/`](evals/results/).

## The stack

| Layer | Component | License |
|---|---|---|
| Hardware | Apple Mac mini, 32 GB unified memory recommended (16 GB is the floor we measured); Mac Studio when a site's test needs a bigger model | n/a |
| Agent | [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research, with the `staffbox-brain` skill | MIT |
| Models | Open-weight models served by Ollama. Cloud burst is optional and runs on the customer's own key | Ollama MIT; model licenses vary |
| Brain | A Markdown vault with frontmatter and `[[links]]`, checked by `staffbox check`, with an append-only log. See [docs/brain.md](docs/brain.md) | Your content |
| Scorecard | `staffbox eval`: the site's own test set, run and graded before go-live and again every month | MIT (this repo) |
| Persona | `profile/SOUL.md.example`, the worker's standing instructions | MIT (this repo) |

## What is in this repo

| Path | What it is |
|---|---|
| `staffbox/`, `bin/staffbox` | The CLI: `check`, `context`, `ask`, `log`, `eval` |
| `examples/peachtree-cabinet-works/` | The demo brain and its test set (`make_tests.py` rebuilds it; CI checks that it matches) |
| `profile/vault/` | The empty brain a new site starts from, Obsidian-ready |
| `profile/skills/staffbox-brain/` | The Hermes skill: read context, answer only from it, log every task |
| `scripts/install.sh` | Sets up Ollama, the Hermes profile, the brain and the skill on a Mac mini |
| `scripts/bench.py` | Tokens per second at 1, 2 and 4 concurrent requests |
| `scripts/hooks/pre-commit` | Stops a broken brain or an edited log line from being committed |
| `evals/results/` | Every published scorecard, with raw answers |
| `docs/` | [brain](docs/brain.md), [architecture](docs/architecture.md), [data policy](docs/data-policy.md), [measurements](docs/measurements.md) |

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
