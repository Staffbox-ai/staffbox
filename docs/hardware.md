# Hardware: ways to run a Staffbox unit

The software is the same on every box: Ollama serving open-weight models on the box itself, Hermes Agent as the worker, the brain, the quote action and the scorecard. What changes is which models fit and how fast they answer. Pick the smallest box whose **scorecard on the site's own test set** passes.

| | Staffbox mini | Staffbox mini Pro (proposed default) | Staffbox Studio | Staffbox custom |
|---|---|---|---|---|
| Machine | Apple Mac mini | Apple Mac mini, M5 Pro, 48 GB | Apple Mac Studio | A tower or rack server with an NVIDIA GPU, running Linux |
| Memory | 16 to 64 GB unified (M6 up to 32 GB; M5 Pro up to 64 GB) | 48 GB unified, 307 GB/s memory bandwidth (Apple spec for M5 Pro) | 36 to 256 GB unified (M5 Max up to 128 GB; M5 Ultra up to 256 GB, 512 GB announced for late October) | GPU memory decides: 24 GB (RTX 3090) runs the 27B class |
| Apple list price, 1 Oct 2026 | from $899 (M6), from $1,699 (M5 Pro) | from $1,699 for the M5 Pro; the price of the 48 GB option is not checked yet | from $2,499 (M5 Max), from $5,499 (M5 Ultra) | depends on the build |
| Models | 8B class; 14B on 32 GB and up | 8B and 27B class: `qwen3.8:27b` used 17 GB at 64K context on the Dell, leaving room for macOS and Hermes | 27B to 70B class; several sites or departments on one box | 8B to 27B on one 24 GB GPU |
| Measured so far | M4, 16 GB: `qwen3:8b` with the quote action scored 40/40 (Fieldstone IT) and 39/40 (Peachtree); demo answers in 2 to 7 s after a clean install. 14B with Hermes' 64K context did not fit in 16 GB. | Not yet measured. See the [bench plan](#bench-plan-mac-mini-m5-pro-48-gb) below. | Not yet measured on a Studio. | Dell Precision 5820 + RTX 3090: `qwen3:8b` 40/40 and 39/40, `qwen3.8:27b` 40/40 and 39/40 with the quote action; 0.4 to 5 s per answer |
| Installer | `scripts/install.sh` (one command) | `scripts/install.sh` with `MODEL=qwen3.8:27b EXTRA_MODELS=qwen3:8b` | `scripts/install.sh` (same; set `MODEL` to the bigger model) | Manual today, steps below |
| Fits | One site, one to three jobs | One site whose scorecard needs the 27B, or room to move up later without new hardware | A larger site, a franchisor serving many locations, or a site whose test needs a 27B+ model | An IT provider's own rack or a site that already runs Linux servers |

Prices are Apple's US list prices on apple.com on 1 October 2026; memory upgrades cost extra. "Measured" rows link to raw results in [`evals/results/`](../evals/results/) and [measurements.md](measurements.md).

## Bench plan: Mac mini M5 Pro, 48 GB

The mini Pro becomes the default unit only if it passes this plan. Until then, the 16 GB mini with the 8B stays the measured option.

**Why 48 GB:** on the 16 GB M4, 14B with Hermes' 64K context did not fit, changing the context size cost about 100 s, and Ollama hung under heavy disk load. The 27B scored higher than the 8B on the Dell (see [measurements.md](measurements.md)), and 48 GB is the smallest memory size that should hold it at 64K context with room left over.

**Setup**

1. Clean install with `MODEL=qwen3.8:27b EXTRA_MODELS=qwen3:8b scripts/install.sh`. Log the macOS version, the Ollama version and `sysctl hw.memsize`.
2. Load the 27B model at 64K context and check that `ollama ps` shows `100% GPU`. Log the model size, `memory_pressure` and the time of the first answer from cold.

**Scorecards** (`brain+quote` mode, model kept warm, nothing else running)

Run each test set with both models: `examples/fieldstone-it/tests.jsonl`, `examples/peachtree-cabinet-works/tests.jsonl`, `examples/fieldstone-it/tests-heldout-ugly.jsonl` and `tests-heldout-ugly2.jsonl`.

```sh
bin/staffbox eval examples/fieldstone-it/vault examples/fieldstone-it/tests.jsonl \
  --model qwen3.8:27b --modes brain+quote \
  --out evals/results/$(date +%F)-fieldstone-it-tests-mac-mini-m5pro-48gb-qwen3.8-27b-quote-v2.3
```

**Speed**

- `python3 scripts/bench.py qwen3:8b` and `python3 scripts/bench.py qwen3.8:27b` (1, 2 and 4 streams). Run once with the installer's settings and once with `OLLAMA_NUM_PARALLEL=4`. On the Dell, the 27B never ran requests in parallel (speculative decoding forces one slot), so expect a flat line for it.
- Run one Hermes task from the demo script with the 27B and log the wall time.

**Soak:** loop the Fieldstone scorecard with the 27B for one hour. Log `memory_pressure` and swap use (`sysctl vm.swapusage`) every minute. Any swap or a hung Ollama counts as a fail.

**Pass bar** (Hadi's call to confirm)

| Check | Pass |
|---|---|
| 27B scorecards | At least the Dell 27B result: 40/40 Fieldstone, 39/40 Peachtree; at least 19/20 and 15/15 on the messy sets (the 8B result on the M4 mini) |
| 27B answer time | p90 under 10 s per scorecard answer, one request at a time |
| 8B | Same scores as on the M4 mini, and faster |
| Soak | No swap, no hung Ollama, no wrong-price quotes |

**Decision:** pass → the mini Pro 48 GB ships as the default unit with the 27B. 27B accurate but too slow → ship the 8B on this box and keep the 27B for queued work. Fail on memory → step up to 64 GB or a Studio.

Results go in `evals/results/` and a row in [measurements.md](measurements.md), as for every other machine.

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
