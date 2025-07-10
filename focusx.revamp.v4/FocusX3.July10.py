import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
import os
import random
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import ntplib
import socket
from tzlocal import get_localzone

class PomodoroBlocker:
    def __init__(self):
        # Initialize the main application window
        self.root = tk.Tk()
        self.root.title("Focus Time")
        
        # Set window size and position it in the center of the screen
        window_width = 450 # Increased width for new controls
        window_height = 400 # Increased height for new controls
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Keep the window on top of others
        self.root.attributes('-topmost', True)
        
        # Define a simple color scheme for the UI
        self.colors = {
            'bg': '#ffffff',
            'primary': '#1a73e8', # A vibrant blue for main actions
            'secondary': '#34a853', # A green for positive actions like resume
            'warning': '#ea4335', # A red for stop/emergency actions
            'text': '#202124', # Dark text for readability
            'accent': '#fbbc05' # An amber for highlights
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Timer settings initialization
        # Default work duration (50 minutes) and rest duration (5 minutes)
        self.default_work_duration = 50 * 60
        self.default_rest_duration = 5 * 60
        
        # Current session durations, which can be adjusted by the user
        self.work_duration = tk.IntVar(value=self.default_work_duration // 60) # Stored in minutes
        self.rest_duration = tk.IntVar(value=self.default_rest_duration // 60) # Stored in minutes
        
        self.current_duration = 0 # Tracks the remaining time in the current phase
        self.is_running = False # Flag to indicate if the timer is actively counting down
        self.is_paused = False # Flag to indicate if the timer is paused
        self.is_work_session = True # True for work, False for break
        self.timer_thread = None # Reference to the thread running the timer
        
        # Time synchronization settings for accurate timekeeping
        self.ntp_servers = [
            'pool.ntp.org',
            'time.google.com',
            'time.windows.com',
            'time.apple.com'
        ]
        self.time_offset = 0 # Offset from local system time based on NTP sync
        self.local_timezone = get_localzone() # Get the local timezone for accurate time display
        
        # Messages displayed during breaks to encourage specific activities
        self.break_activities = [
            "Take time to read and reflect",
            "Step away from the screen and rest your eyes",
            "Go for a short walk",
            "Do some light stretching",
            "Practice deep breathing",
            "Hydrate yourself",
            "Tidy up your workspace",
            "Listen to some calming music",
            "Do a quick meditation",
            "Call a friend or family member"
        ]
        
        self.overlay = None # Reference to the fullscreen overlay for breaks
        
        # Input blocking flags and listeners
        self.blocking_input = False # Flag to indicate if mouse/keyboard are blocked
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Audio control initialization (using pycaw for Windows)
        self.audio = None
        self.init_audio_control()
        
        # Setup the user interface elements
        self.setup_ui()
        
        # Initialize internal default timer for passive break enforcement
        self.last_activity_time = datetime.now() # Tracks when the app was launched or a session started
        self.internal_timer_thread = None
        self.start_internal_timer_monitoring()

        # Synchronize time on startup
        self.sync_time()

    def sync_time(self):
        """
        Synchronizes the system time with an NTP server.
        This is like setting your watch against a highly accurate atomic clock.
        It ensures that the timer runs on a precise, globally consistent time,
        preventing any local system clock drift from affecting your focus sessions.
        """
        for server in self.ntp_servers:
            try:
                ntp_client = ntplib.NTPClient()
                response = ntp_client.request(server, timeout=5)
                self.time_offset = response.offset
                print(f"Time synchronized with {server}, offset: {self.time_offset:.2f} seconds")
                return
            except (ntplib.NTPException, socket.gaierror, socket.timeout) as e:
                print(f"Could not sync with {server}: {e}")
                continue
        print("Warning: Could not sync with any time server, using system time. Time might drift.")

    def get_accurate_time(self):
        """
        Retrieves the current time, adjusted by any NTP offset.
        Think of this as checking your watch after it's been precisely set.
        It gives you the most accurate time available, crucial for reliable
        scheduling of breaks and focus periods.
        """
        current_time = datetime.now(self.local_timezone)
        if self.time_offset:
            # Apply the offset to get the truly accurate time
            current_time = current_time.fromtimestamp(time.time() + self.time_offset, tz=self.local_timezone)
        return current_time

    def init_audio_control(self):
        """
        Initializes audio control capabilities using pycaw.
        This is like setting up a remote control for your system's volume.
        It allows the application to mute or unmute audio during breaks,
        helping to minimize distractions and reinforce the break period.
        """
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.audio = cast(interface, POINTER(IAudioEndpointVolume))
        except Exception as e:
            print(f"Could not initialize audio control: {e}. Audio muting/unmuting might not work.")

    def mute_audio(self):
        """
        Mutes the system audio.
        Imagine flipping a silent switch for your computer's sound.
        This helps create a quiet environment during breaks,
        encouraging you to step away from active tasks.
        """
        if self.audio:
            try:
                self.audio.SetMute(1, None) # 1 means mute
            except Exception as e:
                print(f"Could not mute audio: {e}")

    def unmute_audio(self):
        """
        Unmutes the system audio.
        Think of this as flipping the silent switch back to allow sound.
        It restores your audio after a break, so you can resume your work
        or other activities with sound enabled.
        """
        if self.audio:
            try:
                self.audio.SetMute(0, None) # 0 means unmute
            except Exception as e:
                print(f"Could not unmute audio: {e}")

    def setup_ui(self):
        """
        Sets up all the graphical user interface elements.
        This is like arranging all the controls on a dashboard.
        It includes the timer display, status messages, and buttons
        for starting, stopping, pausing, and resuming sessions,
        along with input fields for adjusting session durations.
        """
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=20, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        # Timer display
        self.time_var = tk.StringVar(value="00:00") # Initialize to 00:00
        self.time_label = tk.Label(main_frame,
                                 textvariable=self.time_var,
                                 font=('Helvetica', 60, 'bold'), # Larger font for timer
                                 fg=self.colors['text'],
                                 bg=self.colors['bg'])
        self.time_label.pack(pady=10)
        
        # Status display
        self.status_var = tk.StringVar(value="Ready to focus")
        self.status_label = tk.Label(main_frame,
                                   textvariable=self.status_var,
                                   font=('Helvetica', 16),
                                   fg=self.colors['primary'],
                                   bg=self.colors['bg'])
        self.status_label.pack(pady=5)

        # Duration adjustment controls
        settings_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        settings_frame.pack(pady=10)

        # Focus time adjustment
        tk.Label(settings_frame, text="Focus (mins):", bg=self.colors['bg'], fg=self.colors['text']).grid(row=0, column=0, padx=5, pady=2)
        self.focus_spinbox = ttk.Spinbox(settings_frame, from_=20, to=120, textvariable=self.work_duration, width=5, command=self.update_session_durations)
        self.focus_spinbox.grid(row=0, column=1, padx=5, pady=2)
        self.focus_spinbox.set(self.default_work_duration // 60) # Set initial value

        # Break time adjustment
        tk.Label(settings_frame, text="Break (mins):", bg=self.colors['bg'], fg=self.colors['text']).grid(row=1, column=0, padx=5, pady=2)
        self.break_spinbox = ttk.Spinbox(settings_frame, from_=1, to=10, textvariable=self.rest_duration, width=5, command=self.update_session_durations)
        self.break_spinbox.grid(row=1, column=1, padx=5, pady=2)
        self.break_spinbox.set(self.default_rest_duration // 60) # Set initial value

        # Control buttons frame
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(pady=10)
        
        # Start button
        self.start_button = tk.Button(button_frame,
                                    text="Start",
                                    command=self.start_timer,
                                    bg=self.colors['primary'],
                                    fg='white',
                                    width=10,
                                    font=('Helvetica', 12, 'bold'),
                                    relief='raised',
                                    bd=2,
                                    activebackground=self.colors['primary'],
                                    activeforeground='white')
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        # Stop button (now functions as a full stop and reset)
        self.stop_button = tk.Button(button_frame,
                                   text="Stop",
                                   command=self.stop_timer,
                                   bg=self.colors['warning'],
                                   fg='white',
                                   width=10,
                                   font=('Helvetica', 12, 'bold'),
                                   relief='raised',
                                   bd=2,
                                   activebackground=self.colors['warning'],
                                   activeforeground='white')
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        # Pause button
        self.pause_button = tk.Button(button_frame,
                                    text="Pause",
                                    command=self.pause_timer,
                                    bg=self.colors['accent'],
                                    fg='white',
                                    width=10,
                                    font=('Helvetica', 12, 'bold'),
                                    relief='raised',
                                    bd=2,
                                    activebackground=self.colors['accent'],
                                    activeforeground='white')
        self.pause_button.grid(row=1, column=0, padx=5, pady=5)
        self.pause_button.config(state=tk.DISABLED) # Initially disabled

        # Resume button
        self.resume_button = tk.Button(button_frame,
                                     text="Resume",
                                     command=self.resume_timer,
                                     bg=self.colors['secondary'],
                                     fg='white',
                                     width=10,
                                     font=('Helvetica', 12, 'bold'),
                                     relief='raised',
                                     bd=2,
                                     activebackground=self.colors['secondary'],
                                     activeforeground='white')
        self.resume_button.grid(row=1, column=1, padx=5, pady=5)
        self.resume_button.config(state=tk.DISABLED) # Initially disabled

        # Initial display of time based on default work duration
        self.update_time_display(self.work_duration.get() * 60)

    def update_session_durations(self):
        """
        Updates the internal work and rest durations based on spinbox values.
        This is like adjusting the dials on a machine before starting it.
        It ensures that the timer uses the user's preferred focus and break lengths.
        """
        self.default_work_duration = self.work_duration.get() * 60
        self.default_rest_duration = self.rest_duration.get() * 60
        if not self.is_running and not self.is_paused:
            # Only update the displayed time if no session is active
            self.update_time_display(self.default_work_duration)

    def create_overlay(self):
        """
        Creates a fullscreen, black overlay with a rotating break message.
        Imagine a curtain drawing across your screen, gently reminding you
        to step away. This overlay blocks visual access to your desktop
        during breaks, helping you disengage from work.
        """
        if self.overlay:
            # If an overlay already exists, destroy it first to prevent duplicates
            self.overlay.destroy()
        
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-fullscreen', True, '-topmost', True)
        self.overlay.configure(bg='black')
        
        message_label = tk.Label(self.overlay,
                               text=random.choice(self.break_activities),
                               font=('Arial', 28, 'bold'), # Larger and bolder font for messages
                               fg='white',
                               bg='black',
                               wraplength=self.root.winfo_screenwidth() - 100, # Wrap text to screen width
                               justify='center')
        message_label.pack(expand=True)
        
        timer_label = tk.Label(self.overlay,
                             font=('Arial', 22),
                             fg='white',
                             bg='black')
        timer_label.pack(pady=30) # More padding for timer label
        
        def update_display():
            """
            Updates the overlay's timer and message periodically.
            This is like a rotating billboard on your break screen.
            It keeps you informed of the remaining break time and
            offers fresh suggestions for how to spend your break.
            """
            if self.overlay and self.is_running and not self.is_work_session:
                # Update timer
                mins, secs = divmod(self.current_duration, 60)
                timer_label.config(text=f"Break time remaining: {mins:02d}:{secs:02d}")
                
                # Update message every 10 seconds
                if secs % 10 == 0:
                    message_label.config(text=random.choice(self.break_activities))
                
                self.overlay.after(1000, update_display) # Schedule next update
        
        update_display() # Start the updates

    def remove_overlay(self):
        """
        Removes the fullscreen break overlay.
        This is like pulling back the curtain, revealing your desktop again.
        It signifies the end of the break and the return to your work environment.
        """
        if self.overlay:
            self.overlay.destroy()
            self.overlay = None

    def start_timer(self):
        """
        Starts a new Pomodoro session.
        Think of hitting the 'start' button on a stopwatch.
        It initiates the work-break cycle, resetting any passive timers,
        and begins counting down the focus time.
        """
        if self.is_running and not self.is_paused:
            # If already running and not paused, do nothing
            return
        
        self.is_running = True
        self.is_paused = False
        self.is_work_session = True
        self.current_duration = self.work_duration.get() * 60 # Set to user-defined focus time
        self.last_activity_time = datetime.now() # Reset internal timer
        self.status_var.set("Work Session")
        self.update_button_states()
        
        # Start the timer in a separate thread to keep the UI responsive
        if self.timer_thread and self.timer_thread.is_alive():
            # If a thread is already running (e.g., from a previous session), stop it gracefully
            self.is_running = False
            self.timer_thread.join() # Wait for the old thread to finish
        
        self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
        self.timer_thread.start()

    def stop_timer(self):
        """
        Completely stops the current Pomodoro session and resets everything.
        This is like pressing the 'reset' button on a stopwatch.
        It ends the current cycle, clears the timer, and brings the application
        back to its initial "Ready to focus" state.
        """
        self.is_running = False
        self.is_paused = False
        self.cleanup() # Resets UI and input/audio states
        self.update_button_states()
        self.update_time_display(self.work_duration.get() * 60) # Show default work time

    def pause_timer(self):
        """
        Pauses the current Pomodoro session, preserving the remaining time.
        This is like pressing the 'lap' button on a stopwatch – it temporarily
        halts the countdown without resetting it. You can resume from this point later.
        """
        if self.is_running and not self.is_paused:
            self.is_paused = True
            self.is_running = False # Stop the _run_timer loop
            self.status_var.set("Paused")
            self.update_button_states()
            self.remove_overlay() # Ensure overlay is removed if paused during break
            self.unblock_input() # Ensure input is unblocked
            self.unmute_audio() # Ensure audio is unmuted

    def resume_timer(self):
        """
        Resumes a paused Pomodoro session from where it left off.
        This is like pressing 'start' again on a stopwatch after a pause.
        It continues the countdown from the exact moment it was paused,
        allowing you to pick up your focus session without losing progress.
        """
        if self.is_paused:
            self.is_running = True
            self.is_paused = False
            self.status_var.set("Work Session" if self.is_work_session else "Break Time")
            self.update_button_states()
            
            # Restart the timer thread if it's not alive (it would have stopped when paused)
            if not self.timer_thread or not self.timer_thread.is_alive():
                self.timer_thread = threading.Thread(target=self._run_timer, daemon=True)
                self.timer_thread.start()

    def update_button_states(self):
        """
        Manages the enabled/disabled state of the UI buttons.
        This is like a traffic light for your controls, guiding you
        on what actions are available at any given moment.
        It prevents illogical actions, like pausing a non-running timer.
        """
        if self.is_running and not self.is_paused:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.NORMAL)
            self.resume_button.config(state=tk.DISABLED)
            self.focus_spinbox.config(state=tk.DISABLED)
            self.break_spinbox.config(state=tk.DISABLED)
        elif self.is_paused:
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.NORMAL)
            self.focus_spinbox.config(state=tk.NORMAL)
            self.break_spinbox.config(state=tk.NORMAL)
        else: # Not running, not paused (initial state or after stop)
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.DISABLED)
            self.resume_button.config(state=tk.DISABLED)
            self.focus_spinbox.config(state=tk.NORMAL)
            self.break_spinbox.config(state=tk.NORMAL)

    def _run_timer(self):
        """
        The core logic of the Pomodoro timer, running in a separate thread.
        This is the engine of your focus system, tirelessly counting down
        and switching between work and break phases. It's designed to run
        smoothly in the background without freezing your application.
        """
        while self.is_running:
            if self.is_work_session:
                self.status_var.set("Work Session")
                self.remove_overlay() # Ensure overlay is gone during work
                self.unblock_input() # Ensure input is unblocked
                self.unmute_audio()
                self.countdown(self.current_duration) # Continue from current duration
            else:
                self.status_var.set("Break Time")
                self.create_overlay() # Show overlay for break
                self.block_screen_only() # Only block screen, not input
                self.mute_audio()
                self.countdown(self.current_duration) # Continue from current duration
            
            if self.is_running: # Check if still running after countdown
                self.is_work_session = not self.is_work_session # Toggle session type
                # Set duration for the next session based on user settings
                self.current_duration = (self.work_duration.get() * 60 if self.is_work_session 
                                         else self.rest_duration.get() * 60)
                self.root.after(0, self.update_time_display, self.current_duration) # Update UI immediately

        # If the loop exits (timer stopped or paused), ensure cleanup
        if not self.is_paused: # Only cleanup fully if stopped, not just paused
            self.root.after(0, self.cleanup) # Schedule cleanup on main thread

    def countdown(self, duration):
        """
        Performs the actual second-by-second countdown.
        This is the ticking clock mechanism itself. It updates the display
        every second and decrements the remaining time, stopping if the
        session is paused or completely stopped.
        """
        while duration > 0 and self.is_running and not self.is_paused:
            self.current_duration = duration # Update current duration for pause/resume
            self.root.after(0, self.update_time_display, duration) # Update UI on main thread
            time.sleep(1)
            duration -= 1
        
        # If countdown finished and still running (not paused/stopped prematurely)
        if duration <= 0 and self.is_running and not self.is_paused:
            self.current_duration = 0 # Ensure it's zero after countdown
            self.root.after(0, self.update_time_display, 0) # Final update to 00:00

    def update_time_display(self, duration):
        """
        Updates the time displayed on the main UI.
        This is like the hands of a clock moving. It takes the remaining
        duration and formats it into minutes and seconds for the user to see.
        """
        minutes, seconds = divmod(duration, 60)
        self.time_var.set(f"{minutes:02d}:{seconds:02d}")

    def cleanup(self):
        """
        Resets the application to its initial state after a session ends or is stopped.
        Think of it as tidying up your workspace after a task. It removes overlays,
        unblocks input, unmutes audio, and resets the timer display and status.
        """
        self.remove_overlay()
        self.unblock_input() # Ensure all input is unblocked
        self.unmute_audio()
        self.time_var.set(f"{self.work_duration.get():02d}:00") # Reset to default work time
        self.status_var.set("Ready to focus")
        self.is_work_session = True # Always start as work session
        self.current_duration = self.work_duration.get() * 60 # Reset current duration
        self.update_button_states() # Update button states to initial

    def block_input(self):
        """
        Blocks both mouse and keyboard input.
        This is like putting a "Do Not Disturb" sign on your computer.
        It prevents any interaction with the system, ensuring you fully
        disengage during critical blocking periods.
        """
        if not self.blocking_input: # Only start listeners if not already blocking
            self.blocking_input = True
            # Listeners return False to block events
            self.mouse_listener = MouseListener(on_move=lambda x, y: False,
                                              on_click=lambda x, y, button, pressed: False)
            self.keyboard_listener = KeyboardListener(on_press=lambda key: False,
                                                    on_release=lambda key: False)
            self.mouse_listener.start()
            self.keyboard_listener.start()

    def block_screen_only(self):
        """
        Blocks only the screen visually by showing the overlay, but keeps input unblocked.
        This is like putting a privacy screen on your monitor – you can't see,
        but you can still type or move the mouse if absolutely necessary.
        Used for breaks where interaction isn't strictly forbidden, just discouraged.
        """
        # Ensure input is NOT blocked when this is called
        self.unblock_input() 
        self.create_overlay() # The overlay itself blocks the screen visually

    def unblock_input(self):
        """
        Unblocks mouse and keyboard input.
        This is like taking down the "Do Not Disturb" sign.
        It restores normal interaction with your computer, allowing you
        to use your mouse and keyboard freely.
        """
        if self.blocking_input: # Only stop listeners if they are running
            self.blocking_input = False
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None

    def start_internal_timer_monitoring(self):
        """
        Starts a background thread to monitor time for passive break enforcement.
        This is like a silent, internal clock always running in the background.
        Even if you don't start a Pomodoro, it keeps track of how long the app
        has been running and will trigger default breaks to ensure you rest.
        """
        def monitor_internal_time():
            while True:
                # Only enforce if no explicit Pomodoro session is running
                if not self.is_running and not self.is_paused:
                    elapsed_time = (datetime.now() - self.last_activity_time).total_seconds()
                    
                    # If default work duration has passed, enforce a break
                    if elapsed_time >= self.default_work_duration:
                        self.root.after(0, self.enforce_default_break)
                        # Reset last activity time to start counting for the next default focus period
                        self.last_activity_time = datetime.now()
                time.sleep(1) # Check every second

        if not self.internal_timer_thread or not self.internal_timer_thread.is_alive():
            self.internal_timer_thread = threading.Thread(target=monitor_internal_time, daemon=True)
            self.internal_timer_thread.start()

    def enforce_default_break(self):
        """
        Enforces a default break when the internal timer triggers it.
        This is like an automatic system reminding you to take a breather.
        It activates the break overlay and mutes audio, even if you haven't
        explicitly started a Pomodoro session.
        """
        if not self.is_running and not self.is_paused: # Only enforce if no session is active
            messagebox.showinfo("Break Time!", "Time for a default break! Please rest your eyes.")
            self.status_var.set("Default Break Time")
            self.create_overlay()
            self.block_screen_only() # Only block screen
            self.mute_audio()
            
            # Start a temporary countdown for the default break
            def default_break_countdown(duration):
                while duration > 0 and not self.is_running and not self.is_paused:
                    self.root.after(0, self.update_time_display, duration)
                    time.sleep(1)
                    duration -= 1
                
                # After default break, clean up and reset
                if not self.is_running and not self.is_paused:
                    self.root.after(0, self.remove_overlay)
                    self.root.after(0, self.unblock_input)
                    self.root.after(0, self.unmute_audio)
                    self.root.after(0, self.status_var.set, "Ready to focus (Default Break Ended)")
                    self.root.after(0, self.update_time_display, self.work_duration.get() * 60) # Reset display

            threading.Thread(target=default_break_countdown, args=(self.default_rest_duration,), daemon=True).start()

    def run(self):
        """
        Starts the main Tkinter event loop.
        This is the heart of the application, keeping the window open and
        responsive to user interactions. It's where the UI comes alive.
        """
        self.root.mainloop()

if __name__ == "__main__":
    app = PomodoroBlocker()
    app.run()
