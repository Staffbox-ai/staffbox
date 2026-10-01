#!/bin/zsh
# Staffbox unit install for a Mac mini. One command, no sudo, safe to re-run.
#   git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src && ~/staffbox-src/scripts/install.sh
# Options (environment):  PROFILE=zero  MODEL=qwen3:8b  EXTRA_MODELS="qwen3:14b"  SKIP_PROOF=1
# What it does, in order: checks the Mac, installs Ollama (local-only), pulls the model, installs Hermes Agent,
# creates the worker profile with cloud models OFF, sets up the brain and demo brains, then proves the unit
# with a short scorecard and writes a unit card to ~/staffbox/UNIT.md.
set -e
PROFILE=${PROFILE:-${1:-zero}}; MODEL=${MODEL:-${2:-qwen3:8b}}; EXTRA_MODELS=${EXTRA_MODELS:-}
HERE="$(cd "$(dirname "$0")/.." && pwd)"; SB=~/staffbox; LOG=$SB/install.log
OLLAMA_APP=/Applications/Ollama.app; OLLAMA=$OLLAMA_APP/Contents/Resources/ollama
OLLAMA_TEAM=3MU9H2V9Y9   # Ollama's Apple Developer ID team; the app is refused if the signature differs
mkdir -p $SB ~/.local/bin; export PATH=$HOME/.local/bin:$PATH
exec > >(tee -a $LOG) 2>&1

if [ -t 1 ]; then G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; B=$'\e[1m'; D=$'\e[2m'; N=$'\e[0m'; else G= Y= R= B= D= N=; fi
STEP=0; TOTAL=8
step(){ STEP=$((STEP+1)); print -r -- ""; print -r -- "${B}[$STEP/$TOTAL] $1${N}"; }
ok(){ print -r -- "  ${G}✓${N} $1"; }
warn(){ print -r -- "  ${Y}!${N} $1"; }
die(){ print -r -- "  ${R}✗ $1${N}"; print -r -- ""; print -r -- "  Fix that, then run the same command again. Everything already done is kept. Log: $LOG"; exit 1; }

print -r -- ""
print -r -- "${B}  Staffbox${N}  ${D}on-site AI worker · unit install · $(date '+%d %b %Y %H:%M')${N}"
print -r -- "${D}  Your data stays on this Mac. Cloud AI stays off unless you turn it on with your own key.${N}"

step "Checking this Mac"
[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] || die "This needs a Mac with Apple silicon."
RAM_GB=$(( $(sysctl -n hw.memsize) / 1073741824 )); FREE_GB=$(df -g / | awk 'NR==2{print $4}')
ok "macOS $(sw_vers -productVersion), $(sysctl -n machdep.cpu.brand_string), ${RAM_GB} GB memory, ${FREE_GB} GB free"
[ $RAM_GB -ge 32 ] || warn "${RAM_GB} GB runs the 8B model well; 32 GB is recommended for customer sites."
[ $FREE_GB -ge 40 ] || die "Needs at least 40 GB free disk for the models."
defaults read MobileMeAccounts Accounts 2>/dev/null | grep -q AccountID && warn "An Apple ID is signed in. A customer unit should have none." || ok "No personal Apple ID on this Mac"

step "Developer tools (for git)"
if xcode-select -p >/dev/null 2>&1; then ok "Command Line Tools present"
else xcode-select --install >/dev/null 2>&1 || true; die "Command Line Tools are not installed yet. Click Install in the dialog on this Mac's screen (about 10 minutes)."; fi

step "Ollama, the local model server"
if [ ! -x $OLLAMA ]; then
  print -r -- "  Downloading Ollama from its official release…"
  curl -fsSL -o /tmp/Ollama-darwin.zip https://github.com/ollama/ollama/releases/latest/download/Ollama-darwin.zip || die "Download failed; check the internet connection."
  ditto -x -k /tmp/Ollama-darwin.zip /Applications/ || die "Could not write to /Applications; run as an admin user."
