# core/night_mode.py

import threading
import time
from datetime import datetime
import ntplib
import socket
from tzlocal import get_localzone # External library for local timezone

class NightMode:
    """
    Manages the night-time blocking feature, encouraging rest during late hours.
    It synchronizes time with NTP servers and displays a full-screen overlay
    if the current time falls within defined "rest hours."
    This is like your digital night guard, making sure you get your beauty sleep!
    """
    def __init__(self, app_instance):
        # Reference to the main application instance to interact with GUI,
        # input blocker, and configuration.
        self.app = app_instance 

        self.ntp_servers = self.app.config.NTP_SERVERS
        self.time_offset = 0 # Offset in seconds from NTP server to local system time
        self.local_timezone = get_localzone() # Automatically detects local timezone

        self.night_overlay_window = None # Tkinter Toplevel window for the overlay

        # Start time synchronization and continuous monitoring.
        # These are launched in background threads to avoid freezing the GUI.
        self.sync_time()
        self.start_time_monitoring()

    def sync_time(self):
        """
        Synchronizes the application's time with a reliable NTP server.
        This ensures our internal clock is highly accurate and resistant to
        local system time tampering, just like setting your watch by the atomic clock!
        """
        print("Attempting to synchronize time with NTP servers...")
        for server in self.ntp_servers:
            try:
                ntp_client = ntplib.NTPClient()
                # Request time from the NTP server with a timeout.
                response = ntp_client.request(server, timeout=5)
                # Calculate the offset between server time and local time.
                self.time_offset = response.offset
                print(f"Time synchronized with {server}, offset: {self.time_offset:.2f} seconds.")
                return # Successfully synced, no need to try other servers.
            except (ntplib.NTPException, socket.gaierror, socket.timeout) as e:
                # If a server fails, it's like a bad Wi-Fi signal, just try the next one!
                print(f"Failed to sync with {server}: {e}. Trying next server...")
                continue
        print("Warning: Could not sync with any time server. Using system time. Time might be slightly off.")
        self.time_offset = 0 # Reset offset if no sync achieved.

    def get_accurate_time(self):
        """
        Retrieves the current accurate time, adjusting for any NTP offset.
        This ensures all time-based features (like night mode) use the most reliable time source.
        It's like having a universal time zone converter built right into the app!
        """
        current_time = datetime.now(self.local_timezone)
        if self.time_offset:
            # Apply the offset to the current timestamp to get adjusted time.
            current_time = current_time.fromtimestamp(time.time() + self.time_offset)
        return current_time

    def is_night_time(self):
        """
        Checks if the current accurate time falls within the defined "night hours" (12 AM to 6 AM).
        This acts as a gentle guardian, reminding you it's time to rest.
        """
        current_time = self.get_accurate_time()
        return 0 <= current_time.hour < 6 # Returns True if hour is between 0 (midnight) and 5 (inclusive).

    def create_night_overlay(self):
        """
        Creates a full-screen, uncloseable black overlay for night-time blocking.
        This visually enforces the "get rest" message, like pulling down a digital blackout curtain.
        """
        if self.night_overlay_window:
            return # If the overlay is already active, do nothing.
            
        self.night_overlay_window = tk.Toplevel(self.app.root)
        # Set attributes for full-screen, always-on-top, and no window decorations (like close button).
        self.night_overlay_window.attributes('-fullscreen', True, '-topmost', True, '-toolwindow', True)
        self.night_overlay_window.configure(bg='black')
        
        # Prevent manual closing of the overlay window.
        self.night_overlay_window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Message label: informing the user why the screen is blocked.
        message = tk.Label(
            self.night_overlay_window,
            text="It's late night hours (12 AM - 6 AM).\nPlease get some rest.",
            font=('Arial', 28, 'bold'), # Larger and bolder for clear visibility.
            fg='white',
            bg='black',
            justify='center',
            wraplength=800 # Wraps text to fit within a certain width.
        )
        message.pack(expand=True)
        
        # Time display label: showing current time on the overlay.
        time_label = tk.Label(
            self.night_overlay_window,
            font=('Arial', 22),
            fg='white',
            bg='black'
        )
        time_label.pack(pady=30)
        
        def update_time_display():
            """Internal function to continuously update the time shown on the overlay."""
            if self.night_overlay_window and self.night_overlay_window.winfo_exists():
                current_time = self.get_accurate_time()
                time_label.config(text=f"Current time: {current_time.strftime('%I:%M:%S %p')}")
                # Schedule this function to run again after 1 second.
                self.night_overlay_window.after(1000, update_time_display)
        
        update_time_display() # Start the time update loop.
        self.app.input_blocker.block_input() # Block all user input when night overlay is active.
        print("Night-time overlay created and input blocked.")

    def remove_night_overlay(self):
        """
        Removes the night-time blocking overlay and unblocks user input.
        This signifies the end of the enforced rest period, like a new dawn!
        """
        if self.night_overlay_window:
            self.night_overlay_window.destroy() # Close the overlay window.
            self.night_overlay_window = None # Clear the reference.
            self.app.input_blocker.unblock_input() # Unblock user input.
            print("Night-time overlay removed and input unblocked.")

    def start_time_monitoring(self):
        """
        Starts background threads for continuous time monitoring and periodic NTP synchronization.
        This ensures the night mode feature is always active and accurate in the background.
        It's like having two vigilant sentinels: one watching the clock, the other adjusting it.
        """
        def monitor_time_loop():
            """Loop to continuously check if it's night time."""
            while True:
                if self.is_night_time():
                    # If it's night time and overlay isn't active, create it.
                    if not self.night_overlay_window:
                        # Use self.app.root.after(0, ...) to ensure GUI updates happen on the main thread.
                        self.app.root.after(0, self.create_night_overlay)
                else:
                    # If it's not night time and overlay is active, remove it.
                    if self.night_overlay_window:
                        self.app.root.after(0, self.remove_night_overlay)
                time.sleep(30)  # Check every 30 seconds for efficiency.

        def periodic_sync_loop():
            """Loop to periodically re-synchronize time with NTP servers."""
            while True:
                time.sleep(3600)  # Sync every hour – because time doesn't wait for anyone!
                self.sync_time()
        
        # Start both monitoring loops in daemon threads so they exit when the main app exits.
        threading.Thread(target=monitor_time_loop, daemon=True).start()
        threading.Thread(target=periodic_sync_loop, daemon=True).start()
        print("Time monitoring and periodic sync started.")

