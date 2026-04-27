#!/usr/bin/env python3
"""
Simple self-contained installer for SimpleYTDLP.
No Inno Setup required - uses PyInstaller to bundle the installer.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from tkinter import Tk, messagebox


def get_install_path():
    """Get the installation directory."""
    program_files = Path(os.environ.get("ProgramFiles", "C:\\Program Files"))
    install_path = program_files / "SimpleYTDLP"
    
    # Try to verify we can write to Program Files
    try:
        test_file = install_path.parent / ".write_test"
        test_file.touch()
        test_file.unlink()
        return install_path
    except (PermissionError, OSError):
        # Fall back to AppData if Program Files is protected
        app_data = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return app_data / "SimpleYTDLP"


def create_shortcuts(app_path):
    """Create Start Menu and Desktop shortcuts."""
    try:
        start_menu = Path(os.environ.get("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
        shortcuts_dir = start_menu / "SimpleYTDLP"
        shortcuts_dir.mkdir(parents=True, exist_ok=True)
        
        exe_path = app_path / "SimpleYTDLP.exe"
        icon_path = app_path / "assets" / "app.ico"
        icon_location = icon_path if icon_path.exists() else exe_path
        
        # Use PowerShell to create shortcuts
        shortcut_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$startMenuLink = $WshShell.CreateShortcut('{shortcuts_dir}\\Simple Video Downloader.lnk')
$startMenuLink.TargetPath = '{exe_path}'
$startMenuLink.WorkingDirectory = '{app_path}'
$startMenuLink.IconLocation = '{icon_location}'
$startMenuLink.Save()
"""
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", shortcut_script],
            capture_output=True,
            timeout=5
        )
    except Exception as e:
        print(f"Warning: Could not create shortcuts: {e}")


def main():
    root = Tk()
    root.withdraw()
    
    try:
        # Get target installation path
        install_path = get_install_path()
        
        # Get app files from PyInstaller bundle
        if hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            app_files = Path(sys._MEIPASS) / "dist" / "SimpleYTDLP"
        else:
            # Running as script (for testing)
            repo_root = Path(__file__).parent.parent
            app_files = repo_root / "dist" / "SimpleYTDLP"
        
        if not app_files.exists():
            raise FileNotFoundError(f"Application files not found at {app_files}")
        
        # Show installation in progress
        messagebox.showinfo("Installing", f"Installing to {install_path}...", parent=root)
        
        # Remove existing installation
        if install_path.exists():
            shutil.rmtree(install_path)
        
        # Copy application
        shutil.copytree(app_files, install_path)
        
        # Create shortcuts
        create_shortcuts(install_path)
        
        # Success message
        if messagebox.askyesno(
            "Installation Complete",
            f"SimpleYTDLP installed successfully!\n\n"
            f"Location: {install_path}\n\n"
            f"Launch it now?"
        ):
            subprocess.Popen(
                str(install_path / "SimpleYTDLP.exe"),
                cwd=str(install_path)
            )
        
        root.destroy()
    
    except Exception as e:
        messagebox.showerror("Installation Error", f"Failed to install:\n\n{e}")
        root.destroy()
        sys.exit(1)


if __name__ == "__main__":
    main()
