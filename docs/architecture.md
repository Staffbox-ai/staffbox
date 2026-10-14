# Architecture

One box per site. Four layers, all replaceable.

1. Hardware: a Mac mini on the customer's LAN, on a shelf or a rack tray, managed by the customer's MSP like any other endpoint.
2. Models: Ollama serves open-weight models locally over an OpenAI-compatible API on 127.0.0.1:11434, from one LaunchAgent (`ai.staffbox.ollama`) with a 64K context. The installer sets `fallback_providers: []`: there is no cloud fallback. A customer can add its own provider key later (dashboard > Keys); that is a manual, per-site decision, not something the installer sets up.
3. Agent: Hermes Agent (pinned commit, see install.md) runs as a profile with a persona (SOUL.md) and a config pointing at the local model. The installer turns off shell, code execution, browser, computer control, web, outside connections, delegation, scheduled jobs, speech and image generation, verifies they are off, and limits file writes to `~/staffbox/vault` and `~/staffbox/work`. There is no email-sending tool; replies are drafts (`staffbox inbox`). A site can turn tools on or add MCP servers in writing; the unit card records what is on.
4. Brain: a Markdown vault (see brain.md). `staffbox context` puts company.md and the relevant notes in front of the agent before it acts, and `staffbox log` appends one line after. People own the brain; the agent appends and never rewrites. `staffbox eval` scores the whole thing against the site's own test set.

Known constraints, September 2026: Hermes Agent requires a 64K context window; on 16 GB that means an 8B model and slow tool use. 32 GB is the recommended build. Requests to one Ollama instance queue at default parallelism; tune OLLAMA_NUM_PARALLEL after measuring with scripts/bench.py.

Updates are manual: the IT provider runs the site's scorecard, updates, re-runs the installer (which re-checks the tool lock-down) and runs the scorecard again; rollback is a reinstall at the previous Hermes pin plus the brain from backup. See [install.md](install.md#updating-manual-on-purpose).
