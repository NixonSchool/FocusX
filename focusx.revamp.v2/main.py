# main.py

import tkinter as tk
import os
import sys

# Import our custom modules from the 'core' and 'gui' packages.
from core.config import AppConfig
from core.scheduler import Scheduler
from core.timer import Timer
from core.audio_control import AudioControl
from core.input_blocker import InputBlocker
from core.night_mode import NightMode
from core.task_killer import TaskKiller
from gui.gui import GUI

class PomodoroBlocker:
    """
    The main application class for FocusX.
    This acts as the central orchestrator, creating and managing instances
    of all the specialized modules (GUI, Timer, Scheduler, etc.).
    It's like the mission control center, coordinating all operations.
    """
    def __init__(self):
        # Store a reference to the global configuration FIRST.
        self.config = AppConfig

        # Initialize the Tkinter root window.
        self.root = tk.Tk()
        self.root.title("Focus Time")
        
        # Explicitly set the geometry of the root window here first.
        # This ensures winfo_screenwidth/height have valid values when called later for centering.
        # It's like measuring your plot before you start digging foundations!
        window_width = self.config.WINDOW_WIDTH
        window_height = self.config.WINDOW_HEIGHT
        screen_width = self.root.winfo_screenwidth() # Get screen width
        screen_height = self.root.winfo_screenheight() # Get screen height
        
        # Calculate center coordinates
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.root.attributes('-topmost', True) # Keep window on top for focus.

        # Initialize core functionalities by passing 'self' (the main app instance).
        # The order here is important! Initialize all functional modules first.
        self.gui = GUI(self) # Initialize GUI instance
        self.timer = Timer(self)
        self.scheduler = Scheduler(self)
        self.audio_control = AudioControl(self)
        self.input_blocker = InputBlocker(self)
        self.night_mode = NightMode(self)
        self.task_killer = TaskKiller(self)

        # NOW call setup_ui on the gui instance, AFTER all its dependencies (like self.timer, self.scheduler) are ready.
        # This is like plugging in all the components before flipping the power switch on the control panel.
        self.gui.setup_ui()

        # Initial check for admin privileges and prompt for persistence setup.
        # This is delayed slightly to allow the GUI to fully initialize.
        self.root.after(100, self.scheduler._check_admin_and_prompt_persistence)

    # Removed _get_center_x and _get_center_y as they are now in __init__ for clarity
    # and to ensure winfo_screenwidth/height are called after root is fully set up.
    
    def run(self):
        """
        Starts the main Tkinter event loop.
        This is where the application comes alive and starts interacting with the user.
        """
        # Initial check for night-time blocking before the main loop starts.
        if self.night_mode.is_night_time():
            self.night_mode.create_night_overlay()
        self.root.mainloop()

if __name__ == "__main__":
    # The entry point of our application.
    # When you run main.py, a PomodoroBlocker instance is created, and its main loop starts.
    app = PomodoroBlocker()
    app.run()

