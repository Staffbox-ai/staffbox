#!/bin/zsh
# Staffbox unit install for a Mac mini. One command, no sudo, safe to re-run.
#   git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src && ~/staffbox-src/scripts/install.sh
# Options (environment):  PROFILE=zero  MODEL=qwen3:8b  EXTRA_MODELS="qwen3:14b"  SKIP_PROOF=1  DEMO_UNIT=1 (allow FileVault off on a demo box)
# What it does, in order: checks the Mac, installs Ollama (local-only), pulls the model, installs Hermes Agent,
# creates the worker profile with cloud models OFF, sets up the brain and demo brains, then proves the unit
# with a short scorecard and writes a unit card to ~/staffbox/UNIT.md. It also brands the desktop and starts
# the Hermes dashboard (127.0.0.1:9119) and a welcome page at login.
#
# Opt-in, needs an admin password (the IT provider runs it once, after the install, as the same user):
#   ~/staffbox-src/scripts/install.sh --harden-macos
# turns on the macOS firewall + stealth mode, sets SSH to keys only, locks the worker's Hermes config
# (chflags schg) and records the result in ~/staffbox/UNIT.md. It changes nothing else.
set -e
HARDEN=${HARDEN_MACOS:-}; if [ "$1" = "--harden-macos" ]; then HARDEN=1; shift; fi
PROFILE=${PROFILE:-${1:-zero}}; MODEL=${MODEL:-${2:-qwen3:8b}}; EXTRA_MODELS=${EXTRA_MODELS:-}
HERE="$(cd "$(dirname "$0")/.." && pwd)"; SB=~/staffbox; LOG=$SB/install.log
OLLAMA_APP=/Applications/Ollama.app; OLLAMA=$OLLAMA_APP/Contents/Resources/ollama
OLLAMA_TEAM=3MU9H2V9Y9   # Ollama's Apple Developer ID team; the app is refused if the signature differs
P=~/.hermes/profiles/$PROFILE
# The only directories the worker's file tools may write to (Hermes HERMES_WRITE_SAFE_ROOT, ':'-separated).
SAFE_ROOT="$SB/vault:$SB/work"
# Tool groups that must be OFF after install. The installer stops if any of them is still on.
LOCKED_TOOLS=(terminal code_execution browser computer_use web connections delegation cronjob tts image_gen)
mkdir -p $SB ~/.local/bin; export PATH=$HOME/.local/bin:$PATH
exec > >(tee -a $LOG) 2>&1
# Downloads go to a private, unpredictable temp dir (not fixed /tmp names) and are removed on exit.
TMPD=$(mktemp -d "${TMPDIR:-/tmp}/staffbox.XXXXXXXX"); trap 'rm -rf "$TMPD"' EXIT

