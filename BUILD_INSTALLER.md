# Build and Install SimpleYTDLP

This project uses PyInstaller for the Windows app folder and Inno Setup for the Windows installer/uninstaller.

## Prerequisites

- Windows
- Python 3.11 or newer
- PowerShell
- Inno Setup 6, required only when building the installer
- Optional but recommended: `yt-dlp.exe`, `ffmpeg.exe`, and `ffprobe.exe` in `vendor\`

The build script creates `.venv` automatically and installs the Python build dependency from `requirements.txt`.

## 1. Prepare downloader tools

Put release binaries here before building a public installer:

```text
vendor\yt-dlp.exe
vendor\ffmpeg.exe
vendor\ffprobe.exe
```

To download `yt-dlp.exe`, `ffmpeg.exe`, and `ffprobe.exe`:

```powershell
.\scripts\download_tools.ps1
```

The script uses the latest `yt-dlp` Windows binary and the latest Windows GPL FFmpeg build from `yt-dlp/FFmpeg-Builds`. To skip FFmpeg and add your own build manually, run:

```powershell
.\scripts\download_tools.ps1 -SkipFFmpeg
```

Without FFmpeg, some MP4 and MP3 downloads may fail on machines that do not already have FFmpeg in `PATH`.

## 2. Build the app folder

```powershell
.\scripts\build_windows.ps1
```

Output:

```text
dist\SimpleYTDLP\SimpleYTDLP.exe
```

This folder includes the app, bundled vendor tools, assets, licence, and third-party notices. You can zip and distribute the whole `dist\SimpleYTDLP\` folder if you want a portable-style release.

## 3. Build the setup executable

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

Output:

```text
installer\output\SimpleYTDLP_Setup_1.0.2.exe
```

Distribute the versioned setup EXE, for example `SimpleYTDLP_Setup_1.0.2.exe`, to end users.

## What the installer does

1. Extracts the bundled `dist\SimpleYTDLP\` app files.
2. Installs to Program Files for all users, or per-user when the user chooses the non-admin install mode.
3. Creates a Start Menu shortcut named **Simple Video Downloader**.
4. Optionally creates a desktop shortcut.
5. Registers the app in Windows **Apps & features** / **Add or remove programs**.
6. Installs a standard Windows uninstaller.
7. Offers to launch the app after installation.

Running a newer installer over an existing installation upgrades the app in place. User settings and download history are stored outside the install directory and are preserved.

## Clean build output

```powershell
.\scripts\clean.ps1
```

This removes `build\`, `dist\`, generated installer output, and generated `.spec` files.

## Troubleshooting

### PowerShell blocks script execution

Run PowerShell from the repository root and allow scripts for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then run the build command again.

### Inno Setup is missing

Install Inno Setup 6, then run the installer build again:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

The build script looks for `ISCC.exe` in `PATH`, `C:\Program Files\Inno Setup 6\`, and `C:\Program Files (x86)\Inno Setup 6\`.

### `Application files not found`

Run the installer build from the repository root:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

The installer expects the app folder to exist at `dist\SimpleYTDLP\` before it is packaged. The standard build command creates it automatically before invoking Inno Setup.

### Installer is not self-contained

Make sure these files exist before building:

```text
vendor\yt-dlp.exe
vendor\ffmpeg.exe
vendor\ffprobe.exe
```

The build script warns when they are missing. The app may still work on developer machines because tools can be found through `PATH`, but that is not reliable for end users.

### Shortcut icon is missing

Rebuild with the current script:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

The build copies `assets\app.ico` into the app folder so the installed shortcut can use it.

## Release checklist

1. Update `APP_VERSION` in `simple_ytdlp\app.py`.
2. Run `.\scripts\download_tools.ps1` or put current `yt-dlp.exe`, `ffmpeg.exe`, and `ffprobe.exe` in `vendor\`.
3. Commit and push the changes.
4. Create and push a matching version tag:

```powershell
git tag v1.0.2
git push <remote> v1.0.2
```

GitHub Actions validates that `v1.0.2` matches `APP_VERSION = "1.0.2"`, builds the installer, creates a GitHub Release, and attaches the installer.

For a local test build, run:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```
