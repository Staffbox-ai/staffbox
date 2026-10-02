# Evals

Every scorecard in `results/` was produced by `staffbox eval` on the machine named in its file and graded automatically. Nothing is hand-edited. Each `.md` file is the scorecard, and the `.jsonl` file next to it holds every answer, raw, so any row can be checked.

To reproduce one:

```sh
bin/staffbox eval examples/peachtree-cabinet-works/vault examples/peachtree-cabinet-works/tests.jsonl \
  --host http://localhost:11434 --model qwen3:8b --out evals/results/$(date +%F)-<machine>-<model>
```

Modes: `none` (the model alone), `brain` (plus the notes the brain retrieves), `brain+calc` (plus a calculator), `brain+quote` (plus the quote action, which prices lines from the vault's own tables).

To add a result, open a PR with both files. Never edit an old result: add a new one.
