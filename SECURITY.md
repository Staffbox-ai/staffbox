# Security

## Reporting a vulnerability

Email **security@staffbox.ai** with what you found and how to reproduce it. Please do not open a public issue for a vulnerability. We will acknowledge within two business days and keep you updated until it is fixed. We do not run a bug bounty yet.

## If a unit is affected

Staffbox tells the affected customer and their IT provider within one business day of confirming an issue that touches their data, with what happened, what was exposed and what to do. Evidence on the unit is preserved before any fix.

## Scope

This repository (the `staffbox` CLI, installer, brain templates and examples). Hermes Agent and Ollama have their own security policies; report issues in them upstream as well.

## How a unit is hardened

See [docs/data-policy.md](docs/data-policy.md): disk encryption, firewall, key-only SSH, model server on 127.0.0.1, cloud AI off, and the default tool restrictions.
