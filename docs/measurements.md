# Measurements

All numbers here are measured on real hardware and dated. Add rows; do not edit old ones.

| Date | Machine | Model | Streams | Per-stream tok/s | Wall for 220 tokens each | Notes |
|---|---|---|---|---|---|---|
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b via Ollama, default parallelism | 1 | 20.6 | 65 s | includes model load |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 2 | 20.4 | 112 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b | 4 | 20.5 | 127 s | requests queued |
| 2026-09-23 | Mac mini M4, 16 GB | qwen3:8b at 64K context, Hermes Agent one-shot task | 1 | n/a | 5 to 10 min | read a vault file, answer, write a log line; browser also running |

Next: three 32 GB units, same tests, plus OLLAMA_NUM_PARALLEL 2 and 4.
