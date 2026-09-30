# Architecture

One box per site. Four layers, all replaceable.

1. Hardware: a Mac mini on the customer's LAN, on a shelf or a rack tray, managed by the customer's MSP like any other endpoint.
2. Models: Ollama serves open-weight models locally over an OpenAI-compatible API on localhost:11434. Optional cloud burst goes through a fallback chain the customer controls with their own keys.
3. Agent: Hermes Agent runs as a profile with a persona (SOUL.md), a config pointing at the local model, and tools for files, shell, email and MCP servers the MSP enables.
4. Brain: a Markdown vault (see brain.md). `staffbox context` puts company.md and the relevant notes in front of the agent before it acts, and `staffbox log` appends one line after. People own the brain; the agent appends and never rewrites. `staffbox eval` scores the whole thing against the site's own test set.

Known constraints, September 2026: Hermes Agent requires a 64K context window; on 16 GB that means an 8B model and slow tool use. 32 GB is the recommended build. Requests to one Ollama instance queue at default parallelism; tune OLLAMA_NUM_PARALLEL after measuring with scripts/bench.py.