fi
codesign -dv $OLLAMA_APP 2>&1 | grep -q "TeamIdentifier=$OLLAMA_TEAM" || die "Ollama's signature does not match its publisher. Not running it."
PL=~/Library/LaunchAgents/ai.staffbox.ollama.plist; mkdir -p ~/Library/LaunchAgents ~/Library/Logs
cat > $PL <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>ai.staffbox.ollama</string>
<key>ProgramArguments</key><array><string>$OLLAMA</string><string>serve</string></array>
<key>EnvironmentVariables</key><dict><key>OLLAMA_HOST</key><string>127.0.0.1:11434</string><key>OLLAMA_KEEP_ALIVE</key><string>30m</string></dict>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardOutPath</key><string>$HOME/Library/Logs/ollama.log</string><key>StandardErrorPath</key><string>$HOME/Library/Logs/ollama.log</string>
</dict></plist>
EOF
curl -s localhost:11434/api/version >/dev/null 2>&1 || launchctl bootstrap gui/$(id -u) $PL 2>/dev/null || launchctl bootstrap user/$(id -u) $PL 2>/dev/null || true
for i in {1..30}; do curl -s localhost:11434/api/version >/dev/null 2>&1 && break; sleep 1; done
curl -s localhost:11434/api/version >/dev/null 2>&1 || die "Ollama did not start. See ~/Library/Logs/ollama.log"
ok "Ollama $($OLLAMA --version 2>/dev/null | awk '{print $NF}') running on this Mac only (127.0.0.1), starts at login"

step "Model"
for M in $MODEL ${=EXTRA_MODELS}; do
  if $OLLAMA list 2>/dev/null | awk '{print $1}' | grep -qx "$M"; then ok "$M already here"
  else print -r -- "  Pulling $M (a few minutes)…"; $OLLAMA pull "$M" >/dev/null 2>&1 || die "Could not pull $M."; ok "$M ready"; fi
done

step "Hermes Agent, the worker"
if ! command -v hermes >/dev/null 2>&1; then
  print -r -- "  Installing Hermes Agent from Nous Research's official installer…"
  curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh -o /tmp/hermes-install.sh || die "Could not download the Hermes installer."
  bash /tmp/hermes-install.sh >> $LOG 2>&1 || die "Hermes install failed. See $LOG"
  export PATH=$HOME/.local/bin:$PATH; hash -r
fi
command -v hermes >/dev/null 2>&1 || die "Hermes is installed but not on PATH. Open a new terminal and run this again."
ok "$(hermes --version 2>/dev/null | head -1)"

step "Worker profile \"$PROFILE\" (cloud models off)"
hermes profile create "$PROFILE" --clone --description "Staffbox unit: company worker on local models" >/dev/null 2>&1 || true
P=~/.hermes/profiles/$PROFILE; [ -d "$P" ] || die "Profile $PROFILE was not created; run: hermes profile create $PROFILE --clone"
[ -s "$P/SOUL.md" ] && grep -q Staffbox "$P/SOUL.md" || cp "$HERE/profile/SOUL.md.example" "$P/SOUL.md"
python3 - "$P/config.yaml" "$MODEL" <<'PY'
import sys, re, os
p, model = sys.argv[1], sys.argv[2]
s = open(p).read() if os.path.exists(p) else "model:\n  default: x\n  provider: ollama\n  base_url: http://localhost:11434/v1\n"
def setkey(s, key, val):
    """Set an active (uncommented) `  key: val` in the model: block; add it after `default:` if absent."""
    if re.search(rf"(?m)^  {key}:", s):
        return re.sub(rf"(?m)^(  {key}:[ \t]*)[^#\n]*", lambda m: m.group(1) + val + " ", s, count=1)
    return re.sub(r"(?m)^(  default:.*)$", lambda m: m.group(1) + f"\n  {key}: {val}", s, count=1)
s = setkey(s, "default", model)
s = setkey(s, "provider", "ollama")        # "ollama" is accepted by Hermes 0.14+
s = setkey(s, "base_url", "http://localhost:11434/v1")
s = setkey(s, "context_length", "65536")
s = setkey(s, "ollama_num_ctx", "65536")   # without it Ollama falls back to a 2048-token window
if re.search(r"(?m)^fallback_providers:", s):  # no silent cloud fallback
    s = re.sub(r"(?ms)^fallback_providers:.*?(?=^\S|\Z)", "fallback_providers: []\n", s, count=1)
else:
    s += "\nfallback_providers: []\n"
