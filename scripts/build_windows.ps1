param(
    [switch]$BuildInstaller
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "== SimpleYTDLP Windows build =="

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Activating virtual environment..."
. .\.venv\Scripts\Activate.ps1

Write-Host "Installing build dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-not (Test-Path "vendor\yt-dlp.exe")) {
    Write-Warning "vendor\yt-dlp.exe was not found. The built app can still use yt-dlp from PATH, but the installer will not be self-contained."
}

if (-not (Test-Path "vendor\ffmpeg.exe") -or -not (Test-Path "vendor\ffprobe.exe")) {
    Write-Warning "FFmpeg tools were not found in vendor\. MP4 merging and MP3 conversion may fail on machines without FFmpeg in PATH."
}

Write-Host "Cleaning previous build..."
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

$IconArgs = @()
if (Test-Path "assets\app.ico") {
    $IconArgs = @("--icon", "assets\app.ico")
}

Write-Host "Building app with PyInstaller..."
pyinstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name "SimpleYTDLP" `
    @IconArgs `
    run.py

Write-Host "Copying vendor tools..."
if (Test-Path "vendor") {
    New-Item -ItemType Directory -Force "dist\SimpleYTDLP\vendor" | Out-Null
    Copy-Item "vendor\*" "dist\SimpleYTDLP\vendor" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Copying app assets..."
if (Test-Path "assets") {
    New-Item -ItemType Directory -Force "dist\SimpleYTDLP\assets" | Out-Null
    Copy-Item "assets\*" "dist\SimpleYTDLP\assets" -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Copying notices..."
Copy-Item "THIRD_PARTY_NOTICES.md" "dist\SimpleYTDLP\" -Force
Copy-Item "LICENSE" "dist\SimpleYTDLP\" -Force

Write-Host "Build complete: dist\SimpleYTDLP\SimpleYTDLP.exe"

if ($BuildInstaller) {
    Write-Host "Building self-contained installer..."
    
    $InstallerScript = "scripts\build_installer.py"
    $OutputDir = "installer\output"
    $DistDir = "dist\SimpleYTDLP"
    
    Remove-Item -Recurse -Force $OutputDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $OutputDir | Out-Null
    
    # Build installer with PyInstaller
    pyinstaller `
        --onefile `
        --windowed `
        --name "SimpleYTDLP_Setup" `
        --icon "assets\app.ico" `
        --add-data "$DistDir;dist/SimpleYTDLP" `
        --distpath "$OutputDir\dist" `
        --specpath "$OutputDir\build" `
        --workpath "$OutputDir\build" `
        --clean `
        $InstallerScript
    
    $InstallerExe = "$OutputDir\dist\SimpleYTDLP_Setup.exe"
    if (Test-Path $InstallerExe) {
        $SizeMB = [math]::Round((Get-Item $InstallerExe).Length / 1MB, 1)
        Write-Host "Installer created: $InstallerExe ($SizeMB MB)"
        Write-Host ""
        Write-Host "To install SimpleYTDLP, run:"
        Write-Host "  $InstallerExe"
    } else {
        Write-Error "Installer was not created"
    }
}
