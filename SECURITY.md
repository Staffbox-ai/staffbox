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

## How a unit is hardened

See [docs/data-policy.md](docs/data-policy.md): disk encryption, firewall, key-only SSH, model server on 127.0.0.1, cloud AI off, and the default tool restrictions.
