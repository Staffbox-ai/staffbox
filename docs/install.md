# Installing a Staffbox unit

For the IT provider doing the install. About an hour, most of it downloads. No admin password is needed after macOS setup, and nothing is sent to a cloud AI service.

## What you need
- A Mac mini with Apple silicon (32 GB memory recommended; 16 GB runs the 8B model), power, a wired network port with internet access.
- A screen, keyboard and mouse for the first 15 minutes only.

## 1. macOS setup (15 min, at the Mac)
1. Turn it on and follow Setup Assistant. **Apple ID: choose "Set up later".** A customer unit has no personal Apple ID.
2. Create the local account the customer will own (for example `staffbox`). Record the password in the customer's password vault.
3. System Settings > General > Sharing: turn on **Remote Login** if you will finish the install from your desk. Energy: prevent sleep, start up after a power failure.

## 2. One command (40 min, from anywhere)
```sh
xcode-select --install          # click Install on the Mac's screen once; about 10 minutes
git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src && ~/staffbox-src/scripts/install.sh
```
The installer prints eight numbered steps and stops with a plain-English fix if anything is wrong; run it again and it carries on. It:

| Step | What happens |
|---|---|
| 1 | Checks the Mac: Apple silicon, memory, free disk, no personal Apple ID |
| 2 | Confirms the developer tools (needed for git) |
| 3 | Installs Ollama from its official release, checks the publisher's signature, and runs it **on this Mac only** (127.0.0.1), starting at login |
| 4 | Pulls the model (`MODEL=qwen3:8b` by default; add `EXTRA_MODELS="qwen3:14b"` on 32 GB units) |
| 5 | Installs Hermes Agent with Nous Research's official installer |
| 6 | Creates the worker profile with **no cloud fallback providers** |
| 7 | Sets up the company brain (`~/staffbox/vault`, Obsidian-ready), the demo brains and the `staffbox` command |
| 8 | Proves the unit: runs the first 10 questions of the Fieldstone IT scorecard and writes a **unit card** to `~/staffbox/UNIT.md` |

## 3. Hand-over (5 min)
- Show the customer `~/staffbox/UNIT.md`: model, versions, "cloud AI: off", and the install proof score.
- Turn Remote Login off unless the support agreement says otherwise.
- Give each person who will use it their own SSH key and point them to [connect.md](connect.md) (Hermes desktop app on Windows or Mac, or a browser).
- Next: load 30 to 50 of the customer's own past requests and run their day-0 scorecard (`staffbox eval`).
