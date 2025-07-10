import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import subprocess
import winreg
from datetime import datetime
import os
import random
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import ntplib
import pytz
import socket
from tzlocal import get_localzone
from screeninfo import get_monitors

class ScreenBlocker:
    def __init__(self, root):
        self.overlays = []
        self.root = root

    def detect_screens(self):
        """Detects all monitors and returns their positions & sizes."""
        return get_monitors()

    def create_overlay(self, monitor):
        """Creates a fullscreen overlay for a given monitor."""
        try:
            overlay = tk.Toplevel(self.root)
            overlay.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
            overlay.configure(bg="black")
            overlay.attributes("-fullscreen", True)
            overlay.attributes("-topmost", True)
            overlay.overrideredirect(True)
            overlay.protocol("WM_DELETE_WINDOW", lambda: None)
            overlay.update_idletasks()

            message = tk.Label(overlay, text="🔒 FOCUS BREAK - STEP AWAY",
                                       font=("Arial", 24, 'bold'), fg="white", bg="black")
            message.pack(expand=True)
            return overlay # Return the created overlay

        except Exception as e:
            print(f"Failed to create overlay on {monitor}: {e}")
            return None

    def block_all_screens(self):
        """Blocks all screens by creating overlays, ensuring no duplicates."""
        # First, remove any existing overlays to prevent duplicates
        self.remove_overlays()

        monitors = self.detect_screens()
        if not monitors:
            print("No monitors detected!")
            return

        created_overlays = [] # Temporarily store new overlays
        for monitor in monitors:
            overlay = self.create_overlay(monitor)
            if overlay:
                created_overlays.append(overlay)

        if not created_overlays:
            print("❌ Overlay creation failed on all monitors.")
            return

        self.overlays = created_overlays # Update self.overlays only after successful creation


    def remove_overlays(self):
        """Removes all screen blocking overlays and clears the list."""
        for overlay in self.overlays:
            try:
                overlay.destroy()
            except Exception as e:
                print(f"Error destroying overlay: {e}")
        self.overlays = [] # Clear the overlays list after destroying them

