# Staffbox

[![ci](https://github.com/Staffbox-ai/staffbox/actions/workflows/ci.yml/badge.svg)](https://github.com/Staffbox-ai/staffbox/actions/workflows/ci.yml)

**Staffbox runs Hermes Agent on local open-weight models on a Mac mini to draft quotes and replies from a company's own price list, and on a 16 GB Mac mini it scored 351 of 360 messy generated requests with 0 wrong totals in 475 graded answers.**

The proof, all on fictional demo companies and graded by machine (no customer site has run it yet):
- **Exact quotes on a 16 GB Mac mini.** `qwen3:8b` with the brain and quote action v2.4, 6 October 2026: Fieldstone IT 40/40, Peachtree Cabinet Works 39/40, messy requests 19/20 and 15/15, generated requests 351/360. Of the 11 misses, 10 declined and asked the customer and 1 was a routing miss. Files: [Fieldstone](evals/results/2026-10-06-fieldstone-it-tests-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md) · [Peachtree](evals/results/2026-10-06-peachtree-cabinet-works-tests-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md) · [messy 20](evals/results/2026-10-06-fieldstone-it-tests-heldout-ugly-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md) · [messy 15](evals/results/2026-10-06-fieldstone-it-tests-heldout-ugly2-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md) · [generated 204](evals/results/2026-10-06-fieldstone-it-tests-generated-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md) · [generated 156](evals/results/2026-10-06-peachtree-cabinet-works-tests-generated-mac-mini-m4-16gb-qwen3-8b-quote-v2.4.md).
- **The brain does most of the work, not the model.** Without the brain, `qwen3:8b` scored 1/40 on Fieldstone IT; with the brain and the quote action, 40/40. A cloud model (Gemini Pro) with the same brain matched on clean requests (39/40) but scored 14/20 on messy ones, where the local 8B model with the quote action scored 19/20. Details: [Scorecard](#scorecard) and [evals/results](evals/results/).
- **Every graded answer is public.** Browse each answer, miss and raw output in the [Hugging Face scorecard Space](https://huggingface.co/spaces/staffbox/scorecard), or read the files in [`evals/results/`](evals/results/).

Staffbox is an open stack for running an agentic AI worker on a Mac mini inside a small company's own network. It runs an open-source agent on local open-weight models. Its memory is a **brain**: a plain Markdown vault the company owns and can open in Obsidian. The company's existing IT provider installs and manages the box. The worker goes live on a workflow only after a **scorecard** on that company's own past requests meets a pass mark agreed in advance. It writes drafts only: there is no sending code, and a person sends.

This repository is the stack. The managed service, the hardware program and the partner channel are what Staffbox, Inc. sells around it.

## Quick start: see it work in two minutes, then install a unit in about an hour

```sh
git clone https://github.com/Staffbox-ai/staffbox && cd staffbox
bin/staffbox check examples/peachtree-cabinet-works/vault          # is the brain healthy?
bin/staffbox context examples/peachtree-cabinet-works/vault "How long does a painted order take?"   # what the worker reads
bin/staffbox quote examples/peachtree-cabinet-works/vault "30 shaker doors 24x30 in maple, painted"   # the quote action, no model
bin/staffbox ask examples/fieldstone-it/vault "A user is locked out of MFA. What do we do first?" --model qwen3:8b
bin/staffbox eval examples/fieldstone-it/vault examples/fieldstone-it/tests.jsonl --model qwen3:8b --modes brain,brain+quote
```

Python 3 standard library only, so there's nothing to install. `ask` and `eval` need [Ollama](https://ollama.com) running a model.

To install a full unit (Ollama, Hermes Agent, the worker profile and the brain) on a Mac mini, follow [docs/install.md](docs/install.md). The one command:

```sh
xcode-select --install          # click Install on the Mac's screen once; about 10 minutes
git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src && ~/staffbox-src/scripts/install.sh
```

Two demo brains, both fictional, each with a 40-question test set (16 quotes, 10 policy or runbook questions, 8 emails to route, and 6 questions the brain *cannot* answer, where the right answer is "not in the vault" plus who to ask):
- `examples/peachtree-cabinet-works`: a Georgia cabinet-door maker. Price list, species and finish surcharges, volume discounts, five policies, three SOPs.
- `examples/fieldstone-it`: an IT provider. Hardware price list with setup fees, labor rates, response times, backups, patching, approvals, onboarding, offboarding and MFA runbooks, three client notes with their own rules, and inbox queues.

## Running Hermes Agent with local models? Read these

Hermes Agent refuses local model windows below 64K tokens, and Ollama's default window is 4K on machines with less than 24 GiB of GPU memory ([Ollama docs](https://docs.ollama.com/context-length)). The repo fix is in [docs/hermes-64k-context.md](docs/hermes-64k-context.md). The longer guides on staffbox.ai:

| Guide | What it answers |
|---|---|
| [Hermes Agent for business](https://staffbox.ai/hermes-agent/) | What Hermes Agent gives and what Staffbox adds |
| [Hermes Agent 64K context](https://staffbox.ai/hermes-agent/64k-context/) | qwen3, Ollama and what we know about the 64K minimum |
| [Hermes Agent with Ollama](https://staffbox.ai/hermes-agent/ollama/) | The Ollama settings that worked for us |
| [Best local model for Hermes Agent](https://staffbox.ai/hermes-agent/local-models/) | Local models compared by their scores on quoting |
| [Is Hermes Agent safe for company data?](https://staffbox.ai/hermes-agent/security/) | What we turn off, and why |
| [Install Hermes Agent on a Mac mini](https://staffbox.ai/hermes-agent/install-on-mac-mini/) | The Staffbox installer, step by step |

Staffbox is not affiliated with Nous Research. Hermes Agent is Nous Research's open-source project (MIT).

## For businesses: send three requests, get the drafts back within 2 business days

Send three recurring requests you get (quotes, orders, routine questions) and get back what Staffbox would have drafted, misses included. Free, drafts back within 2 business days: [staffbox.ai/free-ai-quote-test](https://staffbox.ai/free-ai-quote-test/) or sales@staffbox.ai.

## For IT providers: an AI offer you install and manage for your clients

Staffbox is sold and supported through managed IT providers, who install and manage the box. The partner offer: [staffbox.ai/partners/msp-ai-offer](https://staffbox.ai/partners/msp-ai-offer/) or partners@staffbox.ai.

## Scorecard

Both demo test sets, 40 questions each, graded by machine, 30 September 2026, on a Dell Precision 5820 with an RTX 3090 through Ollama. `qwen3:8b` is the model a 16 GB Mac mini runs; accuracy depends on the model, speed on the box (see [docs/measurements.md](docs/measurements.md)).

| Model | Brain | Alone | + brain | + brain + calculator | + brain + quote action |
|---|---|---|---|---|---|
| `qwen3:8b` | Fieldstone IT | 1/40 | 33/40 | 31/40 | **40/40** |
| `qwen3:8b` | Peachtree Cabinet Works | 1/40 | 31/40 | 33/40 | **39/40** |
| `qwen3.8:27b` | Fieldstone IT | 2/40 | 39/40 | 39/40 | **40/40** |
| `qwen3.8:27b` | Peachtree Cabinet Works | 2/40 | 39/40 | 37/40 | **39/40** |

**On the Mac mini itself, 2 October 2026** (M4, 16 GB, clean install, `qwen3:8b` kept warm, quote action v2.3): Fieldstone IT **40/40** (average 2.4 s, p90 5.3 s), Peachtree **39/40** (2.9 s, p90 5.2 s), messy requests **19/20** (1.2 s) and **15/15** (1.1 s). Files: [Fieldstone](evals/results/2026-10-02-fieldstone-it-tests-mac-mini-m4-16gb-qwen3-8b-quote-v2.3.md) · [Peachtree](evals/results/2026-10-02-peachtree-cabinet-works-tests-mac-mini-m4-16gb-qwen3-8b-quote-v2.3.md) · [messy 20](evals/results/2026-10-02-fieldstone-it-tests-heldout-ugly-mac-mini-m4-16gb-qwen3-8b-quote-v2.3.md) · [messy 15](evals/results/2026-10-02-fieldstone-it-tests-heldout-ugly2-mac-mini-m4-16gb-qwen3-8b-quote-v2.3.md). These are single-request timings with the model already loaded; requests from several people at once still queue.

**Earlier, on the same box** (overnight 30 Sep to 1 Oct, before the clean install and tuning): `qwen3:8b` with the quote action scored **40/40** on Fieldstone IT and **39/40** on Peachtree, the same as on the Dell. Speed varied a lot on this box: median 19 s per answer on Fieldstone and 112 s on Peachtree, with some answers over 3 minutes. `qwen3:14b` does not fit comfortably in 16 GB: 32 of its answers hit the 10-minute timeout, so its scorecard measures the box, not the model. Files: [Fieldstone 8B](evals/results/2026-10-01-fieldstone-it-mac-mini-m4-16gb-qwen3-8b-quote.md) · [Peachtree 8B](evals/results/2026-10-01-peachtree-cabinet-works-mac-mini-m4-16gb-qwen3-8b-quote.md) · [Fieldstone 14B](evals/results/2026-10-01-fieldstone-it-mac-mini-m4-16gb-qwen3-14b-quote.md).

What this shows:
- **The brain is most of the gain.** Alone, both models refused most questions or made answers up. With the brain they answered the policy and runbook questions and declined the ones the brain does not cover.
- **Quotes were the weak spot, and the quote action fixes them.** The 8B model found the right numbers but picked the wrong discount tier or skipped a step; a calculator did not help. With the quote action, a short routing call reads the item, quantity and options, and code prices the line from the vault's own price list, surcharge and discount tables (`staffbox/actions.py`). Every quote in both sets was then exact, and unpriced items (walnut, a 30x36 door, iPads) were declined instead of guessed.
- **The remaining miss** is the same in both models: "Are you hiring?" was answered "not in vault" instead of being routed to the `other` queue.
- The test prompts are templated and the data is fictional. A real site's scorecard uses 30 to 50 of its own past requests.

### A model option that is not Qwen (2 October 2026)

Some buyers cannot use models from certain vendors. Georgia's state IT standard SS-22-002 (revised 30 June 2025) lists "Alibaba products and services" and DeepSeek as prohibited on executive-branch state systems, and Qwen is developed by Alibaba Cloud. Whether a locally run open-weight model falls under that is the buyer's decision, so we also score OpenAI's open-weight `gpt-oss-20b` (Apache 2.0) with the same brain and quote action:

| `gpt-oss-20b` + quote action v2.3, Dell RTX 3090 | Score |
|---|---|
| Fieldstone IT, 40 | **39/40** |
| Peachtree Cabinet Works, 40 | **40/40** |
| Messy requests, clean held-out 15 | **15/15** |

The one miss: asked about clients outside Georgia, it repeated the in-state response times instead of saying the brain does not cover them. The model needs about 14 GB, so it is a 32 GB Mac mini or Mac Studio option; its speed on Apple hardware is not measured yet. Files: [Fieldstone](evals/results/2026-10-02-fieldstone-it-tests-dell-3090-gpt-oss-20b-quote-v2.3.md) · [Peachtree](evals/results/2026-10-02-peachtree-cabinet-works-tests-dell-3090-gpt-oss-20b-quote-v2.3.md) · [messy 15](evals/results/2026-10-02-fieldstone-it-tests-heldout-ugly2-dell-3090-gpt-oss-20b-quote-v2.3.md).

### Messy requests, held out, and a cloud comparison (2 October 2026)

Real quote requests arrive with typos, forwarded threads, signatures, two items in one email, "two dozen", and "no setup". Two sets test that. [`tests-heldout-ugly.jsonl`](examples/fieldstone-it/tests-heldout-ugly.jsonl) (20 requests) was held out from the first quote action, then **used while we fixed v2**, so its later scores are not a clean held-out result. [`tests-heldout-ugly2.jsonl`](examples/fieldstone-it/tests-heldout-ugly2.jsonl) (15 requests) was committed before the changes it measured and is the clean one. Expected totals are computed by code from the vault's price list.

| Fieldstone IT, graded by machine | Clean 40 | Messy 20 | Messy 15 |
|---|---|---|---|
| Gemini Pro (cloud), alone | 5/40 | 0/20 | not run |
| Gemini Pro (cloud) + the same brain | 39/40 | 14/20 | not run |
| `qwen3.8:27b` + quote action v1 | 40/40 | 16/20 | not run |
| `qwen3:8b` + quote action v2.3 (current) | **40/40** | **19/20** | **15/15** |

- **A cloud model with the same brain is as accurate on clean requests.** The brain is most of the product; the model is replaceable.
- **On messy requests the quote action makes the difference.** The cloud model refused six requests it could have priced. The 8B model with the quote action priced them exactly, and still declined the ones it should: unstocked items, "same laptops as last time", and a vague bundle.
- **The one miss is a safe one.** For "40 laptops, half with setup and half without", the volume discount depends on how the lines are split, so the worker asks the customer to confirm the split instead of pricing it.
- **The record includes our own bug.** Quote action v2 let the small model drop setup fees by default and scored 11/20; [that run is kept](evals/results/2026-10-02-dell-3090-qwen3-8b-fieldstone-heldout-ugly-action-v2.md). v2.1 to v2.3 enforce the rules in code: setup is only dropped when the request says so; a model-picked item must be named or described in the request, otherwise the worker asks; and the same item on two lines must add up to a number in the request.

The data is fictional and 35 requests is a small sample. A real site's held-out set is 10 of its own past quotes, graded blind by the site.

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
| `staffbox/`, `bin/staffbox` | The CLI: `check`, `context`, `ask`, `quote`, `log`, `eval`, `review`, `addtest`, `inbox`; `actions.py` holds the quote action, `inbox.py` the draft-only mailbox door |
| `examples/peachtree-cabinet-works/`, `examples/fieldstone-it/` | The two demo brains and their test sets (`make_tests.py` rebuilds each; CI checks that they match) |
| `profile/vault/` | The empty brain a new site starts from, Obsidian-ready |
| `profile/skills/staffbox-brain/` | The Hermes skill: read context, answer only from it, log every task |
| `scripts/install.sh` | Sets up Ollama, the Hermes profile, the brain, the skill, the demo brains and a `zero` shortcut on a Mac mini |
| `scripts/bench.py` | Tokens per second at 1, 2 and 4 concurrent requests |
| `scripts/hooks/pre-commit` | Stops a broken brain or an edited log line from being committed |
| `evals/results/` | Every published scorecard, with raw answers |
| `docs/` | [install](docs/install.md), [connect from your computer](docs/connect.md), [hardware](docs/hardware.md), [brain](docs/brain.md), [architecture](docs/architecture.md), [data policy](docs/data-policy.md), [measurements](docs/measurements.md), [Hermes 64K context](docs/hermes-64k-context.md) |

## How a site goes live

Each step is a command, so the loop is the product, not a promise.

| Step | What happens | Command |
|---|---|---|
| 1. Test set | 30 to 50 of the site's real past requests with the answers it actually sent. 10 are held back and graded blind by the site. | a `tests.jsonl` file |
| 2. Brain | Seed the brain from the site's own price sheets, terms and procedures. | `staffbox check VAULT` |
| 3. Score | Run the test set. For quotes the scorecard shows: share priced, share right with no edits, and 90th-percentile time. A refusal counts as a miss. | `staffbox eval VAULT TESTS --modes brain+quote` |
| 4. Fix | Fix in order: brain first, then a tool, then a bigger model. Re-run after each fix. | `staffbox eval` again |
| 5. Gate | A task type goes live only if it meets the bar agreed before day 0. | `staffbox review NEW.jsonl --bar quote=85` (exit code 3 = not live) |
| 6. Work | Requests land in a folder (or a synced mailbox). Draft replies land in a drafts folder, citing the pricing notes and their dates. A person sends. There is no sending code in Staffbox. | `staffbox inbox VAULT --in requests/ --drafts drafts/` |
| 7. Monthly review | Re-run the test, diff against last month (fixed, regressed, new), and turn every correction into a new test. | `staffbox review NEW.jsonl --prev OLD.jsonl` · `staffbox addtest` |

## Data policy in one paragraph

Inference and the brain stay on the customer's LAN. Connected tools such as email and the CRM behave exactly as they do today. Cloud burst to a frontier model is off until the customer turns it on with their own API key. Remote access by the managing IT provider or by Staffbox is logged and consented. On cancellation the customer keeps the box and the brain, and Staffbox deletes its copies. Full text in `docs/data-policy.md`.

## Status

30 September 2026: v0.1. One unit runs inside Staffbox itself ("Zero"). No customer site is live yet; the first trial install is planned for October.

## Security

Report a vulnerability to security@staffbox.ai, not in a public issue. Policy and scope: [SECURITY.md](SECURITY.md). How a unit is hardened: [docs/data-policy.md](docs/data-policy.md).

## License

MIT for everything in this repository. Hermes Agent and Ollama carry their own MIT licenses. Model weights carry their own licenses, so check them before you ship.

Staffbox, Inc. (in formation, Delaware) is a team of six, staff and contractors. Sales: sales@staffbox.ai · IT providers: partners@staffbox.ai · Security: security@staffbox.ai · [staffbox.ai](https://staffbox.ai)
