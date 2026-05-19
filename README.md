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
- Dark mode toggle
- App update check that opens the latest GitHub Release
- Optional details/log panel for troubleshooting
- `Check / Update Downloader` button for the bundled downloader

## Install or update the GUI

Install Python 3.11 or newer on Windows, then run these two scripts from the repository root:

```powershell
.\scripts\get_dependencies.ps1
.\scripts\install_gui.ps1
```

`get_dependencies.ps1` prepares the Python build environment, downloads `yt-dlp.exe`, downloads FFmpeg and FFprobe, and makes sure Inno Setup 6 is available.

`install_gui.ps1` builds the GUI setup file and launches it. The setup file is created here:

```text
installer\output\SimpleYTDLP_Setup_1.1.exe
```

The installer supports normal Windows install, upgrade, and uninstall behavior, including Add/Remove Programs, Start Menu shortcuts, an optional desktop shortcut, and launching the app after setup.

See [BUILD_INSTALLER.md](BUILD_INSTALLER.md) for the packaging checklist and troubleshooting notes for the two-script flow.

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
|   |-- get_dependencies.ps1
|   `-- install_gui.ps1
|-- vendor/
|   `-- .gitkeep
|-- run.py
|-- requirements.txt
|-- THIRD_PARTY_NOTICES.md
`-- README.md
```

`installer\SimpleYTDLP.iss` is the installer definition used by `.\scripts\install_gui.ps1`.

## Release notes

If you distribute `yt-dlp.exe`, `ffmpeg.exe`, or `ffprobe.exe` with the app, include the required third-party licences and notices with the release. Start with [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Legal reminder

SimpleYTDLP is only a simplified interface for a downloader engine. It should only be used to download content that the user owns, has permission to download, or is legally allowed to save.