open(p, "w").write(s)
PY
KEYS=$(cat ~/.hermes/.env "$P/.env" 2>/dev/null | grep -v '^[[:space:]]*#' | grep -c -E '(KEY|TOKEN|SECRET)[A-Z0-9_]*=.+' || true)
if grep -q "^fallback_providers: \[\]" "$P/config.yaml" && [ "${KEYS:-0}" -eq 0 ]; then CLOUD="off (no fallback providers, no API keys)"; ok "Model $MODEL on this Mac; cloud AI: off (no fallbacks, no API keys)"
else CLOUD="CHECK: fallbacks or API keys present"; warn "Cloud fallbacks or API keys found: check $P/config.yaml and .env"; fi
[ -e ~/.local/bin/$PROFILE ] || { printf '#!/bin/sh\nexec hermes -p %s "$@"\n' "$PROFILE" > ~/.local/bin/$PROFILE; chmod +x ~/.local/bin/$PROFILE; }
ok "Shortcut: $PROFILE -z \"your question\""

step "Brain"
mkdir -p $SB/vault; [ -e $SB/vault/company.md ] || cp -R "$HERE/profile/vault/." $SB/vault/
mkdir -p "$P/skills/staffbox-brain"; cp "$HERE/profile/skills/staffbox-brain/SKILL.md" "$P/skills/staffbox-brain/SKILL.md"
mkdir -p $SB/examples; cp -Rn "$HERE/examples/." $SB/examples/ 2>/dev/null || true
ln -sf "$HERE/bin/staffbox" ~/.local/bin/staffbox
staffbox check $SB/vault >/dev/null 2>&1 && ok "Company brain at $SB/vault (open it in Obsidian)" || warn "Brain check found problems: staffbox check $SB/vault"
ok "Demo brains: $(ls $SB/examples | tr '\n' ' ')"

step "Proof: a short scorecard on this unit"
CARD=""
if [ -z "$SKIP_PROOF" ]; then
  OUT=$(cd / && staffbox eval $SB/examples/fieldstone-it/vault $SB/examples/fieldstone-it/tests.jsonl --model $MODEL --modes brain+quote \
        --limit 10 --num-ctx 12288 --machine "$(scutil --get ComputerName 2>/dev/null)" --out $SB/install-proof 2>/dev/null | grep -m1 '\*\*all\*\*' || true)
  CARD=$(print -r -- "$OUT" | sed -E 's/.*\| ([0-9]+\/[0-9]+ \([0-9]+%\)).*/\1/')
  [ -n "$CARD" ] && ok "Fieldstone IT demo, first 10 questions: $CARD (full results: $SB/install-proof.md)" || warn "Scorecard did not finish; run it later with staffbox eval"
else warn "Skipped (SKIP_PROOF=1)"; fi

SERIAL=$(system_profiler SPHardwareDataType 2>/dev/null | awk -F': ' '/Serial Number/{print $2; exit}')
COMMIT=$(git -C "$HERE" rev-parse --short HEAD 2>/dev/null || cat "$HERE/.version" 2>/dev/null || echo "download")
cat > $SB/UNIT.md <<EOF
# Staffbox unit card

| | |
|---|---|
| Unit | $(scutil --get ComputerName 2>/dev/null) · serial $SERIAL |
| Installed | $(date '+%Y-%m-%d %H:%M') by $(whoami) |
| Mac | macOS $(sw_vers -productVersion), ${RAM_GB} GB memory |
| Worker | Hermes profile "$PROFILE" · $(hermes --version 2>/dev/null | head -1) |
| Model | $MODEL ${EXTRA_MODELS} via Ollama $($OLLAMA --version 2>/dev/null | awk '{print $NF}'), listening on 127.0.0.1 only |
| Cloud AI | $CLOUD |
| Brain | $SB/vault · demo brains in $SB/examples |
| Staffbox | $COMMIT |
| Install proof | ${CARD:-not run} |

Try it: \`staffbox ask $SB/examples/fieldstone-it/vault "Client wants 12 MON-27 monitors set up. How much for the line?"\`
Support: hadi@staffbox.ai · staffbox.ai
EOF
print -r -- ""
print -r -- "${G}${B}  Staffbox unit ready.${N}  Unit card: $SB/UNIT.md"
print -r -- "${D}  Try:  staffbox ask $SB/examples/fieldstone-it/vault \"A user is locked out of MFA. What do we do first?\"${N}"
print -r -- ""
