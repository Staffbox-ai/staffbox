# Sample inbox (fictional)

Three requests the way they arrive. Try the draft-only door:

```sh
cp -R examples/fieldstone-it/inbox-sample /tmp/requests && cp -R examples/fieldstone-it/vault /tmp/fieldstone-vault
bin/staffbox inbox /tmp/fieldstone-vault --in /tmp/requests --drafts /tmp/drafts --model qwen3:8b
```

Each request becomes a draft `.eml` in `/tmp/drafts` that cites the price list and its date. Nothing is sent.
