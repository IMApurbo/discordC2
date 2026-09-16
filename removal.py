#!/usr/bin/env python3
"""
Discord C2 — Persistence Removal Script
Run this on the target machine to cleanly remove all traces.
"""

import os
import sys
import subprocess
import shutil
import time
import traceback
from pathlib import Path


# ── keep window open helper ──────────────────────────────────
def pause(msg="Press ENTER to close..."):
    try:
        input(f"\n{msg}")
    except Exception:
        pass


# ── Colours ─────────────────────────────────────────────────
def enable_ansi():
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetConsoleMode(
            ctypes.windll.kernel32.GetStdHandle(-11), 7)

R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
B = "\033[94m"; C = "\033[96m"; W = "\033[97m"; E = "\033[0m"

def info(msg):  print(f"{B}[*]{E}  {msg}")
def ok(msg):    print(f"{G}[+]{E}  {msg}")
def warn(msg):  print(f"{Y}[!]{E}  {msg}")
def fail(msg):  print(f"{R}[-]{E}  {msg}")
def step(msg):  print(f"\n{W}══ {msg} ══{E}")
def ask(msg):
    print(f"{C}[?]{E}  {msg}", end="", flush=True)
    return input()


def banner():
    print(f"{W}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║      Discord C2 — Full Removal Tool                 ║")
    print("║      Cleans registry, tasks, files, processes       ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(f"{E}")


# ============================================================
# helpers
# ============================================================
def run_cmd(cmd, shell=True):
    try:
        r = subprocess.run(
            cmd, shell=shell,
            capture_output=True, text=True)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def run_ps(script):
    return run_cmd(
        ["powershell", "-WindowStyle", "Hidden",
         "-NonInteractive", "-NoProfile",
         "-Command", script],
        shell=False)


def delete_file(path):
    p = Path(path)
    if p.exists():
        try:
            p.unlink()
            ok(f"Deleted      : {p}")
            return True
        except Exception as e:
            fail(f"Cannot delete: {p}  ({e})")
            return False
    else:
        info(f"Not found    : {p}")
        return True


def delete_dir(path):
    p = Path(path)
    if p.exists():
        try:
            shutil.rmtree(str(p), ignore_errors=True)
            ok(f"Deleted dir  : {p}")
            return True
        except Exception as e:
            fail(f"Cannot delete: {p}  ({e})")
            return False
    else:
        info(f"Not found    : {p}")
        return True


# ============================================================
# REMOVAL STEPS
# ============================================================

def kill_processes():
    step("Killing Implant Processes")

    names = ["c2_client.exe", "wscript.exe",
             "winupdate.exe", "winsec.exe"]

    for name in names:
        rc, out, _ = run_cmd(f'taskkill /F /IM "{name}" /T')
        if rc == 0:
            ok(f"Killed       : {name}")
        else:
            info(f"Not running  : {name}")

    # kill any python running our scripts
    run_ps(
        "Get-Process python,python3,pythonw "
        "-ErrorAction SilentlyContinue | Stop-Process -Force"
    )

    time.sleep(1)
    ok("Process sweep done.")


def remove_registry():
    step("Removing Registry Persistence")

    entries = [
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run", "WinSec"),
        (r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run", "WinSec"),
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
         "WindowsDefenderUpdate"),
        (r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
         "WindowsDefenderUpdate"),
        (r"HKCU\Software\Wow6432Node\Microsoft\Windows"
         r"\CurrentVersion\Run", "WinSec"),
        (r"HKLM\Software\Wow6432Node\Microsoft\Windows"
         r"\CurrentVersion\Run", "WinSec"),
    ]

    for hive, value in entries:
        rc, out, _ = run_cmd(
            f'reg delete "{hive}" /v "{value}" /f')
        if rc == 0:
            ok(f"Removed reg  : {hive}\\{value}")
        else:
            info(f"Not found    : {hive}\\{value}")


def remove_tasks():
    step("Removing Scheduled Tasks")

    task_names = [
        "WinDefUp",
        "WindowsDefenderUpdate",
        "WinSec",
        "WinSecUpdate",
    ]

    for task in task_names:
        rc, out, _ = run_cmd(f'schtasks /delete /tn "{task}" /f')
        if rc == 0:
            ok(f"Removed task : {task}")
        else:
            info(f"Not found    : {task}")

    # PowerShell wildcard sweep
    rc, out, _ = run_ps(
        'Get-ScheduledTask -ErrorAction SilentlyContinue | '
        'Where-Object { $_.TaskName -match "WinDef|WinSec|wupd|C2" } | '
        'Unregister-ScheduledTask -Confirm:$false '
        '-ErrorAction SilentlyContinue'
    )
    if out:
        ok(f"PS sweep     : {out}")


def remove_startup():
    step("Removing Startup Folder Files")

    appdata = os.environ.get("APPDATA", "")
    startup = os.path.join(
        appdata,
        r"Microsoft\Windows\Start Menu\Programs\Startup")

    names = ["wupd.vbs", "wupd.bat",
             "winsec.vbs", "winsec.bat",
             "windefup.vbs", "windefup.bat"]

    for n in names:
        delete_file(os.path.join(startup, n))

    # All-users startup
    all_startup = (r"C:\ProgramData\Microsoft\Windows"
                   r"\Start Menu\Programs\Startup")
    for n in names:
        delete_file(os.path.join(all_startup, n))


def remove_vbs_launchers():
    step("Removing VBS Launcher Files")

    appdata = os.environ.get("APPDATA", "")
    names = [
        "winsec_run.vbs",
        "winsec_task.vbs",
        "winsec_launcher.vbs",
        "wintask_launcher.vbs",
        "windefup.vbs",
    ]
    for n in names:
        delete_file(os.path.join(appdata, n))


def remove_executables():
    step("Removing Implant Files")

    desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    appdata = Path(os.environ.get("APPDATA", ""))
    temp    = Path(os.environ.get("TEMP", r"C:\Temp"))

    targets = []

    for name in ["c2_client.exe", "update.exe",
                 "winupdate.exe", "svchost32.exe"]:
        targets.append(desktop / name)
        targets.append(appdata / name)

    targets.append(temp / "c2_build")  # whole build dir
    targets.append(temp / "sc.png")
    targets.append(temp / "wc.jpg")

    for loc in targets:
        if loc.is_dir():
            delete_dir(loc)
        else:
            delete_file(loc)

    # custom path
    print()
    v = ask("Custom EXE path to delete (Enter=skip): ").strip()
    if v:
        p = Path(v)
        if p.exists():
            delete_file(p)
        else:
            warn(f"Path not found: {v}")


def remove_wmi():
    step("Checking WMI Subscriptions")

    scripts = [
        ('Get-WMIObject -Namespace root\\subscription '
         '-Class __EventFilter -ErrorAction SilentlyContinue | '
         'Where-Object { $_.Name -match "Win|Sec|C2|Update" } | '
         'Remove-WmiObject -ErrorAction SilentlyContinue'),
        ('Get-WMIObject -Namespace root\\subscription '
         '-Class CommandLineEventConsumer '
         '-ErrorAction SilentlyContinue | '
         'Where-Object { $_.Name -match "Win|Sec|C2|Update" } | '
         'Remove-WmiObject -ErrorAction SilentlyContinue'),
    ]

    for ps in scripts:
        rc, out, _ = run_ps(ps)
        if out:
            ok(f"WMI removed  : {out[:60]}")

    ok("WMI sweep done.")


def remove_firewall():
    step("Removing Firewall Rules")

    names = ["WinSec", "WindowsDefenderUpdate",
             "c2_client", "WinDefUp"]

    for name in names:
        rc, out, _ = run_cmd(
            f'netsh advfirewall firewall delete rule name="{name}"')
        if rc == 0 and "deleted" in out.lower():
            ok(f"Removed rule : {name}")
        else:
            info(f"No rule      : {name}")


def clean_event_logs():
    step("Event Log Cleanup")

    v = ask("Clear Windows Event Logs? [y/N]: ").strip().lower()
    if v != "y":
        info("Skipped.")
        return

    logs = [
        "Application", "Security", "System",
        "Microsoft-Windows-TaskScheduler/Operational",
        "Microsoft-Windows-PowerShell/Operational",
    ]

    for log in logs:
        rc, out, _ = run_ps(
            f'Clear-EventLog -LogName "{log}" '
            f'-ErrorAction SilentlyContinue')
        if rc == 0:
            ok(f"Cleared      : {log}")
        else:
            rc2, _, _ = run_cmd(f'wevtutil cl "{log}"')
            if rc2 == 0:
                ok(f"Cleared      : {log}")
            else:
                warn(f"Could not clear (need admin): {log}")


def clean_prefetch():
    step("Prefetch Cleanup")

    v = ask("Delete implant prefetch entries? [y/N]: ").strip().lower()
    if v != "y":
        info("Skipped.")
        return

    prefetch = Path(r"C:\Windows\Prefetch")
    if not prefetch.exists():
        info("Prefetch folder not found.")
        return

    patterns = ["C2_CLIENT*", "WSCRIPT*", "PYTHON*",
                "WINUPDATE*", "WINSEC*"]
    found = 0
    for pat in patterns:
        for f in prefetch.glob(pat):
            try:
                f.unlink()
                ok(f"Deleted      : {f.name}")
                found += 1
            except Exception as e:
                warn(f"Cannot delete (need admin): {f.name}  ({e})")

    if found == 0:
        info("No matching prefetch files found.")


def verify():
    step("Verification Check")

    issues = []

    # Registry
    reg_checks = [
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
         "WinSec"),
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
         "WindowsDefenderUpdate"),
    ]
    for hive, value in reg_checks:
        rc, out, _ = run_cmd(
            f'reg query "{hive}" /v "{value}"')
        if rc == 0:
            issues.append(f"Registry still present : {hive}\\{value}")

    # Tasks
    for task in ["WinDefUp", "WindowsDefenderUpdate"]:
        rc, _, _ = run_cmd(f'schtasks /query /tn "{task}"')
        if rc == 0:
            issues.append(f"Scheduled task still present : {task}")

    # Startup files
    appdata = os.environ.get("APPDATA", "")
    startup = os.path.join(
        appdata,
        r"Microsoft\Windows\Start Menu\Programs\Startup")
    for name in ["wupd.vbs", "wupd.bat"]:
        if os.path.isfile(os.path.join(startup, name)):
            issues.append(f"Startup file still present : {name}")

    # VBS launchers
    for name in ["winsec_run.vbs", "winsec_task.vbs"]:
        if os.path.isfile(os.path.join(appdata, name)):
            issues.append(f"VBS launcher still present : {name}")

    # Result
    print()
    if not issues:
        print(f"{G}╔══════════════════════════════════════════════╗{E}")
        print(f"{G}║   ✓  All clean — no traces found             ║{E}")
        print(f"{G}╚══════════════════════════════════════════════╝{E}")
    else:
        print(f"{R}╔══════════════════════════════════════════════╗{E}")
        print(f"{R}║   ✗  Some traces remain:                     ║{E}")
        print(f"{R}╚══════════════════════════════════════════════╝{E}")
        for issue in issues:
            fail(f"  {issue}")
        print(f"\n{Y}  Tip: Right-click → Run as Administrator{E}")


# ============================================================
# MAIN
# ============================================================
def main():
    enable_ansi()
    banner()

    if sys.platform != "win32":
        fail("Windows only.")
        pause()
        sys.exit(1)

    print(f"{Y}  This will remove all C2 persistence traces.{E}")
    print(f"{Y}  For full cleanup right-click → Run as Administrator.{E}\n")

    v = ask("Continue with removal? [Y/n]: ").strip().lower()
    if v == "n":
        print("\nAborted.")
        pause()
        sys.exit(0)

    print()

    try:
        kill_processes()
        remove_registry()
        remove_tasks()
        remove_startup()
        remove_vbs_launchers()
        remove_executables()
        remove_wmi()
        remove_firewall()
        clean_event_logs()
        clean_prefetch()
        verify()
    except Exception as e:
        print()
        fail(f"Unexpected error: {e}")
        traceback.print_exc()

    print(f"\n{G}[+]{E} Removal script finished.")

    # ── ALWAYS pause at the end so window stays open ──────
    pause("Press ENTER to close this window...")


if __name__ == "__main__":
    main()