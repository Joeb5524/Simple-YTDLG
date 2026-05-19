# Build and Install SimpleYTDLP

Only the two-script flow below is supported for preparing dependencies and installing the GUI.

## Prerequisites

- Windows
- PowerShell
- Python 3.11 or newer

## 1. Get dependencies

```powershell
.\scripts\get_dependencies.ps1
```

This script:

- creates `.venv`
- installs the Python build packages from `requirements.txt`
- downloads `yt-dlp.exe`
- downloads `ffmpeg.exe` and `ffprobe.exe`
- makes sure Inno Setup 6 is available

Downloaded runtime tools are stored in `vendor\` and bundled into the GUI installer.

## 2. Install the GUI

```powershell
.\scripts\install_gui.ps1
```

This script builds the Windows setup file and launches it. The setup file is created here:

```text
installer\output\SimpleYTDLP_Setup_1.1.exe
```

## What the installer does

1. Installs SimpleYTDLP and its bundled downloader tools.
2. Installs to Program Files for all users, or per-user when the user chooses the non-admin install mode.
3. Creates a Start Menu shortcut named **Simple Video Downloader**.
4. Optionally creates a desktop shortcut.
5. Registers the app in Windows **Apps & features** / **Add or remove programs**.
6. Installs a standard Windows uninstaller.
7. Offers to launch the app after installation.

Running a newer installer over an existing installation upgrades the app in place. User settings and download history are stored outside the install directory and are preserved.

## Troubleshooting

### PowerShell blocks script execution

Run PowerShell from the repository root and allow scripts for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the two scripts again.

### Python is missing

Install Python 3.11 or newer, make sure `python` is available in PowerShell, then run:

```powershell
.\scripts\get_dependencies.ps1
```

### Inno Setup could not be installed automatically

Install Inno Setup 6, then run:

```powershell
.\scripts\get_dependencies.ps1
.\scripts\install_gui.ps1
```

### Bundled downloader tools are missing

Run the dependency script again:

```powershell
.\scripts\get_dependencies.ps1
```

The GUI installer bundles `vendor\yt-dlp.exe`, `vendor\ffmpeg.exe`, and `vendor\ffprobe.exe`.

## Release checklist

1. Update `APP_VERSION` in `simple_ytdlp\app.py`.
2. Run `.\scripts\get_dependencies.ps1`.
3. Run `.\scripts\install_gui.ps1`.
4. Commit and push the changes.
5. Create and push a matching version tag:

```powershell
git tag v1.1
git push <remote> v1.1
```

GitHub Actions validates that `v1.1` matches `APP_VERSION = "1.1"`, builds the GUI installer, creates a GitHub Release, and attaches the setup file.
