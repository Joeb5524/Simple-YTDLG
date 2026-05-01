param(
    [switch]$SkipFFmpeg
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $RepoRoot "vendor"
New-Item -ItemType Directory -Force $Vendor | Out-Null

Write-Host "Downloading yt-dlp.exe..."
Invoke-WebRequest `
    -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" `
    -OutFile (Join-Path $Vendor "yt-dlp.exe")

Write-Host "yt-dlp.exe saved to vendor\."

if (-not $SkipFFmpeg) {
    Write-Host "Downloading FFmpeg tools..."
    $TempDir = Join-Path ([System.IO.Path]::GetTempPath()) "SimpleYTDLP-ffmpeg"
    $ZipPath = Join-Path ([System.IO.Path]::GetTempPath()) "SimpleYTDLP-ffmpeg.zip"

    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue

    Invoke-WebRequest `
        -Uri "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip" `
        -OutFile $ZipPath

    Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

    $Ffmpeg = Get-ChildItem -Path $TempDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
    $Ffprobe = Get-ChildItem -Path $TempDir -Recurse -Filter "ffprobe.exe" | Select-Object -First 1

    if (-not $Ffmpeg -or -not $Ffprobe) {
        throw "Could not find ffmpeg.exe and ffprobe.exe in the downloaded FFmpeg archive."
    }

    Copy-Item $Ffmpeg.FullName (Join-Path $Vendor "ffmpeg.exe") -Force
    Copy-Item $Ffprobe.FullName (Join-Path $Vendor "ffprobe.exe") -Force

    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
    Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue

    Write-Host "ffmpeg.exe and ffprobe.exe saved to vendor\."
} else {
    Write-Host ""
    Write-Host "Skipped FFmpeg download. Add these files manually before public release builds:"
    Write-Host "  vendor\ffmpeg.exe"
    Write-Host "  vendor\ffprobe.exe"
}

Write-Host ""
Write-Host "To build the installer, run:"
Write-Host "  .\scripts\build_windows.ps1 -BuildInstaller"
