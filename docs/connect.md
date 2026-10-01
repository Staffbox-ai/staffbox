# Use a Staffbox unit from your own computer

Everything runs on the unit. Your computer is only the window. You can use the **Hermes desktop app** (Windows or Mac) or a **web browser**. Both connect over SSH, so the unit is never exposed to the internet and its dashboard never listens on the network.

## Once per person: an SSH key (2 minutes)

Each person gets their own key, so access can be granted and removed one person at a time.

**Windows** (PowerShell; OpenSSH is built into Windows 10 and 11):
```powershell
ssh-keygen -t ed25519 -C "your.name@company"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```
**Mac** (Terminal):
```sh
ssh-keygen -t ed25519 -C "your.name@company"
cat ~/.ssh/id_ed25519.pub
```
Press Enter at each prompt (a passphrase is recommended). Send the one line it prints (starts with `ssh-ed25519`) to whoever administers the unit. It is a public key; it is safe to email.

**The administrator adds it** on the unit (one line per person):
```sh
echo 'ssh-ed25519 AAAA… your.name@company' >> ~/.ssh/authorized_keys
```
To remove someone later, delete their line. The unit accepts keys only; password logins over SSH are off.

**Test** from your computer (use the unit's IP address; `.local` names do not always resolve on Windows):
```sh
ssh <account>@<unit-address> hostname
```

## Option 1: the Hermes desktop app (easiest for everyday use)

1. Download the app for your system from [Nous Research's releases page](https://github.com/NousResearch/hermes-agent/releases) (Windows, macOS, Linux) and install it.
2. Open **Settings → Connections → Add**, choose **SSH**, and fill in:
   - Host: the unit's address; user: `<account>`; key: the key you made above.
   - Hermes path on the unit: `/Users/<account>/.local/bin/hermes`
   - Profile: `zero` (the worker's profile)
   - On a Linux unit the Hermes path is `/home/<account>/.local/bin/hermes`.
3. Connect. The app starts the Hermes server on the unit over SSH. Chats, tools, files and the brain all run on the unit, not on your computer.

## Option 2: a web browser (a fallback; keep the tunnel window open)

1. Open a tunnel and leave the window open:
   ```sh
   ssh -N -L 9119:127.0.0.1:9119 <account>@<unit-address>
   ```
2. Browse to **http://localhost:9119/?profile=zero**.

The dashboard has Chat, Sessions, Models (with token counts), Profiles (the agents), Keys, Kanban (the worker's task board) and Logs.

## Adding an AI key (optional)

The unit runs local models with cloud AI off. To add a cloud model for a specific job, open **Keys** in the dashboard or the desktop app and paste your own provider key. That turns cloud AI on for that provider only, on your account; do it only if your data agreement allows it.

## What not to do

- Do not open the dashboard port (9119) or Ollama's port (11434) to the network or the internet. Always use SSH.
- Do not share one key between people.
