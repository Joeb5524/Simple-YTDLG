# Build and Install SimpleYTDLP

This project uses PyInstaller for both the Windows app folder and the optional setup executable. Inno Setup is not required for the normal build.

## Prerequisites

- Windows
- Python 3.11 or newer
- PowerShell
- Optional but recommended: `yt-dlp.exe`, `ffmpeg.exe`, and `ffprobe.exe` in `vendor\`

The build script creates `.venv` automatically and installs the Python build dependency from `requirements.txt`.

## 1. Prepare downloader tools

Put release binaries here before building a public installer:

```text
vendor\yt-dlp.exe
vendor\ffmpeg.exe
vendor\ffprobe.exe
```

To download only `yt-dlp.exe`:

```powershell
.\scripts\download_tools.ps1
```

Add FFmpeg manually. Without FFmpeg, some MP4 and MP3 downloads may fail on machines that do not already have FFmpeg in `PATH`.

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
installer\output\dist\SimpleYTDLP_Setup.exe
```

Distribute `SimpleYTDLP_Setup.exe` to end users.

## What the installer does

1. Extracts the bundled `dist\SimpleYTDLP\` app files.
2. Installs to `C:\Program Files\SimpleYTDLP\` when writable.
3. Falls back to `%APPDATA%\SimpleYTDLP\` when Program Files is not writable.
4. Creates a Start Menu shortcut named **Simple Video Downloader**.
5. Offers to launch the app after installation.

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

### `Application files not found`

Run the installer build from the repository root:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

The installer expects the app folder to exist at `dist\SimpleYTDLP\` before it is packaged.

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

## Legacy Inno Setup file

`installer\SimpleYTDLP.iss` is kept only as a legacy script. The supported build path is:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```