if [ -t 1 ]; then G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; B=$'\e[1m'; D=$'\e[2m'; N=$'\e[0m'; else G= Y= R= B= D= N=; fi
STEP=0; TOTAL=9
step(){ STEP=$((STEP+1)); print -r -- ""; print -r -- "${B}[$STEP/$TOTAL] $1${N}"; }
ok(){ print -r -- "  ${G}✓${N} $1"; }
warn(){ print -r -- "  ${Y}!${N} $1"; }
die(){ print -r -- "  ${R}✗ $1${N}"; print -r -- ""; print -r -- "  Fix that, then run the same command again. Everything already done is kept. Log: $LOG"; exit 1; }
release_asset(){ # GitHub releases API URL, asset name (or ".ext") -> "download_url sha256" (sha256 empty if not published)
  curl -fsSL "$1" | python3 -c 'import json,sys
d=json.load(sys.stdin); want=sys.argv[1]
for r in (d if isinstance(d, list) else [d]):
    for a in r.get("assets", []):
        if a["name"] == want or (want.startswith(".") and a["name"].endswith(want)):
            print(a["browser_download_url"], (a.get("digest") or "").replace("sha256:", "")); sys.exit()' "$2" 2>/dev/null; }
check_sha(){ # file, expected sha256 (may be empty), label
  local got; got=$(shasum -a 256 "$1" | awk '{print $1}')
  if [ -n "$2" ]; then [ "$got" = "$2" ] || die "$3: sha256 $got does not match the published $2. Not using it."; ok "$3 sha256 $got (matches the publisher's)"
  else warn "$3 sha256 $got (the publisher gives no checksum to compare; recorded in the log)"; fi; }
ollama_pids(){ lsof -nP -iTCP:11434 -sTCP:LISTEN -t 2>/dev/null | sort -u | tr '\n' ' '; }
agent_pid(){ launchctl print gui/$(id -u)/ai.staffbox.$1 2>/dev/null | awk '/^[[:space:]]*pid = /{print $3; exit}'; }

if [ -n "$HARDEN" ]; then
  # ---- Opt-in macOS hardening (needs sudo). Not part of the default no-sudo install. ----
  STEP=0; TOTAL=4
  print -r -- ""; print -r -- "${B}  Staffbox${N}  ${D}opt-in macOS hardening · $(date '+%d %b %Y %H:%M') · asks for an admin password${N}"
  [ "$(id -u)" -ne 0 ] || die "Run this as the unit's user (not with sudo); it asks for sudo itself."
  [ -f $SB/UNIT.md ] || die "Run the normal install first; this step adds to ~/staffbox/UNIT.md."
  sudo -v || die "This step needs an admin password."
  FWB=/usr/libexec/ApplicationFirewall/socketfilterfw
  step "Application firewall + stealth mode"
  sudo $FWB --setglobalstate on >/dev/null; sudo $FWB --setstealthmode on >/dev/null
  FW=$($FWB --getglobalstate 2>&1 | head -1); ST=$($FWB --getstealthmode 2>&1 | head -1)
  print -r -- "$FW" | grep -qi "enabled" || die "Firewall did not turn on: $FW"
  print -r -- "$ST" | grep -qiE "is on|enabled" || die "Stealth mode did not turn on: $ST"
  ok "$FW · $ST"
  step "SSH: keys only"
  SSHD_DROP=/etc/ssh/sshd_config.d/000-staffbox-keys-only.conf   # 000- so it sorts before macOS's 100-macos.conf (sshd uses the first value it reads)
  if ! grep -q '^Include /etc/ssh/sshd_config.d/\*' /etc/ssh/sshd_config 2>/dev/null; then
    die "/etc/ssh/sshd_config does not include sshd_config.d on this macOS; set key-only SSH by hand (see docs/install.md)."
  fi
  if nc -z -G 2 127.0.0.1 22 >/dev/null 2>&1 && [ ! -s ~/.ssh/authorized_keys ]; then   # port 22 open = Remote Login on
    die "Remote Login is on but ~/.ssh/authorized_keys is empty: key-only SSH would lock everyone out. Add a key first (docs/connect.md)."
  fi
  printf '# Staffbox: key-only SSH (scripts/install.sh --harden-macos)\nPasswordAuthentication no\nKbdInteractiveAuthentication no\n' | sudo tee $SSHD_DROP >/dev/null
  sudo sshd -t || { sudo rm -f $SSHD_DROP; die "sshd rejected the config; removed $SSHD_DROP."; }
  SSHD_EFF=$(sudo sshd -T 2>/dev/null | grep -iE '^(passwordauthentication|kbdinteractiveauthentication) ' | tr '\n' ' ')
  print -r -- "$SSHD_EFF" | grep -qi "passwordauthentication no" && print -r -- "$SSHD_EFF" | grep -qi "kbdinteractiveauthentication no" \
    || die "sshd still allows passwords (effective: ${SSHD_EFF:-unknown})."
  ok "Effective: $SSHD_EFF(new SSH sessions; test your key in a second window before closing this one)"
  step "Lock the worker's Hermes config (system-immutable)"
  [ -f "$P/config.yaml" ] || die "No profile config at $P/config.yaml."
  [ -e "$P/.env" ] || : > "$P/.env"
  sudo chflags schg "$P/config.yaml" "$P/.env" || die "Could not lock $P/config.yaml and .env"
  ls -lO "$P/config.yaml" "$P/.env" | grep -q schg || die "Lock did not take on $P"
  ok "$P/config.yaml and .env are now immutable: no edit, replace or delete without an admin (sudo chflags noschg …)"
  step "Record in the unit card"
  cat >> $SB/UNIT.md <<EOF

## macOS hardening ($(date '+%Y-%m-%d %H:%M') by $(whoami), --harden-macos)

| | |
|---|---|
| Firewall | $FW · $ST |
| SSH | $SSHD_DROP · effective: $SSHD_EFF |
| Worker config lock | chflags schg on $P/config.yaml and .env (unlock: \`sudo chflags noschg …\`) |
EOF
  ok "Added to $SB/UNIT.md"
  print -r -- ""; print -r -- "${G}${B}  Hardening done.${N}"; exit 0
fi

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
FV=$(fdesetup status 2>/dev/null | head -1)
case "$FV" in
  *"is On"*) ok "Disk encryption: $FV" ;;
  *) if [ -n "$DEMO_UNIT" ]; then warn "Disk encryption is OFF (DEMO_UNIT=1: allowed for a demo box with no customer data)."
     else die "Disk encryption is OFF. A customer unit needs it: run 'sudo fdesetup enable', keep the recovery key with the customer's IT provider, then run this again. (Demo box with no customer data: DEMO_UNIT=1)"; fi ;;
esac

step "Developer tools (for git)"
if xcode-select -p >/dev/null 2>&1; then ok "Command Line Tools present"
else xcode-select --install >/dev/null 2>&1 || true; die "Command Line Tools are not installed yet. Click Install in the dialog on this Mac's screen (about 10 minutes)."; fi

step "Ollama, the local model server"
if [ ! -x $OLLAMA ]; then
  print -r -- "  Downloading Ollama from its official release…"
  read -r OURL OSHA <<< "$(release_asset https://api.github.com/repos/ollama/ollama/releases/latest Ollama-darwin.zip)"
  [ -n "$OURL" ] || die "Could not find Ollama's latest release; check the internet connection."
  curl -fsSL -o "$TMPD/Ollama-darwin.zip" "$OURL" || die "Download failed; check the internet connection."
  check_sha "$TMPD/Ollama-darwin.zip" "$OSHA" "Ollama ($OURL)"
  ditto -x -k "$TMPD/Ollama-darwin.zip" /Applications/ || die "Could not write to /Applications; run as an admin user."
fi
# Port 11434 belongs to the ai.staffbox.ollama LaunchAgent (with the 64K settings). A second Ollama
# (the menu-bar app, or one started by hand) would take the port with its own defaults.
osascript -e 'quit app "Ollama"' >/dev/null 2>&1 || true
codesign -dv $OLLAMA_APP 2>&1 | grep -q "TeamIdentifier=$OLLAMA_TEAM" || die "Ollama's signature does not match its publisher. Not running it."
PL=~/Library/LaunchAgents/ai.staffbox.ollama.plist; mkdir -p ~/Library/LaunchAgents ~/Library/Logs
cat > $PL <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>ai.staffbox.ollama</string>
<key>ProgramArguments</key><array><string>$OLLAMA</string><string>serve</string></array>
<key>EnvironmentVariables</key><dict><key>OLLAMA_HOST</key><string>127.0.0.1:11434</string><key>OLLAMA_KEEP_ALIVE</key><string>24h</string><key>OLLAMA_CONTEXT_LENGTH</key><string>65536</string><key>OLLAMA_MAX_LOADED_MODELS</key><string>1</string><key>OLLAMA_FLASH_ATTENTION</key><string>1</string><key>OLLAMA_KV_CACHE_TYPE</key><string>q8_0</string></dict>
<key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
<key>StandardOutPath</key><string>$HOME/Library/Logs/ollama.log</string><key>StandardErrorPath</key><string>$HOME/Library/Logs/ollama.log</string>
</dict></plist>
EOF
launchctl bootout gui/$(id -u)/ai.staffbox.ollama >/dev/null 2>&1 || true; sleep 1
launchctl bootstrap gui/$(id -u) $PL 2>/dev/null || launchctl bootstrap user/$(id -u) $PL 2>/dev/null || true
for i in {1..30}; do curl -s localhost:11434/api/version >/dev/null 2>&1 && break; sleep 1; done
curl -s localhost:11434/api/version >/dev/null 2>&1 || die "Ollama did not start. See ~/Library/Logs/ollama.log"
OPID=$(agent_pid ollama); LPIDS=$(ollama_pids)
if [ -n "$OPID" ] && [ "${LPIDS% }" = "$OPID" ]; then ok "Port 11434 is served by the Staffbox LaunchAgent (pid $OPID)"
else warn "Port 11434 is served by pid(s) ${LPIDS:-none}, not the Staffbox LaunchAgent (pid ${OPID:-not running}). Quit the Ollama menu-bar app, remove it from Login Items, and run this again."; fi
ok "Ollama $($OLLAMA --version 2>/dev/null | awk '{print $NF}') running on this Mac only (127.0.0.1), starts at login; model kept warm 24 h, one model, one context size"

step "Model"
for M in $MODEL ${=EXTRA_MODELS}; do
  if $OLLAMA list 2>/dev/null | awk '{print $1}' | grep -qx "$M"; then ok "$M already here"
  else print -r -- "  Pulling $M (a few minutes)…"; $OLLAMA pull "$M" >/dev/null 2>&1 || die "Could not pull $M."; ok "$M ready"; fi
done
# Load the model the way the worker will (no num_ctx in the request) and read the context Ollama really gave it.
curl -s localhost:11434/api/generate -d "{\"model\":\"$MODEL\",\"prompt\":\"\",\"keep_alive\":\"24h\"}" >/dev/null 2>&1 || true
CTX=$(curl -s localhost:11434/api/ps | python3 -c 'import json,sys
m=[x for x in json.load(sys.stdin).get("models",[]) if x.get("name")==sys.argv[1] or x.get("model")==sys.argv[1]]
print(m[0].get("context_length","") if m else "")' "$MODEL" 2>/dev/null || true)
if [ "$CTX" = 65536 ]; then ok "Effective context for $MODEL: 65536 tokens"
else warn "Effective context for $MODEL is ${CTX:-unknown}, expected 65536 (Hermes needs 64K). Check that only the Staffbox LaunchAgent serves port 11434, or that the model supports 64K."; fi

step "Hermes Agent, the worker"
# Pinned to a reviewed release (v0.21.7, 12 Oct 2026; includes the v0.21.6 dashboard sign-in fixes).
# To move the pin: change HERMES_COMMIT to a SHA that is on NousResearch/hermes-agent main.
HERMES_COMMIT=71d34bad1045610252eda02ee79549436896e784
# sha256 of scripts/install.sh AT that commit (immutable). Moving the pin means updating this too:
#   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/<SHA>/scripts/install.sh | shasum -a 256
HERMES_INSTALLER_SHA256=034845e34289813ff5fb7fd3e071ec69f6b14aee8ba297a477b31dda6374cb86
if ! command -v hermes >/dev/null 2>&1; then
  print -r -- "  Installing Hermes Agent v0.21.7 from Nous Research's official installer (taken from the pinned commit)…"
  curl -fsSL "https://raw.githubusercontent.com/NousResearch/hermes-agent/$HERMES_COMMIT/scripts/install.sh" -o "$TMPD/hermes-install.sh" || die "Could not download the Hermes installer."
  check_sha "$TMPD/hermes-install.sh" "$HERMES_INSTALLER_SHA256" "Hermes installer @ ${HERMES_COMMIT:0:7}"
  bash "$TMPD/hermes-install.sh" --commit $HERMES_COMMIT >> $LOG 2>&1 || die "Hermes install failed. See $LOG"
  export PATH=$HOME/.local/bin:$PATH; hash -r
else
  print -r -- "  Hermes is already installed: $(hermes --version 2>/dev/null | head -1). Not changing it (see docs/install.md, Updating)."
fi
command -v hermes >/dev/null 2>&1 || die "Hermes is installed but not on PATH. Open a new terminal and run this again."
ok "$(hermes --version 2>/dev/null | head -1)"
HV=$(hermes --version 2>/dev/null | sed -nE '1s/.*v([0-9]+\.[0-9]+\.[0-9]+).*/\1/p'); autoload -Uz is-at-least
is-at-least 0.21.6 "${HV:-0}" || warn "Hermes ${HV:-unknown} is older than 0.21.6 (dashboard sign-in fixes). See docs/install.md, Updating."
HDIR=$(hermes --version 2>/dev/null | sed -nE 's/^Install directory: (.*)$/\1/p'); HDIR=${HDIR:-$HOME/.hermes/hermes-agent}
HREV=$(git -C "$HDIR" rev-parse HEAD 2>/dev/null || echo unknown)
[ "$HREV" = "$HERMES_COMMIT" ] && ok "Hermes code at the pinned commit ${HREV:0:7}" || warn "Hermes code is at ${HREV:0:12}, not the pinned ${HERMES_COMMIT:0:7} (recorded in the unit card)"

step "Worker profile \"$PROFILE\" (cloud models off)"
hermes profile create "$PROFILE" --clone --description "Staffbox unit: company worker on local models" >/dev/null 2>&1 || true
[ -d "$P" ] || die "Profile $PROFILE was not created; run: hermes profile create $PROFILE --clone"
ls -lO "$P/config.yaml" "$P/.env" 2>/dev/null | grep -q schg && die "The worker config is locked by --harden-macos. Unlock: sudo chflags noschg $P/config.yaml $P/.env, run this again, then re-run --harden-macos."
chmod u+w "$P/config.yaml" "$P/.env" 2>/dev/null || true   # read-only from a previous run; locked again at the end of step 8
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
# Write containment: Hermes' file tools (write_file, patch) refuse any path outside SAFE_ROOT. Set in the
# profile .env (read when Hermes runs this profile, including over SSH from the desktop app), in the shortcut,
# and in the dashboard's LaunchAgent. Hermes also always refuses ~/.ssh, ~/.aws, .env files and its own secrets.
mkdir -p $SB/work
touch "$P/.env"; grep -v '^HERMES_WRITE_SAFE_ROOT=' "$P/.env" > "$TMPD/env" || true
print -r -- "HERMES_WRITE_SAFE_ROOT=$SAFE_ROOT" >> "$TMPD/env"; cat "$TMPD/env" > "$P/.env"
SC=~/.local/bin/$PROFILE
if [ ! -e $SC ] || grep -q "exec hermes -p" $SC; then
  printf '#!/bin/sh\nexport HERMES_WRITE_SAFE_ROOT="%s"\nexec hermes -p %s "$@"\n' "$SAFE_ROOT" "$PROFILE" > $SC; chmod +x $SC
fi
ok "Worker file writes limited to: ${SAFE_ROOT//:/, }"
ok "Shortcut: $PROFILE -z \"your question\""

step "Brain"
mkdir -p $SB/vault; [ -e $SB/vault/company.md ] || cp -R "$HERE/profile/vault/." $SB/vault/
mkdir -p "$P/skills/staffbox-brain"; cp "$HERE/profile/skills/staffbox-brain/SKILL.md" "$P/skills/staffbox-brain/SKILL.md"
mkdir -p $SB/examples; cp -Rn "$HERE/examples/." $SB/examples/ 2>/dev/null || true
ln -sf "$HERE/bin/staffbox" ~/.local/bin/staffbox
staffbox check $SB/vault >/dev/null 2>&1 && ok "Company brain at $SB/vault (open it in Obsidian)" || warn "Brain check found problems: staffbox check $SB/vault"
ok "Demo brains: $(ls $SB/examples | tr '\n' ' ')"

step "Desktop, dashboard and welcome page"
hermes -p "$PROFILE" config set dashboard.show_token_analytics true >/dev/null 2>&1 || true
# Safe default: no shell, code execution, browser, computer control, web, outside connections, delegation or scheduled jobs.
# Customer-facing replies go through `staffbox inbox` (drafts only, no sending code). A site turns tools on in writing:
#   hermes -p <profile> tools enable terminal   (and so on)
# image_gen is a cloud image service. Each group is disabled on its own (one unknown name must not stop the
# rest), then the result is checked: the install stops if any locked group is still on or cannot be found.
for T in $LOCKED_TOOLS; do hermes -p "$PROFILE" tools disable "$T" >/dev/null 2>&1 || true; done
TL=$(hermes -p "$PROFILE" tools list 2>&1) || die "Could not read the worker's tools (hermes -p $PROFILE tools list): $TL"
TOOLS_ON=$(print -r -- "$TL" | awk '$2=="enabled"{print $3}' | tr '\n' ' ')
TOOLS_OFF=$(print -r -- "$TL" | awk '$2=="disabled"{print $3}' | tr '\n' ' ')
BAD=""; MISSING=""
for T in $LOCKED_TOOLS; do
  if [[ " $TOOLS_ON " == *" $T "* ]]; then BAD="$BAD $T"
  elif [[ " $TOOLS_OFF " != *" $T "* ]]; then MISSING="$MISSING $T"; fi
done
[ -z "$BAD" ] || die "Tool lock-down failed: still ON after disabling:$BAD. Check: hermes -p $PROFILE tools list"
[ -z "$MISSING" ] || die "Tool lock-down not verified: Hermes does not list$MISSING, so they cannot be confirmed off. Check: hermes -p $PROFILE tools list"
MCP=$(print -r -- "$TL" | awk '/^MCP servers:/{f=1;next} f&&NF&&$1!~/^\(/{print $1}' | tr '\n' ' ')
[ -z "${MCP// }" ] || warn "MCP servers configured for this worker: $MCP(remove any the site has not approved in writing)"
ok "Tools verified off: ${LOCKED_TOOLS[*]}"
ok "Tools on: ${TOOLS_ON:-none}"
# Make the worker's config read-only. Limits (see SECURITY.md): Hermes saves config by replacing the file, and any
# process running as this user can chmod it back. The real locks are --harden-macos (chflags schg) and a separate
# standard macOS user for the worker.
chmod a-w "$P/config.yaml" "$P/.env" 2>/dev/null && ok "Worker config.yaml and .env set read-only (re-running the installer unlocks and relocks them)"
cp "$HERE/profile/brand/wallpaper.png" $SB/wallpaper.png
sed "s#__WALLPAPER__#$SB/wallpaper.png#" "$HERE/profile/brand/set-wallpaper.js" > $SB/set-wallpaper.js
cp "$HERE/profile/brand/welcome.html" $SB/welcome.html
sed -i '' "s#profile=zero#profile=$PROFILE#g; s#profile <code>zero</code>#profile <code>$PROFILE</code>#; s#qwen3:8b on this Mac#$MODEL on this Mac#" $SB/welcome.html
FS_ENC=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$SB/examples/fieldstone-it/vault")
sed -i '' "s#__FIELDSTONE__#$FS_ENC#" $SB/welcome.html
if [ ! -d /Applications/Obsidian.app ] && [ -z "$SKIP_OBSIDIAN" ]; then   # Obsidian: the brain as a notebook people can browse
  read -r DMG DSHA <<< "$(release_asset "https://api.github.com/repos/obsidianmd/obsidian-releases/releases?per_page=10" .dmg)"
  if [ -n "$DMG" ] && curl -fsSL -o "$TMPD/obsidian.dmg" "$DMG" && check_sha "$TMPD/obsidian.dmg" "$DSHA" "Obsidian ($DMG)" \
     && hdiutil attach -nobrowse -quiet "$TMPD/obsidian.dmg" -mountpoint "$TMPD/obsmnt"; then
    ditto "$TMPD/obsmnt/Obsidian.app" /Applications/Obsidian.app; hdiutil detach -quiet "$TMPD/obsmnt"
    codesign -dv /Applications/Obsidian.app 2>&1 | grep -q "TeamIdentifier=6JSW4SJWN9" || { rm -rf /Applications/Obsidian.app; warn "Obsidian signature did not match its publisher; removed"; }
  else warn "Obsidian download failed; install it later from obsidian.md"; fi
fi
if [ -d /Applications/Obsidian.app ]; then
  mkdir -p "$HOME/Library/Application Support/obsidian"
  python3 - "$SB" <<'PY'
import json, os, sys, time
sb = sys.argv[1]; p = os.path.expanduser("~/Library/Application Support/obsidian/obsidian.json")
cfg = json.load(open(p)) if os.path.exists(p) else {"vaults": {}}
known = {v["path"] for v in cfg.get("vaults", {}).values()}
now = int(time.time() * 1000)
for i, (key, path) in enumerate([("sbfieldstone", sb + "/examples/fieldstone-it/vault"), ("sbcompany", sb + "/vault"), ("sbpeachtree", sb + "/examples/peachtree-cabinet-works/vault")]):
    if path not in known:
        cfg.setdefault("vaults", {})[key] = {"path": path, "ts": now - i * 1000}
json.dump(cfg, open(p, "w"))
PY
  ok "Obsidian with the company brain and both demo brains"
fi
agent(){ # label, then program arguments
  local L=$1; shift; local A=""; for x in "$@"; do A="$A<string>$x</string>"; done
  cat > ~/Library/LaunchAgents/ai.staffbox.$L.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>Label</key><string>ai.staffbox.$L</string><key>ProgramArguments</key><array>$A</array>
<key>EnvironmentVariables</key><dict><key>PATH</key><string>$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string><key>HERMES_WRITE_SAFE_ROOT</key><string>$SAFE_ROOT</string></dict>
<key>RunAtLoad</key><true/>$EXTRA<key>StandardOutPath</key><string>$HOME/Library/Logs/staffbox-$L.log</string><key>StandardErrorPath</key><string>$HOME/Library/Logs/staffbox-$L.log</string></dict></plist>
EOF
  launchctl bootout gui/$(id -u)/ai.staffbox.$L >/dev/null 2>&1 || true
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/ai.staffbox.$L.plist >/dev/null 2>&1 || launchctl bootstrap user/$(id -u) ~/Library/LaunchAgents/ai.staffbox.$L.plist >/dev/null 2>&1 || true; }
EXTRA="<key>KeepAlive</key><dict><key>SuccessfulExit</key><false/></dict>"; agent dashboard $HOME/.local/bin/hermes dashboard --no-open --skip-build --host 127.0.0.1 --port 9119
EXTRA=""; agent wallpaper /usr/bin/osascript -l JavaScript $SB/set-wallpaper.js
FS_URL="obsidian://open?path=$FS_ENC"
cat > $SB/login.sh <<EOF
#!/bin/sh
# Staffbox login: check who serves the model port, warm the model, open the brain in Obsidian, then the welcome page.
# Ollama is served only by the ai.staffbox.ollama LaunchAgent (64K context). The Ollama menu-bar app is NOT opened:
# it starts its own server and can take port 11434 with default settings.
sleep 15
OPID=\$(launchctl print gui/\$(id -u)/ai.staffbox.ollama 2>/dev/null | awk '/^[[:space:]]*pid = /{print \$3; exit}')
LPID=\$(lsof -nP -iTCP:11434 -sTCP:LISTEN -t 2>/dev/null | head -1)
[ -n "\$OPID" ] && [ "\$LPID" = "\$OPID" ] || echo "\$(date '+%F %T') WARNING: port 11434 served by pid \${LPID:-none}, not ai.staffbox.ollama (pid \${OPID:-none}). Quit the Ollama app." >&2
curl -s localhost:11434/api/generate -d '{"model":"$MODEL","prompt":"","keep_alive":"24h"}' >/dev/null 2>&1
CTX=\$(curl -s localhost:11434/api/ps | python3 -c 'import json,sys;m=json.load(sys.stdin).get("models",[]);print(m[0].get("context_length","") if m else "")' 2>/dev/null)
[ "\$CTX" = 65536 ] || echo "\$(date '+%F %T') WARNING: model context is \${CTX:-unknown}, expected 65536." >&2
[ -d /Applications/Obsidian.app ] && /usr/bin/open -a Obsidian "$FS_URL"
sleep 4
/usr/bin/open $SB/welcome.html
EOF
chmod +x $SB/login.sh
EXTRA=""; agent welcome /bin/sh $SB/login.sh
for i in {1..30}; do curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/ 2>/dev/null | grep -q 200 && break; sleep 2; done
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119/ 2>/dev/null | grep -q 200 && ok "Hermes dashboard at http://127.0.0.1:9119 (this Mac only): chat, agents, models and tokens, keys, Kanban" || warn "Dashboard not answering yet; see ~/Library/Logs/staffbox-dashboard.log"
ok "At every login: model port checked, model warmed (warnings in ~/Library/Logs/staffbox-welcome.log), the brain open in Obsidian, Staffbox wallpaper and welcome page"

step "Proof: a short scorecard on this unit"
CARD=""
if [ -z "$SKIP_PROOF" ]; then
  OUT=$(cd / && staffbox eval $SB/examples/fieldstone-it/vault $SB/examples/fieldstone-it/tests.jsonl --model $MODEL --modes brain+quote \
        --limit 10 --machine "$(scutil --get ComputerName 2>/dev/null)" --out $SB/install-proof 2>/dev/null | grep -m1 '\*\*all\*\*' || true)
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
| Hermes code | $HREV (pin $HERMES_COMMIT) |
| Tools off (verified) | ${LOCKED_TOOLS[*]} |
| Tools on | ${TOOLS_ON:-none}${MCP:+ · MCP: $MCP} |
| File writes allowed in | ${SAFE_ROOT//:/, } (HERMES_WRITE_SAFE_ROOT) |
| macOS hardening | not run (opt-in: scripts/install.sh --harden-macos, needs an admin) |
| Disk encryption | $(fdesetup status 2>/dev/null | head -1) |
| Model | $MODEL ${EXTRA_MODELS} via Ollama $($OLLAMA --version 2>/dev/null | awk '{print $NF}'), listening on 127.0.0.1 only · context ${CTX:-unknown} |
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
