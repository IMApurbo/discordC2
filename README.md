
<div align="center">

<img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white">
<img src="https://img.shields.io/badge/Discord-C2-5865F2?style=for-the-badge&logo=discord&logoColor=white">
<img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge">

<br><br>

# DiscordC2

**Control a Windows machine through Discord.**  
No server. No port forwarding. Just a bot token.

<br>

[Features](#-features) • [Commands](#-commands) • [Persistence](#-persistence) • [Removal](#-removal) • [Disclaimer](#-disclaimer)

</div>

---

## 💡 Features

- 💻 Interactive shell — type commands directly in Discord
- 📸 Screenshot & webcam capture
- 🔍 Recon — sysinfo, processes, netstat, ARP
- 📁 File upload & download
- 📎 Clipboard read / write
- ⌨️ Keylogger
- 🔒 Hidden persistence — registry, scheduled task, startup folder
- 🎮 Full Discord UI — slash commands, buttons, popup text box
- 🗑️ Removal tool included

---

## 💬 Commands

> In **interactive mode** the `[id]` field is always optional.

| Command | Description |
|---|---|
| `/ls` | List active sessions |
| `/interact [id]` | Start interactive shell |
| `/exit` | Leave interactive mode |
| `/help` | Show all commands |
| `/cmd <command> [id]` | Run a shell command |
| `/shell [id]` | Open a popup text box to type a command |
| `/sysinfo [id]` | System information |
| `/screenshot [id]` | Take a screenshot |
| `/webshot [id]` | Capture webcam image |
| `/processes [id]` | List running processes |
| `/netstat [id]` | Show network connections |
| `/arp [id]` | Show ARP table |
| `/download <path> [id]` | Get a file from the target |
| `/upload <url> <dest> [id]` | Send a file to the target |
| `/clipboard_get [id]` | Read clipboard |
| `/clipboard_set <text> [id]` | Write to clipboard |
| `/keyscan_start [id]` | Start keylogger |
| `/keyscan_dump [id]` | Dump captured keys |
| `/keyscan_stop [id]` | Stop keylogger |
| `/persist_reg [id]` | Persist via registry |
| `/persist_task [id]` | Persist via scheduled task |
| `/persist_startup [id]` | Persist via startup folder |
| `/persist_all [id]` | Install all persistence methods |

---

## 🔒 Persistence

All methods run **completely invisible** — no window, no flash, no console.

| Method | Trigger | Needs Admin |
|---|---|---|
| Registry `HKCU\...\Run` | Login | ❌ |
| Scheduled Task | Login | ❌ |
| Startup Folder `.vbs` | Login | ❌ |

---

## 🗑️ Removal

Run on the target machine to clean every trace:

```batch
python removal.py
```

> Tip: Right-click → **Run as Administrator** for full cleanup.

Removes registry keys, scheduled tasks, startup files, VBS launchers, the EXE, event logs, and prefetch entries. Ends with a verification check.

---

## ⚠️ Disclaimer

For **educational and authorized security research only**.  
Only use on systems you **own or have explicit permission** to test.  
The author is not responsible for any misuse.

---

<div align="center">

**Made by [IMApurbo](https://github.com/IMApurbo)**

[![GitHub](https://img.shields.io/badge/GitHub-IMApurbo-181717?style=for-the-badge&logo=github)](https://github.com/IMApurbo)
[![Repo](https://img.shields.io/badge/discordC2-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://github.com/IMApurbo/discordC2)

⭐ Star if you found it useful

</div>
