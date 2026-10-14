# Installing a Staffbox unit

For the IT provider doing the install, on a Mac (mini or Studio). For a Linux + NVIDIA unit, see [hardware.md](hardware.md#staffbox-custom-linux--nvidia). About an hour, most of it downloads. Nothing is sent to a cloud AI service.

**Admin rights, plainly.** The installer never calls `sudo`, but the account running it must be an **administrator** so it can put Ollama and Obsidian in `/Applications`. Three things need an admin password: turning on FileVault (`sudo fdesetup enable`), the opt-in hardening step (`--harden-macos`, below), and the separate worker account we recommend for customer units (below).

## What you need
- A Mac mini with Apple silicon (32 GB memory recommended; 16 GB runs the 8B model), power, a wired network port with internet access.
- A screen, keyboard and mouse for the first 15 minutes only.

## 1. macOS setup (15 min, at the Mac)
1. Turn it on and follow Setup Assistant. **Apple ID: choose "Set up later".** A customer unit has no personal Apple ID.
2. Create the local account the customer will own (for example `staffbox`), as an administrator for now. Record the password in the customer's password vault. For a customer unit, see [Recommended: a separate standard user](#recommended-a-separate-standard-user-for-the-worker) before you start.
3. System Settings > General > Sharing: turn on **Remote Login** if you will finish the install from your desk. Energy: prevent sleep, start up after a power failure.
4. Turn on disk encryption: `sudo fdesetup enable`, and keep the recovery key in the customer's password vault. The installer stops if FileVault is off (a demo box with no customer data can run it with `DEMO_UNIT=1`).

## 2. One command (40 min, from anywhere)
```sh
xcode-select --install          # click Install on the Mac's screen once; about 10 minutes
git clone https://github.com/Staffbox-ai/staffbox ~/staffbox-src && ~/staffbox-src/scripts/install.sh
```
The installer prints nine numbered steps and stops with a plain-English fix if anything is wrong; run it again and it carries on. It:

| Step | What happens |
|---|---|
| 1 | Checks the Mac: Apple silicon, memory, free disk, no personal Apple ID, FileVault on |
| 2 | Confirms the developer tools (needed for git) |
| 3 | Installs Ollama from its official release into a private temp folder, checks the **sha256 GitHub publishes** for the file and the publisher's code signature, and runs it **on this Mac only** (127.0.0.1) from the `ai.staffbox.ollama` LaunchAgent; warns if anything else is serving port 11434 |
| 4 | Pulls the model (`MODEL=qwen3:8b` by default; add `EXTRA_MODELS="qwen3:14b"` on 32 GB units), loads it and **warns if the effective context is not 65536** |
| 5 | Installs Hermes Agent, **pinned to v0.21.7** (commit `71d34ba`): Nous Research's installer is taken from that commit, its sha256 is checked against the one in `install.sh`, and it runs from a file (no `curl \| bash`); warns if the code is not at the pin |
| 6 | Creates the worker profile with **no cloud fallback providers**, and limits the worker's file writes to `~/staffbox/vault` and `~/staffbox/work` (`HERMES_WRITE_SAFE_ROOT`) |
| 7 | Sets up the company brain (`~/staffbox/vault`, Obsidian-ready), the demo brains and the `staffbox` command |
| 8 | Sets up the desktop, dashboard and welcome page; **turns off the risky tool groups and checks each one is off** (the install stops if one is still on); makes the worker's `config.yaml` and `.env` read-only |
| 9 | Proves the unit: runs the first 10 questions of the Fieldstone IT scorecard and writes a **unit card** to `~/staffbox/UNIT.md` (versions, Hermes commit, tools on and off, write folders) |

**Hermes version.** `scripts/install.sh` installs Hermes at the pinned commit (`HERMES_COMMIT`, v0.21.7, 12 Oct 2026) using the upstream installer's `--commit` flag. An existing Hermes is never changed by the installer; it prints the installed version and the commit, and the unit card records both. To move the pin for new installs, set `HERMES_COMMIT` to a SHA on NousResearch/hermes-agent `main`, set `HERMES_INSTALLER_SHA256` to the sha256 of `scripts/install.sh` at that SHA (the command is in a comment next to it), and update this page.

## 3. Opt-in: macOS hardening (5 min, needs an admin password)

The default install changes nothing that needs `sudo`. These controls do, so the IT provider runs one extra command, as the unit's user (not with `sudo`; it asks for the password itself):
```sh
~/staffbox-src/scripts/install.sh --harden-macos
```

| Control | Default install | With `--harden-macos` |
|---|---|---|
| macOS application firewall + stealth mode | not changed | on, checked after |
| SSH password and keyboard-interactive logins | not changed | off, via `/etc/ssh/sshd_config.d/000-staffbox-keys-only.conf`; checked with `sshd -T` |
| Worker's Hermes `config.yaml` and `.env` | read-only (`chmod a-w`): a speed bump only | system-immutable (`chflags schg`): cannot be edited, replaced or deleted without an admin |
| Recorded in `~/staffbox/UNIT.md` | "not run" | firewall state, effective SSH settings, lock |

It refuses to turn off SSH passwords if Remote Login is on and `~/.ssh/authorized_keys` is empty, so nobody is locked out. Test that your key still logs in from a second window before you close the first. Run it again after any re-install (a re-install rewrites the unit card), and unlock first if you re-run the installer: `sudo chflags noschg ~/.hermes/profiles/zero/config.yaml ~/.hermes/profiles/zero/.env`.

## Recommended: a separate standard user for the worker

Read-only files and the write safe-root stop accidents, not a determined process running as the same user. The real separation is that the worker's account cannot become admin. For customer units:
1. In Setup Assistant, create an **administrator** account for the IT provider (for example `itadmin`). Its password stays with the IT provider.
2. System Settings > Users & Groups > Add User: create `staffbox` as **Administrator** (needed only during the install, to write `/Applications`).
3. Log in to the Mac's screen as `staffbox`, run the one command (section 2), then `--harden-macos` (section 3).
4. Take admin away from `staffbox` (from the `itadmin` account):
   ```sh
   sudo dseditgroup -o edit -d staffbox -t user admin
   dseditgroup -o checkmember -m staffbox admin    # should say: no staffbox is NOT a member of admin
   ```
5. From now on the worker runs as a standard user: it cannot `sudo`, install apps in `/Applications`, or undo the firewall, SSH or `schg` settings. Updates and key changes are done by `itadmin`.

## Updating (manual, on purpose)

Units do not update themselves. To update Hermes, Ollama or the model:
1. Before: run the site's scorecard and keep the result (`staffbox eval … --out ~/staffbox/before`). Back up the brain: `git -C ~/staffbox/vault log -1` if it is a git repo, otherwise copy the folder.
2. Unlock if hardened: `sudo chflags noschg ~/.hermes/profiles/<profile>/config.yaml ~/.hermes/profiles/<profile>/.env`.
3. Update (`hermes update`, or a new Ollama release), then re-run `scripts/install.sh` so the tool lock-down and write folders are checked again, and `--harden-macos` if the unit had it.
4. After: run the same scorecard. If it is worse, roll back.

**Roll back:** reinstall Hermes at the previous pin with Nous Research's installer from that commit: download `https://raw.githubusercontent.com/NousResearch/hermes-agent/<previous commit>/scripts/install.sh` to a file, check its sha256, run `bash <file> --commit <previous commit>`, then re-run `scripts/install.sh` (and `--harden-macos`). The previous commit is in the old unit card. Restore the brain from the backup in step 1 (`git -C ~/staffbox/vault checkout <commit> -- .` if it is a git repo). Rehearse this on a demo unit before relying on it.

## 4. Hand-over (5 min)
- Show the customer `~/staffbox/UNIT.md`: model, versions, "cloud AI: off", and the install proof score.
- Remote Login: turn it off, or keep it on key-only if the customer agrees in writing to remote support. Key-only means adding each person's public key to `~/.ssh/authorized_keys` first, then running `--harden-macos` (section 3). Test that your key still logs in before you close the session.
- Give each person who will use it their own SSH key and point them to [connect.md](connect.md) (Hermes desktop app on Windows or Mac, or a browser).
- Next: load 30 to 50 of the customer's own past requests and run their day-0 scorecard (`staffbox eval`).
