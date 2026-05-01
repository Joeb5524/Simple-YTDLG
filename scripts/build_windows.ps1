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
    Write-Host "Building Windows installer with Inno Setup..."

    $InstallerScript = "installer\SimpleYTDLP.iss"
    $OutputDir = "installer\output"
    $DistDir = "dist\SimpleYTDLP"

    $IsccCandidates = @(
        @(
            (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source,
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
    )

    if (-not $IsccCandidates) {
        throw "Inno Setup 6 was not found. Install it from https://jrsoftware.org/isinfo.php, then rerun: .\scripts\build_windows.ps1 -BuildInstaller"
    }

    $Iscc = $IsccCandidates[0]
    $AppSource = Get-Content "simple_ytdlp\app.py" -Raw
    if ($AppSource -notmatch 'APP_VERSION\s*=\s*"([^"]+)"') {
        throw "Could not read APP_VERSION from simple_ytdlp\app.py"
    }

    $AppVersion = $Matches[1]
    $DistPath = (Resolve-Path $DistDir).Path
    $OutputPath = Join-Path (Resolve-Path "installer").Path "output"

    Remove-Item -Recurse -Force $OutputDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $OutputDir | Out-Null

    & $Iscc `
        "/DAppVersion=$AppVersion" `
        "/DSourceDir=$DistPath" `
        "/O$OutputPath" `
        $InstallerScript

    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup failed with exit code $LASTEXITCODE"
    }

    $InstallerExe = Join-Path $OutputDir "SimpleYTDLP_Setup_$AppVersion.exe"
    if (Test-Path $InstallerExe) {
        $SizeMB = [math]::Round((Get-Item $InstallerExe).Length / 1MB, 1)
        Write-Host "Installer created: $InstallerExe ($SizeMB MB)"
        Write-Host ""
        Write-Host "To install or upgrade SimpleYTDLP, run:"
        Write-Host "  $InstallerExe"
    } else {
        Write-Error "Installer was not created"
    }
}
