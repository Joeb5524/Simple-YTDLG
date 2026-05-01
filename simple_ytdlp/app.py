"""
SimpleYTDLP - a lightweight, older-user-friendly GUI wrapper around yt-dlp.

The app intentionally hides most yt-dlp complexity. It supports:
- multi-link queues
- video/audio mode
- best/smaller quality choices
- default Downloads folder output
- progress bar and plain-English status messages
- history
- open file / open folder buttons
- basic dependency check/update

This is a GUI wrapper only. Users are responsible for downloading content they own
or have permission to save.
"""

from __future__ import annotations

import json
import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_NAME = "SimpleYTDLP"
APP_DISPLAY_NAME = "Simple Video Downloader"
APP_VERSION = "1.0.0"

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
PERCENT_RE = re.compile(r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%")
DESTINATION_RE = re.compile(r"Destination:\s+(.+)$")
MERGE_RE = re.compile(r"Merging formats into\s+\"(.+?)\"")
MOVE_RE = re.compile(r"Moving file\s+\"(.+?)\"\s+to\s+\"(.+?)\"")
AFTER_MOVE_FILE_RE = re.compile(r"^FINAL_FILE:(.+)$")


@dataclass
class DownloadJob:
    url: str
    mode: str
    quality: str
    status: str = "Waiting"
    file_path: str = ""


class AppPaths:
    """Centralises paths for settings, history and runtime resources."""

    def __init__(self) -> None:
        self.home = Path.home()
        self.downloads = self._downloads_folder()
        self.config_dir = self._config_folder()
        self.settings_file = self.config_dir / "settings.json"
        self.history_file = self.config_dir / "history.json"
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _downloads_folder(self) -> Path:
        # Works well for Windows and most desktop Linux/macOS setups.
        return self.home / "Downloads"

    def _config_folder(self) -> Path:
        if platform.system() == "Windows":
            base = os.environ.get("LOCALAPPDATA") or str(self.home / "AppData" / "Local")
            return Path(base) / APP_NAME
        if platform.system() == "Darwin":
            return self.home / "Library" / "Application Support" / APP_NAME
        return self.home / ".config" / APP_NAME


def resource_path(*parts: str) -> Path:
    """Returns a path that works from source, PyInstaller one-dir, and PyInstaller one-file."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidate = exe_dir.joinpath(*parts)
        if candidate.exists():
            return candidate
        bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        return bundle_dir.joinpath(*parts)
    return Path(__file__).resolve().parents[1].joinpath(*parts)


def hide_console_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    if platform.system() != "Windows":
        return None
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return startupinfo


class SimpleYTDLPApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.paths = AppPaths()
        self.settings = self.load_settings()
        self.message_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self.jobs: list[DownloadJob] = []
        self.worker: Optional[threading.Thread] = None
        self.current_process: Optional[subprocess.Popen[str]] = None
        self.cancel_requested = False
        self.current_file_path: Optional[Path] = None
        self.last_completed_file: Optional[Path] = None
        self.details_visible = False

        self.title(f"{APP_DISPLAY_NAME} {APP_VERSION}")
        self.configure_window_size()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_style()
        self.build_ui()
        self.after(100, self.process_queue)
        self.after(300, self.offer_clipboard_url)

    # ------------------------------------------------------------------
    # Settings and history
    # ------------------------------------------------------------------
    def load_settings(self) -> dict:
        default = {
            "save_dir": str(self.paths.downloads),
            "mode": "video",
            "quality": "best",
            "show_details": False,
        }
        try:
            if self.paths.settings_file.exists():
                loaded = json.loads(self.paths.settings_file.read_text(encoding="utf-8"))
                default.update({k: v for k, v in loaded.items() if k in default})
        except Exception:
            pass
        return default

    def save_settings(self) -> None:
        self.settings.update(
            {
                "save_dir": self.save_dir_var.get(),
                "mode": self.mode_var.get(),
                "quality": self.quality_var.get(),
                "show_details": self.details_visible,
            }
        )
        self.paths.settings_file.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def load_history(self) -> list[dict]:
        try:
            if self.paths.history_file.exists():
                data = json.loads(self.paths.history_file.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
        except Exception:
            pass
        return []

    def append_history(self, job: DownloadJob) -> None:
        history = self.load_history()
        history.insert(
            0,
            {
                "url": job.url,
                "mode": job.mode,
                "quality": job.quality,
                "file_path": job.file_path,
                "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )
        history = history[:100]
        self.paths.history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def configure_window_size(self) -> None:
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(950, max(760, screen_width - 80))
        height = min(720, max(540, screen_height - 120))
        self.minsize(760, 540)
        self.geometry(f"{width}x{height}")

    def setup_style(self) -> None:
        self.configure(bg="#f4f6f8")
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        base_font = ("Segoe UI", 13)
        heading_font = ("Segoe UI", 20, "bold")
        button_font = ("Segoe UI", 13, "bold")

        self.option_add("*Font", base_font)
        self.option_add("*TCombobox*Listbox.font", base_font)

        style.configure("TFrame", background="#f4f6f8")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("TLabel", background="#f4f6f8", foreground="#17212b", font=base_font)
        style.configure("Card.TLabel", background="#ffffff", foreground="#17212b", font=base_font)
        style.configure("Heading.TLabel", background="#f4f6f8", foreground="#0f172a", font=heading_font)
        style.configure("Subtle.TLabel", background="#f4f6f8", foreground="#475569", font=("Segoe UI", 11))
        style.configure("CardSubtle.TLabel", background="#ffffff", foreground="#475569", font=("Segoe UI", 11))
        style.configure("TButton", font=button_font, padding=(14, 10))
        style.configure("Primary.TButton", font=("Segoe UI", 15, "bold"), padding=(20, 14))
        style.configure("Danger.TButton", font=button_font, padding=(14, 10))
        style.configure("TRadiobutton", background="#ffffff", foreground="#17212b", font=base_font, padding=8)
        style.configure("Horizontal.TProgressbar", thickness=28)
        style.configure("Treeview", font=("Segoe UI", 11), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"))

    def build_ui(self) -> None:
        self.ui_canvas = tk.Canvas(self, bg="#f4f6f8", highlightthickness=0)
        self.ui_scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.ui_canvas.yview)
        self.ui_canvas.configure(yscrollcommand=self.ui_scrollbar.set)
        self.ui_scrollbar.pack(side="right", fill="y")
        self.ui_canvas.pack(side="left", fill="both", expand=True)

        outer = ttk.Frame(self.ui_canvas, padding=20)
        self.ui_window = self.ui_canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>", self.sync_scroll_region)
        self.ui_canvas.bind("<Configure>", self.sync_scroll_width)

        ttk.Label(outer, text=APP_DISPLAY_NAME, style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Paste one or more video links, choose video or audio, then press Start Download.",
            style="Subtle.TLabel",
        ).pack(anchor="w", pady=(2, 16))

        main = ttk.Frame(outer)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(2, weight=1)

        input_card = ttk.Frame(main, style="Card.TFrame", padding=16)
        input_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        input_card.columnconfigure(0, weight=1)

        ttk.Label(input_card, text="Video links", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(input_card, text="One link per line is best.", style="CardSubtle.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 8)
        )

        self.url_text = tk.Text(input_card, height=7, wrap="word", font=("Segoe UI", 13), undo=True)
        self.url_text.grid(row=2, column=0, sticky="nsew")
        self.url_text.configure(borderwidth=1, relief="solid")
        input_card.rowconfigure(2, weight=1)

        url_buttons = ttk.Frame(input_card, style="Card.TFrame")
        url_buttons.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(url_buttons, text="Paste from Clipboard", command=self.paste_clipboard).pack(side="left")
        ttk.Button(url_buttons, text="Clear Links", command=lambda: self.url_text.delete("1.0", "end")).pack(
            side="left", padx=(10, 0)
        )

        options_card = ttk.Frame(main, style="Card.TFrame", padding=16)
        options_card.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        options_card.columnconfigure(0, weight=1)

        self.mode_var = tk.StringVar(value=self.settings.get("mode", "video"))
        self.quality_var = tk.StringVar(value=self.settings.get("quality", "best"))
        self.save_dir_var = tk.StringVar(value=self.settings.get("save_dir", str(self.paths.downloads)))

        ttk.Label(options_card, text="Download type", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(options_card, text="Video file (MP4)", variable=self.mode_var, value="video").grid(
            row=1, column=0, sticky="w"
        )
        ttk.Radiobutton(options_card, text="Audio file (MP3)", variable=self.mode_var, value="audio").grid(
            row=2, column=0, sticky="w"
        )

        ttk.Label(options_card, text="Quality", style="Card.TLabel").grid(row=3, column=0, sticky="w", pady=(14, 0))
        ttk.Radiobutton(options_card, text="Best quality", variable=self.quality_var, value="best").grid(
            row=4, column=0, sticky="w"
        )
        ttk.Radiobutton(options_card, text="Smaller file", variable=self.quality_var, value="small").grid(
            row=5, column=0, sticky="w"
        )

        ttk.Label(options_card, text="Save location", style="Card.TLabel").grid(row=6, column=0, sticky="w", pady=(14, 4))
        save_row = ttk.Frame(options_card, style="Card.TFrame")
        save_row.grid(row=7, column=0, sticky="ew")
        save_row.columnconfigure(0, weight=1)
        self.save_entry = ttk.Entry(save_row, textvariable=self.save_dir_var, font=("Segoe UI", 11))
        self.save_entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(save_row, text="Browse", command=self.choose_save_folder).grid(row=0, column=1, padx=(8, 0))

        primary_actions = ttk.Frame(options_card, style="Card.TFrame")
        primary_actions.grid(row=8, column=0, sticky="ew", pady=(18, 0))
        primary_actions.columnconfigure(0, weight=1)
        self.start_button = ttk.Button(
            primary_actions, text="Start Download", style="Primary.TButton", command=self.start_downloads
        )
        self.start_button.grid(row=0, column=0, sticky="ew")
        self.cancel_button = ttk.Button(primary_actions, text="Cancel", command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        actions_card = ttk.Frame(main, style="Card.TFrame", padding=16)
        actions_card.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        actions_card.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value=f"Ready. Files will save to {self.save_dir_var.get()}.")
        self.progress_var = tk.DoubleVar(value=0)

        self.progress = ttk.Progressbar(
            actions_card, orient="horizontal", mode="determinate", maximum=100, variable=self.progress_var
        )
        self.progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(actions_card, textvariable=self.status_var, style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 10)
        )

        secondary_actions = ttk.Frame(actions_card, style="Card.TFrame")
        secondary_actions.grid(row=2, column=0, sticky="w")
        ttk.Button(secondary_actions, text="Open Downloads Folder", command=self.open_save_folder).grid(
            row=0, column=0, sticky="w"
        )
        self.open_file_button = ttk.Button(
            secondary_actions, text="Open Last File", command=self.open_last_file, state="disabled"
        )
        self.open_file_button.grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Button(secondary_actions, text="Check / Update Downloader", command=self.check_update_downloader).grid(
            row=1, column=0, sticky="w", pady=(10, 0)
        )
        self.details_button = ttk.Button(secondary_actions, text="Show Details", command=self.toggle_details)
        self.details_button.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(10, 0))

        queue_card = ttk.Frame(main, style="Card.TFrame", padding=16)
        queue_card.grid(row=2, column=0, sticky="nsew", padx=(0, 12))
        queue_card.rowconfigure(1, weight=1)
        queue_card.columnconfigure(0, weight=1)
        ttk.Label(queue_card, text="Download queue", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.queue_tree = ttk.Treeview(queue_card, columns=("status", "type", "quality", "file"), show="tree headings")
        self.queue_tree.heading("#0", text="Link")
        self.queue_tree.heading("status", text="Status")
        self.queue_tree.heading("type", text="Type")
        self.queue_tree.heading("quality", text="Quality")
        self.queue_tree.heading("file", text="File")
        self.queue_tree.column("#0", width=260, stretch=True)
        self.queue_tree.column("status", width=120)
        self.queue_tree.column("type", width=80)
        self.queue_tree.column("quality", width=90)
        self.queue_tree.column("file", width=240, stretch=True)
        self.queue_tree.grid(row=1, column=0, sticky="nsew")

        history_card = ttk.Frame(main, style="Card.TFrame", padding=16)
        history_card.grid(row=2, column=1, sticky="nsew")
        history_card.rowconfigure(1, weight=1)
        history_card.columnconfigure(0, weight=1)
        ttk.Label(history_card, text="Recent downloads", style="Card.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.history_list = tk.Listbox(history_card, font=("Segoe UI", 11), height=8)
        self.history_list.grid(row=1, column=0, sticky="nsew")
        history_buttons = ttk.Frame(history_card, style="Card.TFrame")
        history_buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(history_buttons, text="Open Selected", command=self.open_selected_history).pack(side="left")
        ttk.Button(history_buttons, text="Refresh", command=self.refresh_history).pack(side="left", padx=(10, 0))
        self.refresh_history()

        self.details_frame = ttk.Frame(outer, padding=(0, 12, 0, 0))
        self.log_text = tk.Text(self.details_frame, height=8, wrap="word", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)
        if self.settings.get("show_details", False):
            self.toggle_details()

    def sync_scroll_region(self, _event: tk.Event) -> None:
        self.ui_canvas.configure(scrollregion=self.ui_canvas.bbox("all"))

    def sync_scroll_width(self, event: tk.Event) -> None:
        self.ui_canvas.itemconfigure(self.ui_window, width=event.width)

    def offer_clipboard_url(self) -> None:
        try:
            text = self.clipboard_get().strip()
        except Exception:
            return
        if URL_RE.search(text) and not self.url_text.get("1.0", "end").strip():
            use_link = messagebox.askyesno(
                APP_DISPLAY_NAME,
                "A video link appears to be copied already.\n\nWould you like to paste it into the downloader?",
            )
            if use_link:
                self.url_text.insert("1.0", text)

    def paste_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
        except Exception:
            messagebox.showwarning(APP_DISPLAY_NAME, "There is nothing readable on the clipboard.")
            return
        if self.url_text.get("1.0", "end").strip():
            self.url_text.insert("end", "\n" + text.strip())
        else:
            self.url_text.insert("1.0", text.strip())

    def choose_save_folder(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.save_dir_var.get() or str(self.paths.downloads))
        if chosen:
            self.save_dir_var.set(chosen)
            self.status_var.set(f"Files will save to {chosen}.")
            self.save_settings()

    def toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.details_frame.pack(fill="both", expand=False)
        else:
            self.details_frame.pack_forget()
        self.details_button.configure(text="Hide Details" if self.details_visible else "Show Details")
        self.save_settings()

    def write_log(self, text: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text.rstrip() + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def refresh_history(self) -> None:
        self.history_entries = self.load_history()
        self.history_list.delete(0, "end")
        for entry in self.history_entries[:20]:
            file_path = entry.get("file_path") or entry.get("url", "")
            label = Path(file_path).name if file_path else entry.get("url", "Unknown")
            self.history_list.insert("end", label)

    # ------------------------------------------------------------------
    # Downloader command construction
    # ------------------------------------------------------------------
    def find_yt_dlp(self) -> Optional[Path | str]:
        bundled = resource_path("vendor", "yt-dlp.exe")
        if bundled.exists():
            return bundled
        bundled_no_ext = resource_path("vendor", "yt-dlp")
        if bundled_no_ext.exists():
            return bundled_no_ext
        path_hit = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
        return path_hit

    def find_ffmpeg_dir(self) -> Optional[Path]:
        bundled_ffmpeg = resource_path("vendor", "ffmpeg.exe")
        bundled_ffprobe = resource_path("vendor", "ffprobe.exe")
        if bundled_ffmpeg.exists() and bundled_ffprobe.exists():
            return bundled_ffmpeg.parent
        path_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        path_ffprobe = shutil.which("ffprobe") or shutil.which("ffprobe.exe")
        if path_ffmpeg and path_ffprobe:
            return Path(path_ffmpeg).parent
        return None

    def build_command(self, job: DownloadJob, save_dir: Path) -> list[str]:
        yt_dlp = self.find_yt_dlp()
        if yt_dlp is None:
            raise FileNotFoundError("yt-dlp was not found. Place yt-dlp.exe in vendor/ or install it in PATH.")

        output_template = str(save_dir / "%(title).150B [%(id)s].%(ext)s")
        command = [
            str(yt_dlp),
            "--newline",
            "--no-playlist",
            "--windows-filenames",
            "--restrict-filenames",
            "--progress",
            "--print",
            "after_move:FINAL_FILE:%(filepath)s",
            "-o",
            output_template,
        ]

        ffmpeg_dir = self.find_ffmpeg_dir()
        if ffmpeg_dir:
            command.extend(["--ffmpeg-location", str(ffmpeg_dir)])

        if job.mode == "audio":
            command.extend(["-x", "--audio-format", "mp3"])
            command.extend(["--audio-quality", "0" if job.quality == "best" else "5"])
        else:
            if job.quality == "small":
                command.extend(
                    [
                        "-f",
                        "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]/best",
                    ]
                )
            else:
                command.extend(
                    [
                        "-f",
                        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestvideo+bestaudio/best",
                    ]
                )
            command.extend(["--merge-output-format", "mp4"])

        command.append(job.url)
        return command

    # ------------------------------------------------------------------
    # Download handling
    # ------------------------------------------------------------------
    def extract_urls(self) -> list[str]:
        raw = self.url_text.get("1.0", "end")
        urls = []
        for line in raw.splitlines():
            found = URL_RE.findall(line)
            urls.extend(found)
        return list(dict.fromkeys(urls))

    def start_downloads(self) -> None:
        urls = self.extract_urls()
        if not urls:
            messagebox.showwarning(APP_DISPLAY_NAME, "Please paste at least one video link first.")
            return

        save_dir = Path(self.save_dir_var.get()).expanduser()
        try:
            save_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror(APP_DISPLAY_NAME, f"Could not use this save folder:\n\n{save_dir}\n\n{exc}")
            return

        yt_dlp = self.find_yt_dlp()
        if yt_dlp is None:
            messagebox.showerror(
                APP_DISPLAY_NAME,
                "The downloader engine was not found.\n\nPlace yt-dlp.exe in the vendor folder before building, or install yt-dlp so it is available in PATH.",
            )
            return

        if self.find_ffmpeg_dir() is None:
            proceed = messagebox.askyesno(
                APP_DISPLAY_NAME,
                "FFmpeg was not found.\n\nVideo merging and MP3 conversion may fail without it. Continue anyway?",
            )
            if not proceed:
                return

        self.save_settings()
        self.jobs = [DownloadJob(url=url, mode=self.mode_var.get(), quality=self.quality_var.get()) for url in urls]
        self.populate_queue()
        self.set_running(True)
        self.cancel_requested = False
        self.progress_var.set(0)
        self.status_var.set(f"Starting {len(self.jobs)} download(s). Files will save to {save_dir}.")

        self.worker = threading.Thread(target=self.download_worker, args=(save_dir,), daemon=True)
        self.worker.start()

    def populate_queue(self) -> None:
        for item in self.queue_tree.get_children():
            self.queue_tree.delete(item)
        for index, job in enumerate(self.jobs):
            self.queue_tree.insert(
                "",
                "end",
                iid=str(index),
                text=self.shorten(job.url, 45),
                values=(job.status, job.mode.title(), job.quality.title(), ""),
            )

    def update_queue_row(self, index: int) -> None:
        job = self.jobs[index]
        file_label = Path(job.file_path).name if job.file_path else ""
        self.queue_tree.item(
            str(index),
            values=(job.status, job.mode.title(), job.quality.title(), file_label),
        )

    def set_running(self, running: bool) -> None:
        self.start_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")

    def download_worker(self, save_dir: Path) -> None:
        completed = 0
        for index, job in enumerate(self.jobs):
            if self.cancel_requested:
                job.status = "Cancelled"
                self.message_queue.put(("queue", index))
                continue

            self.current_file_path = None
            job.status = "Downloading"
            self.message_queue.put(("queue", index))
            self.message_queue.put(("status", f"Downloading {index + 1} of {len(self.jobs)}..."))
            self.message_queue.put(("progress", 0.0))

            try:
                command = self.build_command(job, save_dir)
                self.message_queue.put(("log", "> " + self.safe_command_for_log(command)))
                self.current_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    startupinfo=hide_console_startupinfo(),
                    bufsize=1,
                )

                assert self.current_process.stdout is not None
                for line in self.current_process.stdout:
                    self.handle_process_output(line, index)
                    if self.cancel_requested and self.current_process.poll() is None:
                        self.current_process.terminate()

                return_code = self.current_process.wait()
                self.current_process = None

                if self.cancel_requested:
                    job.status = "Cancelled"
                elif return_code == 0:
                    if self.current_file_path:
                        job.file_path = str(self.current_file_path)
                    job.status = "Complete"
                    completed += 1
                    self.append_history(job)
                    self.message_queue.put(("history", None))
                    if job.file_path:
                        self.last_completed_file = Path(job.file_path)
                        self.message_queue.put(("last_file", str(self.last_completed_file)))
                else:
                    job.status = "Failed"

                self.message_queue.put(("queue", index))
            except Exception as exc:
                job.status = "Failed"
                self.message_queue.put(("queue", index))
                self.message_queue.put(("log", f"ERROR: {exc}"))

        if self.cancel_requested:
            self.message_queue.put(("done", "Downloads cancelled."))
        else:
            self.message_queue.put(
                (
                    "done",
                    f"Download complete. {completed} of {len(self.jobs)} file(s) saved to {save_dir}.",
                )
            )

    def handle_process_output(self, line: str, index: int) -> None:
        line = line.rstrip("\n")
        self.message_queue.put(("log", line))

        percent_match = PERCENT_RE.search(line)
        if percent_match:
            try:
                self.message_queue.put(("progress", float(percent_match.group(1))))
            except ValueError:
                pass

        final_match = AFTER_MOVE_FILE_RE.match(line.strip())
        if final_match:
            self.current_file_path = Path(final_match.group(1).strip())
            self.jobs[index].file_path = str(self.current_file_path)
            self.message_queue.put(("queue", index))
            return

        merge_match = MERGE_RE.search(line)
        if merge_match:
            self.current_file_path = Path(merge_match.group(1).strip())
            self.jobs[index].file_path = str(self.current_file_path)
            self.message_queue.put(("queue", index))
            return

        move_match = MOVE_RE.search(line)
        if move_match:
            self.current_file_path = Path(move_match.group(2).strip())
            self.jobs[index].file_path = str(self.current_file_path)
            self.message_queue.put(("queue", index))
            return

        destination_match = DESTINATION_RE.search(line)
        if destination_match:
            self.current_file_path = Path(destination_match.group(1).strip().strip('"'))
            self.jobs[index].file_path = str(self.current_file_path)
            self.message_queue.put(("queue", index))

    def process_queue(self) -> None:
        try:
            while True:
                kind, payload = self.message_queue.get_nowait()
                if kind == "log":
                    self.write_log(str(payload))
                elif kind == "status":
                    self.status_var.set(str(payload))
                elif kind == "progress":
                    self.progress_var.set(float(payload))
                elif kind == "queue":
                    self.update_queue_row(int(payload))
                elif kind == "history":
                    self.refresh_history()
                elif kind == "last_file":
                    self.open_file_button.configure(state="normal")
                elif kind == "info":
                    messagebox.showinfo(APP_DISPLAY_NAME, str(payload))
                elif kind == "done":
                    self.set_running(False)
                    self.progress_var.set(100 if not self.cancel_requested else 0)
                    self.status_var.set(str(payload))
                    messagebox.showinfo(APP_DISPLAY_NAME, str(payload))
        except queue.Empty:
            pass
        self.after(100, self.process_queue)

    def cancel_download(self) -> None:
        if not self.worker or not self.worker.is_alive():
            return
        if not messagebox.askyesno(APP_DISPLAY_NAME, "A download is still running. Do you want to cancel it?"):
            return
        self.cancel_requested = True
        self.status_var.set("Cancelling download...")
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Buttons and helpers
    # ------------------------------------------------------------------
    def check_update_downloader(self) -> None:
        yt_dlp = self.find_yt_dlp()
        if yt_dlp is None:
            messagebox.showerror(
                APP_DISPLAY_NAME,
                "yt-dlp was not found. Put yt-dlp.exe in the vendor folder or install yt-dlp in PATH.",
            )
            return

        def update() -> None:
            self.message_queue.put(("log", f"Checking downloader: {yt_dlp}"))
            try:
                result = subprocess.run(
                    [str(yt_dlp), "-U"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    startupinfo=hide_console_startupinfo(),
                    timeout=120,
                )
                output = (result.stdout or "") + (result.stderr or "")
                self.message_queue.put(("log", output.strip() or "No updater output."))
                if result.returncode == 0:
                    self.message_queue.put(("status", "Downloader check complete."))
                    self.message_queue.put(("info", "Downloader check complete."))
                else:
                    self.message_queue.put(("status", "Downloader update failed. See Details."))
            except Exception as exc:
                self.message_queue.put(("log", f"Updater error: {exc}"))
                self.message_queue.put(("status", "Downloader update failed. See Details."))

        threading.Thread(target=update, daemon=True).start()

    def open_save_folder(self) -> None:
        self.open_path(Path(self.save_dir_var.get()).expanduser())

    def open_last_file(self) -> None:
        if self.last_completed_file and self.last_completed_file.exists():
            self.open_path(self.last_completed_file)
        else:
            messagebox.showwarning(APP_DISPLAY_NAME, "No completed file is available yet.")

    def open_selected_history(self) -> None:
        selection = self.history_list.curselection()
        if not selection:
            messagebox.showwarning(APP_DISPLAY_NAME, "Please select a recent download first.")
            return
        entry = self.history_entries[selection[0]]
        file_path = Path(entry.get("file_path", ""))
        if file_path.exists():
            self.open_path(file_path)
        else:
            messagebox.showwarning(APP_DISPLAY_NAME, "That file could not be found. It may have been moved or deleted.")

    def open_path(self, path: Path) -> None:
        try:
            if platform.system() == "Windows":
                os.startfile(path)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            webbrowser.open(path.as_uri())

    def on_close(self) -> None:
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno(
                APP_DISPLAY_NAME,
                "A download is still running. Do you want to cancel it and close the app?",
            ):
                return
            self.cancel_requested = True
            if self.current_process and self.current_process.poll() is None:
                try:
                    self.current_process.terminate()
                except Exception:
                    pass
        self.save_settings()
        self.destroy()

    @staticmethod
    def shorten(text: str, max_len: int) -> str:
        return text if len(text) <= max_len else text[: max_len - 3] + "..."

    @staticmethod
    def safe_command_for_log(command: Iterable[str]) -> str:
        return " ".join(f'"{part}"' if " " in part else part for part in command)


def main() -> None:
    app = SimpleYTDLPApp()
    app.mainloop()


if __name__ == "__main__":
    main()
