param(
    [switch]$BuildOnly
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Get-InnoSetupCompiler {
    $Candidates = @(
        @(
            (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source,
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
        ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique
    )

    if ($Candidates) {
        return $Candidates[0]
    }

    return $null
}

function Ensure-Dependencies {
    $Missing = @()

    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        $Missing += "Python build environment"
    }

    if (-not (Test-Path "vendor\yt-dlp.exe")) {
        $Missing += "yt-dlp.exe"
    }

    if (-not (Test-Path "vendor\ffmpeg.exe") -or -not (Test-Path "vendor\ffprobe.exe")) {
        $Missing += "FFmpeg tools"
    }

    if (-not (Get-InnoSetupCompiler)) {
        $Missing += "Inno Setup 6"
    }

    if ($Missing.Count -gt 0) {
        Write-Host "Preparing missing dependencies: $($Missing -join ', ')"
        & "$PSScriptRoot\get_dependencies.ps1"
    }
}

Write-Host "== SimpleYTDLP GUI installer =="
Ensure-Dependencies

$Python = ".\.venv\Scripts\python.exe"

Write-Host "Cleaning previous GUI build..."
Remove-Item -Recurse -Force build, dist, installer\output, installer\Output -ErrorAction SilentlyContinue
Remove-Item -Force *.spec -ErrorAction SilentlyContinue

$IconArgs = @()
if (Test-Path "assets\app.ico") {
    $IconArgs = @("--icon", "assets\app.ico")
}

Write-Host "Building the GUI..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name "SimpleYTDLP" `
    @IconArgs `
    run.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE"
}

Write-Host "Adding bundled dependencies..."
New-Item -ItemType Directory -Force "dist\SimpleYTDLP\vendor" | Out-Null
Copy-Item "vendor\*" "dist\SimpleYTDLP\vendor" -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Adding app assets and notices..."
New-Item -ItemType Directory -Force "dist\SimpleYTDLP\assets" | Out-Null
Copy-Item "assets\*" "dist\SimpleYTDLP\assets" -Recurse -Force -ErrorAction SilentlyContinue
Copy-Item "THIRD_PARTY_NOTICES.md" "dist\SimpleYTDLP\" -Force
Copy-Item "LICENSE" "dist\SimpleYTDLP\" -Force

$Iscc = Get-InnoSetupCompiler
if (-not $Iscc) {
    throw "Inno Setup 6 was not found. Run .\scripts\get_dependencies.ps1, then rerun .\scripts\install_gui.ps1."
}

$AppSource = Get-Content "simple_ytdlp\app.py" -Raw
if ($AppSource -notmatch 'APP_VERSION\s*=\s*"([^"]+)"') {
    throw "Could not read APP_VERSION from simple_ytdlp\app.py"
}

$AppVersion = $Matches[1]
$InstallerScript = "installer\SimpleYTDLP.iss"
$OutputDir = "installer\output"
$OutputPath = Join-Path (Resolve-Path "installer").Path "output"
$DistPath = (Resolve-Path "dist\SimpleYTDLP").Path

New-Item -ItemType Directory -Force $OutputDir | Out-Null

Write-Host "Creating the Windows setup file..."
& $Iscc `
    "/DAppVersion=$AppVersion" `
    "/DSourceDir=$DistPath" `
    "/O$OutputPath" `
    $InstallerScript

if ($LASTEXITCODE -ne 0) {
    throw "Inno Setup failed with exit code $LASTEXITCODE"
}

$InstallerExe = Join-Path $OutputDir "SimpleYTDLP_Setup_$AppVersion.exe"
if (-not (Test-Path $InstallerExe)) {
    throw "Installer was not created."
}

$InstallerPath = (Resolve-Path $InstallerExe).Path
$SizeMB = [math]::Round((Get-Item $InstallerPath).Length / 1MB, 1)

Write-Host "Installer created: $InstallerPath ($SizeMB MB)"

if (-not $BuildOnly) {
    Write-Host "Launching the GUI installer..."
    Start-Process -FilePath $InstallerPath -Wait
}
