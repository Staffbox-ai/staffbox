# Hardware: three ways to run a Staffbox unit

The software is the same on all three: Ollama serving open-weight models on the box itself, Hermes Agent as the worker, the brain, the quote action and the scorecard. What changes is which models fit and how fast they answer. Pick the smallest box whose **scorecard on the site's own test set** passes.

| | Staffbox mini | Staffbox Studio | Staffbox custom |
|---|---|---|---|
| Machine | Apple Mac mini | Apple Mac Studio | A tower or rack server with an NVIDIA GPU, running Linux |
| Memory | 16 to 64 GB unified (M6 up to 32 GB; M5 Pro up to 64 GB) | 36 to 256 GB unified (M5 Max up to 128 GB; M5 Ultra up to 256 GB, 512 GB announced for late October) | GPU memory decides: 24 GB (RTX 3090) runs the 27B class |
| Apple list price, 1 Oct 2026 | from $899 (M6), from $1,699 (M5 Pro) | from $2,499 (M5 Max), from $5,499 (M5 Ultra) | depends on the build |
| Models | 8B class; 14B on 32 GB and up | 27B to 70B class; several sites or departments on one box | 8B to 27B on one 24 GB GPU |
| Measured so far | M4, 16 GB: `qwen3:8b` with the quote action scored 40/40 (Fieldstone IT) and 39/40 (Peachtree); demo answers in 2 to 7 s after a clean install. 14B with Hermes' 64K context did not fit in 16 GB. | Not yet measured on a Studio. | Dell Precision 5820 + RTX 3090: `qwen3:8b` 40/40 and 39/40, `qwen3.8:27b` 40/40 and 39/40 with the quote action; 0.4 to 5 s per answer |
| Installer | `scripts/install.sh` (one command) | `scripts/install.sh` (same; set `MODEL` to the bigger model) | Manual today, steps below |
| Fits | One site, one to three jobs | A larger site, a franchisor serving many locations, or a site whose test needs a 27B+ model | An IT provider's own rack or a site that already runs Linux servers |

Prices are Apple's US list prices on apple.com on 1 October 2026; memory upgrades cost extra. "Measured" rows link to raw results in [`evals/results/`](../evals/results/) and [measurements.md](measurements.md).

## Staffbox Studio

Install exactly as on a mini, choosing a bigger model:

```sh
MODEL=qwen3.8:27b ~/staffbox-src/scripts/install.sh
```

Then run the site's scorecard with that model and compare it with the 8B result before go-live. A Studio can also hold several worker profiles (one per department or location), each with its own brain, on one machine.

## Staffbox custom (Linux + NVIDIA)

The CLI is standard-library Python and runs unchanged on Linux. Until the installer supports Linux:

1. Install the NVIDIA driver and [Ollama for Linux](https://ollama.com/download/linux). Bind it to the machine itself: set `OLLAMA_HOST=127.0.0.1:11434` in the systemd unit.
2. Pull the model: `ollama pull qwen3:8b` (and `qwen3.8:27b` on 24 GB GPUs).
3. Install Hermes Agent with Nous Research's installer, create the worker profile, and set `fallback_providers: []` in its config so nothing falls back to a cloud model.
4. `git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src`, link `bin/staffbox` onto your PATH, copy `examples/` and `profile/vault/` to `~/staffbox/`.
5. Prove it: `staffbox eval ~/staffbox/examples/fieldstone-it/vault ~/staffbox/examples/fieldstone-it/tests.jsonl --modes brain+quote`.
