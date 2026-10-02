# Measurements

All numbers here are measured on real hardware and dated. Add rows; do not edit old ones.

| Date | Machine | Model | Streams | Per-stream tok/s | Wall for 220 tokens each | Notes |
|---|---|---|---|---|---|---|
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b via Ollama, default parallelism | 1 | 20.6 | 65 s | includes model load |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 2 | 20.4 | 112 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 4 | 20.5 | 127 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b at 64K context, Hermes Agent one-shot task | 1 | n/a | 5 to 10 min | read a vault file, answer, write a log line; browser also running |

Next: three 32 GB units, same tests, plus OLLAMA_NUM_PARALLEL 2 and 4.

## Accuracy (scorecard)

| Date | Machine | Model | Test set | Model alone | + brain | + brain + calc | File |
|---|---|---|---|---|---|---|---|
| 2026-09-30 | Dell Precision 5820, RTX 3090 | qwen3:8b (Mac mini class) | Peachtree, 40 | 1/40 | 32/40 | 34/40 | evals/results/2026-09-30-dell-3090-qwen3-8b.md |
| 2026-09-30 | Dell Precision 5820, RTX 3090 | qwen3.8-27b | Peachtree, 40 | 2/40 | 39/40 | 37/40 | evals/results/2026-09-30-dell-3090-qwen3.8-27b.md |

The same 8B run on the 16 GB Mac mini was stopped partway through: another job on the mini loaded a vision model, and 16 GB holds one model at a time. It needs a re-run on a quiet box.
