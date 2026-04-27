# SimpleYTDLP

SimpleYTDLP is a lightweight Windows GUI for `yt-dlp`. It is designed for people who want the basics without learning downloader flags:

- paste one or more links
- choose **Video file (MP4)** or **Audio file (MP3)**
- choose **Best quality** or **Smaller file**
- click **Start Download**
- open the completed file or the Downloads folder

The app intentionally hides advanced `yt-dlp` options such as format codes, cookies, proxies, SponsorBlock, archive files, and metadata flags.

## Features

- Multi-link download queue
- Large text and simple high-contrast layout
- Defaults to the user's Downloads folder
- Plain-English success and error messages
- Progress bar and recent downloads list
- Clipboard link detection
- Cancel active download
- Prevents accidental closing while a download is running
- Optional details/log panel for troubleshooting
- `Check / Update Downloader` button for bundled or PATH-based `yt-dlp`

## Run from source

Install Python 3.11+ on Windows, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

For development, the app can use `yt-dlp` and FFmpeg from your system `PATH`. For a packaged release, bundle the downloader tools in `vendor\` so the installer is self-contained.

## Bundle downloader tools

For the best user experience, place these files in `vendor\` before building:

```text
vendor\yt-dlp.exe
vendor\ffmpeg.exe
vendor\ffprobe.exe
```

You can download `yt-dlp.exe` with:

```powershell
.\scripts\download_tools.ps1
```

FFmpeg is strongly recommended because MP4 merging and MP3 conversion usually need it. Add `ffmpeg.exe` and `ffprobe.exe` manually from the FFmpeg build you choose to distribute.

## Build the app

From the repository root:

```powershell
.\scripts\build_windows.ps1
```

This creates:

```text
dist\SimpleYTDLP\SimpleYTDLP.exe
```

You can distribute the whole `dist\SimpleYTDLP\` folder directly if you do not need an installer.

## Build the installer

To build the app and the self-contained installer:

```powershell
.\scripts\build_windows.ps1 -BuildInstaller
```

This creates:

```text
installer\output\dist\SimpleYTDLP_Setup.exe
```

The installer copies the app to `C:\Program Files\SimpleYTDLP\` when possible, falls back to `%APPDATA%\SimpleYTDLP\` when Program Files is not writable, creates a Start Menu shortcut, and offers to launch the app when installation finishes.

See [BUILD_INSTALLER.md](BUILD_INSTALLER.md) for the full packaging checklist and troubleshooting notes.

## Project layout

```text
SimpleYTDLP/
|-- simple_ytdlp/
|   |-- app.py
|   `-- __main__.py
|-- assets/
|   `-- app.ico
|-- installer/
|   `-- SimpleYTDLP.iss
|-- scripts/
|   |-- build_installer.py
|   |-- build_windows.ps1
|   |-- clean.ps1
|   `-- download_tools.ps1
|-- vendor/
|   `-- .gitkeep
|-- run.py
|-- requirements.txt
|-- THIRD_PARTY_NOTICES.md
`-- README.md
```

`installer\SimpleYTDLP.iss` is kept only as a legacy Inno Setup script. The normal installer path is `.\scripts\build_windows.ps1 -BuildInstaller`.

## Release notes

If you distribute `yt-dlp.exe`, `ffmpeg.exe`, or `ffprobe.exe` with the app, include the required third-party licences and notices with the release. Start with [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Legal reminder

SimpleYTDLP is only a simplified interface for a downloader engine. It should only be used to download content that the user owns, has permission to download, or is legally allowed to save.
