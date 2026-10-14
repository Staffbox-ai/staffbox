# Hermes Agent on Ollama: set a 64K context window

**The fix: give Ollama a 65,536-token window in two places, the Ollama server and the Hermes profile, and keep that one size for every run.** Hermes Agent refuses a local model window below 64K tokens, and Ollama's default is smaller on most small machines, so an untuned setup fails before it answers anything. Every Staffbox Mac mini score was measured at this setting.

Longer version with background: [staffbox.ai/hermes-agent/64k-context](https://staffbox.ai/hermes-agent/64k-context/).

## Why it fails out of the box

| Fact | Source |
|---|---|
| Hermes Agent refuses local model windows below 64K tokens. | Staffbox setup notes, 28 September 2026 |
| Ollama's default window depends on GPU memory: 4k below 24 GiB, 32k from 24 to 48 GiB, 256k at 48 GiB and above. | [docs.ollama.com/context-length](https://docs.ollama.com/context-length) |
| If Hermes does not pass a window size, Ollama falls back to a 2,048-token window. | comment in [`scripts/install.sh`](../scripts/install.sh) |

## What the installer sets

[`scripts/install.sh`](../scripts/install.sh) does not build a separate model. It sets the window on the server and in the Hermes profile.

**1. The Ollama server.** The installer runs Ollama as a LaunchAgent (`~/Library/LaunchAgents/ai.staffbox.ollama.plist`) with these environment variables:

| Variable | Value | Why |
|---|---|---|
| `OLLAMA_HOST` | `127.0.0.1:11434` | model server reachable from this Mac only |
| `OLLAMA_CONTEXT_LENGTH` | `65536` | the 64K window Hermes requires |
| `OLLAMA_KEEP_ALIVE` | `24h` | keeps the model warm between requests |
| `OLLAMA_MAX_LOADED_MODELS` | `1` | one model in memory at a time |
| `OLLAMA_FLASH_ATTENTION` | `1` | as set by the installer |
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | as set by the installer |

To try the same window by hand without the LaunchAgent, Ollama's documented form is:

```sh
OLLAMA_CONTEXT_LENGTH=65536 ollama serve
```

**2. The Hermes profile.** In `~/.hermes/profiles/<profile>/config.yaml`, under `model:`, the installer sets:

```yaml
model:
  default: qwen3:8b
  provider: ollama
  base_url: http://localhost:11434/v1
  context_length: 65536
  ollama_num_ctx: 65536
fallback_providers: []
```

`fallback_providers: []` means no silent cloud fallback.

**3. Check it.** With a request running, `ollama ps` shows the window in its `CONTEXT` column ([Ollama docs](https://docs.ollama.com/context-length)).

## Another way: a model variant with the window built in

Staffbox's own units have also run `-64k` model variants, built from an Ollama Modelfile with `num_ctx 65536`. The installer does not do this; it is an option if you cannot set server environment variables. Standard Ollama syntax:

```sh
printf 'FROM qwen3:8b\nPARAMETER num_ctx 65536\n' > Modelfile
ollama create qwen3:8b-64k -f Modelfile
```

Then set `default: qwen3:8b-64k` in the Hermes profile.

## What was measured at 64K, and what was not

**Measured** (fictional demo companies, graded by machine; 16 GB Mac mini M4, `qwen3:8b` + brain + quote action v2.4, 6 October 2026, one request at a time, model warm):

| Test set | Score | Average / 90th-percentile seconds |
|---|---|---|
| Fieldstone IT, 40 | 40/40 | 2.3 / 5.3 |
| Peachtree Cabinet Works, 40 | 39/40 | 2.5 / 4.4 |
| Messy requests, 20 | 19/20 | 1.2 / 2.3 |
| Messy requests, 15 | 15/15 | 1.1 / 1.7 |
| Generated, Fieldstone 204 + Peachtree 156 | 351/360 | 1.6 / 2.1 and 3.2 / 3.4 |

0 wrong totals in 475 answers. Files are in [`evals/results/`](../evals/results/) (names starting `2026-10-06-` and ending `quote-v2.4`). The 30 September `qwen3.8:27b` runs on a Dell RTX 3090 were also at 64K (files ending `-64k`).

**Not measured:**
- **Prompts longer than 40,960 tokens.** That is `qwen3:8b`'s native window. Ollama accepts the 65,536 setting, but no Staffbox test sends a prompt that long; the test prompts are far shorter.
- **A 14B model at 64K on 16 GB.** `qwen3:14b` did not fit comfortably: 32 of its answers hit the 10-minute timeout, so that run measures the box, not the model ([file](../evals/results/2026-10-01-fieldstone-it-mac-mini-m4-16gb-qwen3-14b-quote.md)).
- **Concurrent requests.** All timings above are one request at a time; requests from several people at once queue.

## Two things that cost time

- **Changing the window reloads the model.** On a 16 GB Mac mini that takes about 100 seconds, so keep one context size for every run.
- **Ollama can hang** when the disk is busy or a model unloads between steps. Restart it with `launchctl kickstart -k gui/$UID/ai.staffbox.ollama`.

Staffbox is not affiliated with Nous Research, which makes Hermes Agent.
