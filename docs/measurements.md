# Measurements

All numbers here are measured on real hardware and dated. Add rows; do not edit old ones.

| Date | Machine | Model | Streams | Per-stream tok/s | Wall for 220 tokens each | Notes |
|---|---|---|---|---|---|---|
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b via Ollama, default parallelism | 1 | 20.6 | 65 s | includes model load |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 2 | 20.4 | 112 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 4 | 20.5 | 127 s | requests queued |
| 2026-10-01 | Mac mini M4, 16 GB, freshly erased, Staffbox installer | qwen3:8b via Ollama 0.35.0, flash attention, KV cache q8_0 | 1 | 20.2 | 11.2 s | model already warm |
| 2026-10-01 | same | qwen3:8b | 2 | 20.3 | 21.8 s | requests queued (one at a time) |
| 2026-10-01 | same | qwen3:8b | 4 | 20.3 | 43.5 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b at 64K context, Hermes Agent one-shot task | 1 | n/a | 5 to 10 min | read a vault file, answer, write a log line; browser also running |

Next: three 32 GB units, same tests, plus OLLAMA_NUM_PARALLEL 2 and 4.

## Accuracy (scorecard)

| Date | Machine | Model | Test set | Model alone | + brain | + brain + calc | File |
|---|---|---|---|---|---|---|---|
| 2026-09-30 | Dell Precision 5820, RTX 3090 | qwen3:8b (Mac mini class) | Peachtree, 40 | 1/40 | 32/40 | 34/40 | evals/results/2026-09-30-dell-3090-qwen3-8b.md |
| 2026-09-30 | Dell Precision 5820, RTX 3090 | qwen3.8-27b | Peachtree, 40 | 2/40 | 39/40 | 37/40 | evals/results/2026-09-30-dell-3090-qwen3.8-27b.md |

The same 8B run on the 16 GB Mac mini was stopped partway through: another job on the mini loaded a vision model, and 16 GB holds one model at a time. It needs a re-run on a quiet box.

## Demo answer times on the clean unit (1 Oct 2026)

Mac mini M4 16 GB after the installer, model kept warm, one context size for every caller (so no reloads between tools):

| Task | Path | Seconds |
|---|---|---|
| Price 12 monitors with setup (quote action) | `staffbox ask` | 1 to 2 |
| Runbook answer (MFA lockout) | `staffbox ask` | 7 |
| Route an email | `staffbox ask` | 3 |
| Explain the offer in three sentences | Hermes Agent, 64K context | 23 |
| Turn dock notes into a checklist | Hermes Agent | 28 |

Before keeping the model warm and using one context size, a switch between Hermes and the CLI could force a full reload; on the cluttered pre-wipe install we saw up to about 100 s for that.

## KV cache: q8_0 vs q4_0 (1 Oct 2026, Mac mini M4 16 GB, qwen3:8b, Ollama 0.35.0, flash attention)

| KV cache type | Model + cache in memory | Fieldstone scorecard, brain+quote | Fieldstone, brain only | Scorecard wall time |
|---|---|---|---|---|
| q8_0 (default in the installer) | 8.69 GB | 40/40 | 31/40 | 360 s |
| q4_0 | 7.18 GB | 40/40 | 31/40 | 364 s |

Same accuracy and speed on this test; q4_0 saves 1.5 GB. Hermes answer times varied 14 to 48 s on the same setting (answer length), so speed is not set by the KV type here. The installer keeps q8_0 for precision on long Hermes sessions; set `OLLAMA_KV_CACHE_TYPE=q4_0` in `~/Library/LaunchAgents/ai.staffbox.ollama.plist` on memory-tight units.
