$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $RepoRoot "vendor"
New-Item -ItemType Directory -Force $Vendor | Out-Null

Write-Host "Downloading yt-dlp.exe..."
Invoke-WebRequest `
    -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" `
    -OutFile (Join-Path $Vendor "yt-dlp.exe")

Write-Host "yt-dlp.exe saved to vendor\."
Write-Host ""
Write-Host "FFmpeg is also recommended. Because FFmpeg builds vary by licence/distribution choice, add these files manually:"
Write-Host "  vendor\ffmpeg.exe"
Write-Host "  vendor\ffprobe.exe"
Write-Host ""
Write-Host "After adding FFmpeg, run:"
Write-Host "  .\scripts\build_windows.ps1 -BuildInstaller"
