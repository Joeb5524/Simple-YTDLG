param()

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Vendor = Join-Path $RepoRoot "vendor"

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

function Install-InnoSetup {
    if (Get-InnoSetupCompiler) {
        Write-Host "Inno Setup 6 is already available."
        return
    }

    $Choco = (Get-Command "choco.exe" -ErrorAction SilentlyContinue).Source
    if ($Choco) {
        Write-Host "Installing Inno Setup 6 with Chocolatey..."
        & $Choco install innosetup -y --no-progress
        if ($LASTEXITCODE -ne 0) {
            throw "Chocolatey could not install Inno Setup 6."
        }

        if (Get-InnoSetupCompiler) {
            return
        }
    }

    $Winget = (Get-Command "winget.exe" -ErrorAction SilentlyContinue).Source
    if ($Winget) {
        Write-Host "Installing Inno Setup 6 with winget..."
        & $Winget install --id JRSoftware.InnoSetup -e --silent --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            throw "winget could not install Inno Setup 6."
        }

        if (Get-InnoSetupCompiler) {
            return
        }
    }

    throw "Inno Setup 6 is required. Install it, then rerun .\scripts\get_dependencies.ps1."
}

Write-Host "== SimpleYTDLP dependencies =="

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}

$Python = ".\.venv\Scripts\python.exe"

Write-Host "Installing Python build dependencies..."
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

New-Item -ItemType Directory -Force $Vendor | Out-Null

Write-Host "Downloading yt-dlp.exe..."
Invoke-WebRequest `
    -Uri "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe" `
    -OutFile (Join-Path $Vendor "yt-dlp.exe")

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

Install-InnoSetup

Write-Host ""
Write-Host "Dependencies are ready."
Write-Host "Next, install the GUI with:"
Write-Host "  .\scripts\install_gui.ps1"
