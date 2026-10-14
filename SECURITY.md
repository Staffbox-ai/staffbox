# Security

## Reporting a vulnerability

Email **security@staffbox.ai** with what you found and how to reproduce it. Please do not open a public issue for a vulnerability. We will acknowledge within two business days and keep you updated until it is fixed. We do not run a bug bounty yet.

## If a unit is affected

Staffbox tells the affected customer and their IT provider within one business day of confirming an issue that touches their data, with what happened, what was exposed and what to do. Evidence on the unit is preserved before any fix.

## Scope

This repository (the `staffbox` CLI, installer, brain templates and examples). Hermes Agent and Ollama have their own security policies; report issues in them upstream as well.

## Known Hermes advisories and this configuration (14 Oct 2026)

As of 14 October 2026, three CVEs name Hermes Agent or its ecosystem. CVE-2026-7397 (symlink bypass of the file-write deny list on macOS) was fixed in Hermes Agent 0.9.0 in April 2026; Staffbox units install a later version. CVE-2026-7396 (path traversal in the WeChat Work messaging adapter) applies only when that adapter is running; Staffbox units do not configure any messaging gateway. CVE-2026-6829 affects hermes-webui, a separate third-party interface Staffbox does not install. Staffbox's installer turns off Hermes' shell, code execution, browser, computer control, web, outside connections, delegation, scheduled jobs, speech and image generation, keeps the model server and dashboard on the Mac itself (127.0.0.1), and contains no code that sends email.

Sources: NVD entries for each CVE; NousResearch/hermes-agent commit 311dac1 and issue #8733; hermes-webui v0.50.34; Cloud Security Alliance research note, 4 May 2026.

## Write containment and its limits

- **Tool lock-down fails closed.** After turning tool groups off, the installer reads `hermes -p <profile> tools list` and stops with an error if any locked group is still on or is not listed. The unit card records the tools that are on and the Hermes commit.
- **Write safe-root.** The installer sets `HERMES_WRITE_SAFE_ROOT=~/staffbox/vault:~/staffbox/work` in the worker profile's `.env`, its shortcut and the dashboard LaunchAgent. Hermes' `file` tools (`write_file`, `patch`) then refuse any path outside those folders, with no approval prompt. Hermes also always refuses writes to `~/.ssh`, `~/.aws`, `.env` and its own secret stores. Limits, from Hermes' own security docs: this guards the `file` tools only; it is defence-in-depth and "does not sandbox a hostile or compromised agent"; the `terminal` tool (off on Staffbox units) runs as the same user and is not covered. With the safe-root set, the worker also cannot write its own profile skills or Hermes state outside those folders.
- **Config read-only.** The worker's `config.yaml` and `.env` are `chmod a-w` after install. This is a speed bump: Hermes saves config by writing a new file and renaming it over the old one, and any process running as the same user can `chmod` it back. `install.sh --harden-macos` (admin password) sets `chflags schg` instead, which an ordinary user cannot undo and which blocks edit, replace and delete.
- **Recommended for IT providers:** run the worker as a separate **standard** macOS user (admin only during the install), as described in [docs/install.md](docs/install.md#recommended-a-separate-standard-user-for-the-worker). That is the control that stops a same-user process from undoing the others.
- **Tool resolution.** The check covers the profile's tool configuration, which the Hermes CLI and dashboard chat use. A site that turns on Hermes' coding "focus" mode or sets `HERMES_TUI_TOOLSETS` changes what the dashboard chat gets; Staffbox units do neither.

## How a unit is hardened

See [docs/data-policy.md](docs/data-policy.md): disk encryption, model server on 127.0.0.1, cloud AI off, and the default tool restrictions (default install, no sudo); firewall, key-only SSH and the config lock (opt-in `--harden-macos`, run by the IT provider with an admin password).
