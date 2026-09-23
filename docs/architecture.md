# Architecture

One box per site. Four layers, all replaceable.

1. Hardware: a Mac mini on the customer's LAN, on a shelf or a rack tray, managed by the customer's MSP like any other endpoint.
2. Models: Ollama serves open-weight models locally over an OpenAI-compatible API on localhost:11434. Optional cloud burst goes through a fallback chain the customer controls with their own keys.
3. Agent: Hermes Agent runs as a profile with a persona (SOUL.md), a config pointing at the local model, and tools for files, shell, email and MCP servers the MSP enables.
4. Memory: a Markdown vault. The agent reads company.md and the relevant SOPs before acting, and appends to log.md after. Humans own the vault; the agent appends, never rewrites.

Known constraints, September 2026: Hermes Agent requires a 64K context window; on 16 GB that means an 8B model and slow tool use. 32 GB is the recommended build. Requests to one Ollama instance queue at default parallelism; tune OLLAMA_NUM_PARALLEL after measuring with scripts/bench.py.
