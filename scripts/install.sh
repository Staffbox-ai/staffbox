#!/bin/zsh
# Staffbox unit install for a Mac mini. Read before running. Idempotent where it can be.
# Usage: ./install.sh <profile-name> [model]     e.g. ./install.sh zero qwen3:8b
set -e
PROFILE=${1:-zero}; MODEL=${2:-qwen3:8b}; HERE="$(cd "$(dirname "$0")/.." && pwd)"
echo "1/5 Ollama"; if ! command -v ollama >/dev/null && [ ! -d /Applications/Ollama.app ]; then echo "Install Ollama from https://ollama.com/download and re-run."; exit 1; fi
curl -s localhost:11434/api/tags >/dev/null || { echo "Start Ollama (open the app) and re-run."; exit 1; }
echo "2/5 model $MODEL"; ollama pull "$MODEL" 2>/dev/null || curl -s localhost:11434/api/pull -d "{\"name\":\"$MODEL\"}" >/dev/null
echo "3/5 Hermes Agent"; command -v hermes >/dev/null || { echo "Install Hermes Agent first: https://hermes-agent.nousresearch.com (then re-run)."; exit 1; }
echo "4/5 profile $PROFILE"; hermes profile create "$PROFILE" --clone --description "Staffbox unit: company worker on local models" || true
P=~/.hermes/profiles/$PROFILE; [ -d "$P" ] || { echo "Profile $PROFILE was not created; run: hermes profile create $PROFILE --clone"; exit 1; }; cp "$HERE/profile/SOUL.md.example" "$P/SOUL.md"
python3 - "$P/config.yaml" "$MODEL" <<'PY'
import sys,re; p,model=sys.argv[1],sys.argv[2]; s=open(p).read()
s=re.sub(r"(?m)^(\s*provider:\s*).*$", r"\1ollama", s, count=1)  # "ollama" is accepted by Hermes 0.14 and enables its Ollama context check; use "custom" on older builds
s=re.sub(r"(?m)^(\s*base_url:\s*).*$", r"\1http://localhost:11434/v1", s, count=1)
s=re.sub(r"(?m)^(\s*default:\s*).*$", r"\1"+model, s, count=1)
if "context_length" not in s: s=re.sub(r"(?m)^(\s*default:\s*"+re.escape(model)+r"\s*)$", r"\1\n  context_length: 65536\n  ollama_num_ctx: 65536", s, count=1)
open(p,"w").write(s)
PY
echo "5/5 vault"; mkdir -p ~/staffbox/vault/sops; cp -n "$HERE/profile/vault/"*.md ~/staffbox/vault/ 2>/dev/null || true; cp -n "$HERE/profile/vault/sops/"*.md ~/staffbox/vault/sops/ 2>/dev/null || true
echo "Done. Try:  cd ~/staffbox && $PROFILE -z \"Today is $(date +%F). Read vault/company.md and tell me what you know.\""