class PomodoroBlocker:
    def __init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Focus Time")

        # Window positioning - (rest of your positioning code remains the same)
        window_width = 400
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.attributes('-topmost', True)


        # Colors, Timer Settings, Time Sync Settings, Break Messages - (rest of your settings remain the same)
        self.colors = {
            'bg': '#ffffff',
            'primary': '#1a73e8',
            'warning': '#ea4335',
            'text': '#202124'
        }
        self.root.configure(bg=self.colors['bg'])
        self.work_duration = 50 * 60  # 50 minutes
        self.rest_duration = 7 * 60  # 7 minutes
        self.is_running = False
        self.is_work_session = True
        self.ntp_servers = [
            'pool.ntp.org',
            'time.google.com',
            'time.windows.com',
            'time.apple.com'
        ]
        self.time_offset = 0
        self.local_timezone = get_localzone()
        self.break_activities = [
            "Take time to read and reflect",
            "Step away from the screen and rest your eyes",
            "Go for a short walk",
            "Do some light stretching",
            "Practice deep breathing",
            "Hydrate yourself",
            "Tidy up your workspace"
        ]

        self.setup_ui()

        self.blocking = False
        self.mouse_listener = None
        self.keyboard_listener = None

        # Audio control - (audio control remains the same)
        self.audio = None
        self.init_audio_control()

        # Initialize ScreenBlocker - Pass self.root
        self.screen_blocker = ScreenBlocker(self.root) # Initialize ScreenBlocker

        # Start time monitoring - (time monitoring remains the same)
        self.sync_time()
        self.start_time_monitoring()

    # Time sync, accurate time, night time check - (time functions remain the same)
    def sync_time(self):
        for server in self.ntp_servers:
            try:
                ntp_client = ntplib.NTPClient()
                response = ntp_client.request(server, timeout=5)
                self.time_offset = response.offset
                print(f"Time synchronized with {server}, offset: {self.time_offset:.2f} seconds")
                return
            except (ntplib.NTPException, socket.gaierror, socket.timeout):
                continue
        print("Warning: Could not sync with any time server, using system time")

    def get_accurate_time(self):
        current_time = datetime.now(self.local_timezone)
        if self.time_offset:
            current_time = current_time.fromtimestamp(time.time() + self.time_offset)
        return current_time

    def is_night_time(self):
        current_time = self.get_accurate_time()
        return 0 <= current_time.hour < 6

    # Night overlay functions - (night overlay functions remain mostly the same, but use ScreenBlocker)
    def create_night_overlay(self):
        """Create overlay for night-time blocking on all screens using ScreenBlocker"""
        if self.screen_blocker.overlays: # Check if overlays already exist using ScreenBlocker's list
            return
        self.screen_blocker.block_all_screens() # Use ScreenBlocker to block screens
        night_overlays = self.screen_blocker.overlays # Get the overlays created by ScreenBlocker

        for night_overlay in night_overlays: # Iterate through the overlays created by ScreenBlocker

            message = tk.Label(
                night_overlay,
                text="It's late night hours (12 AM - 6 AM).\nPlease get some rest.",
                font=('Arial', 24),
                fg='white',
                bg='black',
                justify='center'
            )
            message.pack(expand=True)

            time_label = tk.Label(
                night_overlay,
                font=('Arial', 18),
                fg='white',
                bg='black'
            )
            time_label.pack(pady=20)

            def update_time(overlay_time_label):  # Need to pass time_label to update function
                if night_overlay.winfo_exists(): # Check if overlay still exists
                    current_time = self.get_accurate_time()
                    overlay_time_label.config(text=f"Current time: {current_time.strftime('%I:%M:%S %p')}")
                    night_overlay.after(1000, lambda: update_time(overlay_time_label)) # Use lambda for argument

            update_time(time_label)


        self.block_input()

    def remove_night_overlay(self):
        """Remove night-time blocking overlay from all screens using ScreenBlocker"""
        self.screen_blocker.remove_overlays() # Use ScreenBlocker to remove overlays
        self.unblock_input()

    def start_time_monitoring(self): # No changes needed here - remains the same
        """Start monitoring time for night-time blocking"""
        def monitor_time():
            while True:
                if self.is_night_time():
                    if not self.screen_blocker.overlays:  # Check ScreenBlocker's overlays
                        self.root.after(0, self.create_night_overlay)
                else:
                    if self.screen_blocker.overlays: # Check ScreenBlocker's overlays
                        self.root.after(0, self.remove_night_overlay)
                time.sleep(30)  # Check every 30 seconds

        threading.Thread(target=monitor_time, daemon=True).start()

        def periodic_sync():
            while True:
                time.sleep(3600)  # Sync every hour
                self.sync_time()

        threading.Thread(target=periodic_sync, daemon=True).start()

    # Audio control functions - (audio control functions remain the same)
    def init_audio_control(self):
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.audio = cast(interface, POINTER(IAudioEndpointVolume))
        except:
            print("Could not initialize audio control")

    def mute_audio(self):
        if self.audio:
            try:
                self.audio.SetMute(1, None)
            except:
                print("Could not mute audio")

    def unmute_audio(self):
        if self.audio:
            try:
                self.audio.SetMute(0, None)
            except:
                print("Could not unmute audio")

    def __init__(self):
        pygame.mixer.init()  # Initialize sound player
        self.sound_path = os.path.join(os.path.dirname(__file__), "FocusX.mp3")  # Get file path
        # Other existing code...

    def play_sound(self):
        """Play break alert sound"""
        try:
            pygame.mixer.music.load(self.sound_path)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error playing sound: {e}")

    def _run_timer(self):
        while self.is_running:
            if self.is_work_session:
                self.countdown(self.work_duration)
            else:
                self.play_sound()  # 🔥 Play sound at start of break
                self.screen_blocker.block_all_screens()
                self.countdown(self.rest_duration)
                self.screen_blocker.remove_overlays()
            if self.is_running:
                self.is_work_session = not self.is_work_session

    def setup_ui(self):
    main_frame = tk.Frame(self.root)
    main_frame.pack(expand=True, fill='both', padx=20, pady=20)

    self.time_var = tk.StringVar(value=f"{self.work_duration // 60}:00")
    self.time_label = tk.Label(main_frame, textvariable=self.time_var, font=('Helvetica', 48, 'bold'))
    self.time_label.pack(pady=20)

    self.start_button = tk.Button(main_frame, text="Start", command=self.start_timer)
    self.start_button.pack(pady=5)

    self.stop_button = tk.Button(main_frame, text="Stop", command=self.stop_timer)
    self.stop_button.pack(pady=5)

    # 🔥 New settings button
    self.settings_button = tk.Button(main_frame, text="Settings", command=self.open_settings)
    self.settings_button.pack(pady=5)

    def open_settings(self):
    """Opens a settings window to adjust work time"""
    settings_win = tk.Toplevel(self.root)
    settings_win.title("Settings")
    settings_win.geometry("300x200")

    tk.Label(settings_win, text="Set Work Duration (Minutes)").pack(pady=5)
    work_time_entry = tk.Entry(settings_win)
    work_time_entry.pack(pady=5)

    def save_settings():
        new_work_time = work_time_entry.get()
        if new_work_time.isdigit():
            new_work_time = int(new_work_time)
            if 10 <= new_work_time <= 180:  # Min 10 min, max 3 hours
                self.work_duration = new_work_time * 60
                self.time_var.set(f"{new_work_time}:00")
                settings_win.destroy()
            else:
                messagebox.showerror("Invalid", "Work time must be between 10 and 180 minutes")
        else:
            messagebox.showerror("Invalid", "Enter a number")

    tk.Button(settings_win, text="Save", command=save_settings).pack(pady=10)

 def __init__(self):
        self.blocked_processes = ["Taskmgr.exe", "cmd.exe", "regedit.exe", "ProcessHacker.exe"]
        self.running = True
        self.thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.thread.start()

    def monitor_processes(self):
        while self.running:
            self.check_tampering()  # 🔥 Check for renamed processes
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] in self.blocked_processes:
                    try:
                        proc.kill()
                        print(f"Blocked {proc.info['name']}")
                    except Exception as e:
                        print(f"Failed to block {proc.info['name']}: {e}")
            time.sleep(1)

    def check_tampering(self):
        """Detects renamed versions of blocked programs"""
        found_files = []
        for proc in psutil.process_iter(attrs=['pid', 'exe']):
            try:
                exe_path = proc.info['exe']
                if exe_path and any(tool.lower() in exe_path.lower() for tool in self.blocked_processes):
                    found_files.append(exe_path)
            except:
                pass  # Ignore permission errors

        if found_files:
            self.running = False  # 🔥 Pause program
            self.prompt_user(found_files)

    def prompt_user(self, found_files):
        """Ask user to paste paths of renamed tools"""
        paths = "\n".join(found_files)
        messagebox.showwarning(
            "Tampering Detected",
            f"🤡 Stop playing with my head 💯. Paste the paths of these tools:\n{paths}"
        )
        input("Paste here: ")  # Pause execution

    class ProcessBlocker:
    def __init__(self):
        self.blocked_processes = ["Taskmgr.exe", "cmd.exe", "regedit.exe", "ProcessHacker.exe"]
        self.running = True
        self.log_path = os.path.join(os.path.dirname(__file__), "FocusX.log")
        self.thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.thread.start()

    def log_event(self, message):
        """Logs events to FocusX.log"""
        with open(self.log_path, "a") as log_file:
            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            log_file.write(f"{timestamp} {message}\n")

    def monitor_processes(self):
        while self.running:
            self.check_tampering()  # 🔥 Check for renamed processes
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] in self.blocked_processes:
                    try:
                        proc.kill()
                        self.log_event(f"Blocked {proc.info['name']}")
                        print(f"Blocked {proc.info['name']}")
                    except Exception as e:
                        self.log_event(f"Failed to block {proc.info['name']}: {e}")
                        print(f"Failed to block {proc.info['name']}: {e}")
            time.sleep(1)

    def check_tampering(self):
        """Detects renamed versions of blocked programs"""
        found_files = []
        for proc in psutil.process_iter(attrs=['pid', 'exe']):
            try:
                exe_path = proc.info['exe']
                if exe_path and any(tool.lower() in exe_path.lower() for tool in self.blocked_processes):
                    found_files.append(exe_path)
            except:
                pass  # Ignore permission errors

        if found_files:
            self.running = False  # 🔥 Pause program
            self.log_event(f"TAMPERING DETECTED: {found_files}")
            self.auto_close_tampering_tools(found_files)

    def auto_close_tampering_tools(self, found_files):
        """Auto-close detected tampering tools"""
        for file in found_files:
            try:
                proc = next((p for p in psutil.process_iter(attrs=['pid', 'exe']) if p.info['exe'] == file), None)
                if proc:
                    proc.terminate()
                    self.log_event(f"Closed tampering tool: {file}")
                    print(f"🔥 Closed tampering tool: {file}")
            except Exception as e:
                self.log_event(f"Failed to close {file}: {e}")
                print(f"Failed to close {file}: {e}")

        messagebox.showwarning(
            "Tampering Detected",
            "🚫 You CANNOT bypass FocusX! We shut down your tools. Be serious 🤡💯"
        )


    # UI Setup - (UI setup remains the same)
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        self.time_var = tk.StringVar(value="40:00")
        self.time_label = tk.Label(main_frame,
                                        textvariable=self.time_var,
                                        font=('Helvetica', 48, 'bold'),
                                        fg=self.colors['text'],
                                        bg=self.colors['bg'])
        self.time_label.pack(pady=20)

        self.status_var = tk.StringVar(value="Ready to focus")
        self.status_label = tk.Label(main_frame,
                                            textvariable=self.status_var,
                                            font=('Helvetica', 14),
                                            fg=self.colors['primary'],
                                            bg=self.colors['bg'])
        self.status_label.pack(pady=10)

        self.start_button = tk.Button(main_frame,
                                        text="Start",
                                        command=self.start_timer,
                                        bg=self.colors['primary'],
                                        fg='white',
                                        width=10)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(main_frame,
                                       text="Emergency Stop",
                                       command=self.stop_timer,
                                       bg=self.colors['warning'],
                                       fg='white',
                                       width=20)
        self.stop_button.pack(pady=5)

    # Create Overlay Function - MODIFIED to use ScreenBlocker
    def create_overlay(self):
        """Create a simple black overlay on all screens using ScreenBlocker."""
        if self.screen_blocker.overlays: # Check if overlays already exist using ScreenBlocker
            return

        self.screen_blocker.block_all_screens() # Use ScreenBlocker to block screens
        overlays = self.screen_blocker.overlays # Get overlays created by ScreenBlocker
        activity_messages = [random.choice(self.break_activities) for _ in overlays] # Message per screen

        for i, overlay in enumerate(overlays):
            message_label = tk.Label(overlay,
                                            text=activity_messages[i], # Use pre-selected message
                                            font=('Arial', 24),
                                            fg='white',
                                            bg='black',
                                            wraplength=800)
            message_label.pack(expand=True)

            timer_label = tk.Label(overlay,
                                            font=('Arial', 18),
                                            fg='white',
                                            bg='black')
            timer_label.pack(pady=20)

            def update_display(overlay_timer_label, overlay_message_label, message_index=i): # Pass message index
                if overlay.winfo_exists(): # Check if overlay still exists
                    remaining = int(self.time_var.get().split(':')[0]) * 60 + int(self.time_var.get().split(':')[1])
                    mins, secs = divmod(remaining, 60)
                    overlay_timer_label.config(text=f"Break time remaining: {mins:02d}:{secs:02d}")

                    if remaining % 5 == 0:
                        overlay_message_label.config(text=activity_messages[message_index]) # Use message for this screen

                    overlay.after(1000, lambda: update_display(overlay_timer_label, overlay_message_label, message_index)) # Pass index


            update_display(timer_label, message_label)


        self.block_input()
        self.mute_audio()

    # Remove Overlay Function - MODIFIED to use ScreenBlocker
    def remove_overlay(self):
        """Remove blocking overlay from all screens using ScreenBlocker."""
        self.screen_blocker.remove_overlays() # Use ScreenBlocker's method to remove overlays
        self.unblock_input()
        self.unmute_audio()

    # Timer control, countdown, cleanup, input block/unblock - (timer functions remain the same)
    def start_timer(self):
        self.is_running = True
        self.is_work_session = True
        threading.Thread(target=self._run_timer, daemon=True).start()

    def stop_timer(self):
        self.is_running = False
        self.cleanup()

    def _run_timer(self):
        while self.is_running:
            if self.is_work_session:
                self.status_var.set("Work Session")
                self.unblock_input()
                self.unmute_audio()
                self.remove_overlay()
                self.countdown(self.work_duration)
            else:
                self.status_var.set("Break Time")
                self.create_overlay()
                self.countdown(self.rest_duration)

            if self.is_running:
                self.is_work_session = not self.is_work_session

    def countdown(self, duration):
        while duration > 0 and self.is_running:
            minutes, seconds = divmod(duration, 60)
            self.time_var.set(f"{minutes:02d}:{seconds:02d}")
            time.sleep(1)
            duration -= 1

    def cleanup(self):
        self.remove_overlay()
        self.remove_night_overlay()
        self.unblock_input()
        self.unmute_audio()
        self.time_var.set("40:00")
        self.status_var.set("Ready to focus")
        self.is_work_session = True

    def block_input(self):
        self.blocking = True
        self.mouse_listener = MouseListener(on_move=lambda x, y: False,
                                                on_click=lambda x, y, button, pressed: False)
        self.keyboard_listener = KeyboardListener(on_press=lambda key: False,
                                                        on_release=lambda key: False)
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def unblock_input(self):
        self.blocking = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

    # Run function - (run function remains the same)
    def run(self):
        # Initial time check before starting
        if self.is_night_time():
            self.create_night_overlay()
        self.root.mainloop()

