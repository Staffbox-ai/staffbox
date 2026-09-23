# Staffbox

**Your first agentic worker. One box, on your network.**

Staffbox is an open stack for running an agentic AI worker on a Mac mini inside a small company's own network: an open-source agent on local open-weight models, with a plain-text vault as the company's memory, installed and managed by the company's existing IT provider. This repository is the stack. The managed service ($695 a month including a monthly workflow review; founding sites $595 for life), the hardware program and the partner channel are what Staffbox, Inc. sells around it.

Status, 23 September 2026: working draft. One unit runs inside Staffbox itself. Nothing is installed at a customer site yet.

## The stack

| Layer | Component | License |
|---|---|---|
| Hardware | Apple Mac mini, 32 GB unified memory recommended (16 GB is the floor we measured) | n/a |
| Agent | [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research | MIT |
| Models | Open-weight models served by [Ollama](https://ollama.com); cloud burst optional, on the customer's own key | Ollama MIT; model licenses vary |
| Memory | A Markdown vault (Obsidian-compatible) the agent reads before it acts and appends to after | Your content |
| Persona | `profile/SOUL.md.example`, the worker's standing instructions | MIT (this repo) |

## What is in this repo

- `scripts/install.sh`: checks that Ollama and Hermes Agent are installed (it tells you where to get them if not), pulls a model, and creates a Hermes profile from the persona and vault templates. Read it before you run it; it is short.
- `scripts/bench.py`: measures tokens per second at one, two and four concurrent requests against a local Ollama model. Run it before you promise anyone a team size.
- `scripts/model.py`: the twelve-month unit-economics model behind the pricing, with every input labelled fact or guess. Change the numbers; it prints the scenarios.
- `profile/SOUL.md.example`: the persona template for a company's first worker.
- `profile/vault/`: the vault skeleton: `company.md`, `log.md`, `sops/`.
- `docs/architecture.md`, `docs/data-policy.md`, `docs/measurements.md`.

## Measured, not promised

On an Apple M4 Mac mini with 16 GB running an 8B model through Ollama at default settings, 23 September 2026: about 20 tokens a second per request at one, two and four concurrent requests, with requests queuing, so four people asking at once each waited about two minutes for a 200-word answer. Hermes Agent requires a 64K context window; at 64K the same machine completed a read-and-answer task in under ten minutes with a browser also running. That is the floor. The next three units are 32 GB builds and the numbers will be published here.

## Data policy in one paragraph

Inference and memory stay on the customer's LAN. Connected tools such as email and the CRM behave exactly as they do today. Cloud burst to a frontier model is off until the customer turns it on with their own API key. Remote access by the managing MSP or by Staffbox is logged and consented. On cancellation the customer keeps the box and the vault; Staffbox deletes its copies. Full text in `docs/data-policy.md`.

## License

MIT for everything in this repository. Hermes Agent and Ollama carry their own MIT licenses; model weights carry their own licenses, check before you ship.

Staffbox, Inc. (in formation, Delaware). Founder: Hadi Irvani. staffbox.ai
