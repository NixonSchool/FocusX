import os
import time
import psutil
import threading
import keyboard
from datetime import datetime
import tkinter as tk
from tkinter import messagebox

LOG_PATH = os.path.join(os.path.dirname(__file__), "FocusX.log")

class ProcessBlocker:
    """Blocks Task Manager, Registry Editor, Command Prompt, and other bypass tools."""
    
    def __init__(self):
        self.blocked_processes = ["Taskmgr.exe", "cmd.exe", "regedit.exe", "ProcessHacker.exe"]
        self.running = True
        self.thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.thread.start()

    def log_event(self, message):
        """Logs security events to FocusX.log."""
        with open(LOG_PATH, "a") as log_file:
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            log_file.write(f"{timestamp} {message}\n")

    def monitor_processes(self):
        """Continuously checks for and terminates blacklisted processes."""
        while self.running:
            self.check_tampering()  # 🔥 Detect renamed tools
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] in self.blocked_processes:
                    try:
                        proc.kill()
                        self.log_event(f"Blocked {proc.info['name']}")
                        print(f"Blocked {proc.info['name']}")
                    except Exception as e:
                        self.log_event(f"Failed to block {proc.info['name']}: {e}")
            time.sleep(1)  # Check every second

    def check_tampering(self):
        """Detects renamed versions of blocked programs."""
        found_files = []
        for proc in psutil.process_iter(attrs=['pid', 'exe']):
            try:
                exe_path = proc.info['exe']
                if exe_path and any(tool.lower() in exe_path.lower() for tool in self.blocked_processes):
                    found_files.append(exe_path)
            except:
                pass  # Ignore permission errors

        if found_files:
            self.running = False  # 🔥 Pause monitoring
            self.log_event(f"TAMPERING DETECTED: {found_files}")
            self.auto_close_tampering_tools(found_files)

    def auto_close_tampering_tools(self, found_files):
        """Automatically closes detected tampering tools."""
        for file in found_files:
            try:
                proc = next((p for p in psutil.process_iter(attrs=['pid', 'exe']) if p.info['exe'] == file), None)
                if proc:
                    proc.terminate()
                    self.log_event(f"Closed tampering tool: {file}")
                    print(f"🔥 Closed tampering tool: {file}")
            except Exception as e:
                self.log_event(f"Failed to close {file}: {e}")

        messagebox.showwarning(
            "Tampering Detected",
            "🚫 You CANNOT bypass FocusX! We shut down your tools. Be serious 🤡💯"
        )

class HotkeyBlocker:
    """Blocks escape shortcuts like Alt+Tab, Win+D, Ctrl+Shift+Esc, etc."""
    
    def __init__(self):
        self.blocked_keys = ["alt+tab", "win+tab", "ctrl+shift+esc", "alt+f4", "win+d"]
        self.running = True
        self.thread = threading.Thread(target=self.block_hotkeys, daemon=True)
        self.thread.start()

    def block_hotkeys(self):
        """Registers hotkey blocking."""
        while self.running:
            try:
                for hotkey in self.blocked_keys:
                    keyboard.block_key(hotkey)
            except Exception as e:
                print(f"Error blocking hotkeys: {e}")
            time.sleep(0.1)

    def stop(self):
        """Stops the hotkey blocking."""
        self.running = False
        for hotkey in self.blocked_keys:
            keyboard.unblock_key(hotkey)