class ProcessBlocker:
    """Blocks Task Manager, Registry Editor, Command Prompt, and other bypass tools."""
    
    def __init__(self):
        self.blocked_processes = ["Taskmgr.exe", "cmd.exe", "regedit.exe", "ProcessHacker.exe"]
        self.running = True
        self.thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.thread.start()

    def monitor_processes(self):
        """Continuously checks for and terminates blacklisted processes."""
        while self.running:
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] in self.blocked_processes:
                    try:
                        proc.kill()
                        print(f"Blocked {proc.info['name']}")
                    except Exception as e:
                        print(f"Failed to block {proc.info['name']}: {e}")
            time.sleep(1)  # Check every second

    def stop(self):
        """Stops the process monitoring thread."""
        self.running = False

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
            for hotkey in self.blocked_keys:
                keyboard.block_key(hotkey)
            time.sleep(0.1)  # Quick polling to maintain block

    def stop(self):
        """Stops the hotkey blocking."""
        self.running = False
        for hotkey in self.blocked_keys:
            keyboard.unblock_key(hotkey)

class SelfReviver:
    """Restarts the app if it gets force-closed."""
    
    def __init__(self, script_name):
        self.script_name = script_name
        self.running = True
        self.thread = threading.Thread(target=self.monitor_self, daemon=True)
        self.thread.start()

    def monitor_self(self):
        """Monitors if the script is terminated and restarts it."""
        while self.running:
            if not self.is_running():
                print("App was closed! Restarting...")
                self.restart_app()
            time.sleep(5)  # Check every 5 seconds

    def is_running(self):
        """Checks if the main script is still running."""
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if self.script_name in " ".join(proc.info['cmdline']):
                return True
        return False

    def restart_app(self):
        """Restarts the script."""
        subprocess.Popen([sys.executable] + sys.argv, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit()

    def stop(self):
        """Stops monitoring."""
        self.running = False

# Task manager and stuff like that
class ProcessBlocker:
    """Blocks Task Manager, Registry Editor, Command Prompt, and other bypass tools."""
    
    def __init__(self):
        self.blocked_processes = ["Taskmgr.exe", "cmd.exe", "regedit.exe", "ProcessHacker.exe"]
        self.running = True
        self.thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.thread.start()

    def monitor_processes(self):
        """Continuously checks for and terminates blacklisted processes."""
        while self.running:
            for proc in psutil.process_iter(attrs=['pid', 'name']):
                if proc.info['name'] in self.blocked_processes:
                    try:
                        proc.kill()
                        print(f"Blocked {proc.info['name']}")
                    except Exception as e:
                        print(f"Failed to block {proc.info['name']}: {e}")
            time.sleep(1)  # Check every second

    def stop(self):
        """Stops the process monitoring thread."""
        self.running = False


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
            for hotkey in self.blocked_keys:
                keyboard.block_key(hotkey)
            time.sleep(0.1)  # Quick polling to maintain block

    def stop(self):
        """Stops the hotkey blocking."""
        self.running = False
        for hotkey in self.blocked_keys:
            keyboard.unblock_key(hotkey)

class SelfReviver:
    """Restarts the app if it gets force-closed."""
    
    def __init__(self, script_name):
        self.script_name = script_name
        self.running = True
        self.thread = threading.Thread(target=self.monitor_self, daemon=True)
        self.thread.start()

    def monitor_self(self):
        """Monitors if the script is terminated and restarts it."""
        while self.running:
            if not self.is_running():
                print("App was closed! Restarting...")
                self.restart_app()
            time.sleep(5)  # Check every 5 seconds

    def is_running(self):
        """Checks if the main script is still running."""
        for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
            if self.script_name in " ".join(proc.info['cmdline']):
                return True
        return False

    def restart_app(self):
        """Restarts the script."""
        subprocess.Popen([sys.executable] + sys.argv, creationflags=subprocess.CREATE_NEW_CONSOLE)
        sys.exit()

    def stop(self):
        """Stops monitoring."""
        self.running = False

class SelfReviver:
    def __init__(self, exe_path):
        self.exe_path = exe_path
        self.setup_persistence()
    
    def setup_persistence(self):
        """Adds the app to Windows Startup via Registry"""
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key_handle = winreg.OpenKey(reg, key, 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key_handle, "FocusX", 0, winreg.REG_SZ, self.exe_path)
            winreg.CloseKey(key_handle)
            print("✔️ FocusX added to startup.")
        except Exception as e:
            print(f"❌ Failed to add startup entry: {e}")
    
    def restart_if_closed(self):
        """Uses Task Scheduler to restart the app if closed"""
        task_name = "FocusX_AutoRestart"
        cmd = f'schtasks /create /tn {task_name} /tr "{self.exe_path}" /sc onlogon /rl highest /f'
        subprocess.run(cmd, shell=True)
        print("✔️ FocusX is now self-reviving.")
    
    def remove_persistence(self):
        """Removes from startup (if needed)"""
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key_handle = winreg.OpenKey(reg, key, 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key_handle, "FocusX")
            winreg.CloseKey(key_handle)
            print("✔️ Removed FocusX from startup.")
        except:
            print("❌ Could not remove startup entry.")

# Example usage
self_reviver = SelfReviver("C:\\Users\\Nick\\Documents\\FocusX\\FocusX.exe")
self_reviver.restart_if_closed()

if __name__ == "__main__":
    # Start security features
    process_blocker = ProcessBlocker()
    hotkey_blocker = HotkeyBlocker()
    self_reviver = SelfReviver("FocusX.py")  # Change to actual script filename

    # Run Pomodoro
    app = PomodoroBlocker()
    app.run()

