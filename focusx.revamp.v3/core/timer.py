# core/timer.py

import threading
import time
from tkinter import messagebox

class Timer:
    def __init__(self, app_instance):
        self.app = app_instance 
        self.is_running = False
        self.is_work_session = True

        self.work_duration = 0 
        self.rest_duration = 0

    def start_timer(self):
        if self.is_running:
            self.app.gui.show_info("Already Running", "A session is already in progress. Stay focused!")
            return

        self.work_duration = self.app.gui.work_duration_minutes.get() * 60
        self.rest_duration = self.app.gui.rest_duration_minutes.get() * 60

        self.app.gui.time_var.set(f"{self.app.gui.work_duration_minutes.get():02d}:00")
        self.app.gui.status_var.set("Work Session Starting! 🔥")
        
        self.app.gui.work_slider.config(state='disabled')
        self.app.gui.rest_slider.config(state='disabled')
        self.app.gui.start_button.config(state='disabled')
        if hasattr(self.app.gui, 'persistence_button'):
            self.app.gui.persistence_button.config(state='disabled')

        self.is_running = True
        self.is_work_session = True
        
        threading.Thread(target=self._run_timer, daemon=True).start()

    def stop_timer(self):
        if not self.is_running:
            return

        self.is_running = False
        self.app.root.after(0, self._cleanup)

    def _run_timer(self):
        while self.is_running:
            if self.is_work_session:
                self.app.gui.status_var.set("Work Session in Progress! 🔥")
                self.app.input_blocker.unblock_input()
                self.app.audio_control.unmute_audio()
                if self.app.gui.overlay:
                    self.app.gui.overlay.destroy()
                    self.app.gui.overlay = None
                
                self.app.task_killer.start_task_manager_monitoring()

                # Pass the total duration of the work session
                self.countdown(self.work_duration)

            else:
                self.app.gui.status_var.set("Break Time! 🎉 Relax and Recharge!")
                self.app.gui.create_overlay()
                self.app.input_blocker.block_input()
                self.app.audio_control.mute_audio()
                
                self.app.task_killer.stop_task_manager_monitoring()

                # Pass the total duration of the rest session
                self.countdown(self.rest_duration)
            
            # Only switch session type if the timer is still running (i.e., not stopped externally)
            if self.is_running:
                self.is_work_session = not self.is_work_session
            else:
                break # Loop exits if is_running becomes False (e.g., app is closed forcefully)

    def countdown(self, total_session_duration):
        """
        Counts down the specified total duration, updating the GUI every second.
        This version is more accurate as it bases calculations on the initial start time.
        It's like having a reliable stopwatch that always measures from zero, preventing drift.
        """
        start_time = time.time()
        while self.is_running: # Loop as long as the app is active
            elapsed_time = time.time() - start_time
            current_duration_left = int(total_session_duration - elapsed_time)
            
            if current_duration_left <= 0:
                self.app.root.after(0, self.app.gui.time_var.set, "00:00") # Ensure it shows 00:00
                break # Exit the loop if time is up or negative

            minutes, seconds = divmod(current_duration_left, 60)
            
            # Update GUI on the main thread for smooth animation.
            self.app.root.after(0, self.app.gui.time_var.set, f"{minutes:02d}:{seconds:02d}")
            
            time.sleep(1) # Wait for approximately one second

    def _cleanup(self):
        if self.app.gui.overlay:
            self.app.gui.overlay.destroy()
            self.app.gui.overlay = None
        self.app.input_blocker.unblock_input()
        self.app.audio_control.unmute_audio()
        self.app.task_killer.stop_task_manager_monitoring()
        
        self.app.gui.time_var.set(f"{self.app.gui.work_duration_minutes.get():02d}:00")
        self.app.gui.status_var.set("Ready to focus!")
        
        self.is_work_session = True
        self.is_running = False

        self.app.gui.work_slider.config(state='normal')
        self.app.gui.rest_slider.config(state='normal')
        self.app.gui.start_button.config(state='normal')
        if hasattr(self.app.gui, 'persistence_button'):
            self.app.gui.persistence_button.config(state='normal')
            self.app.scheduler._update_persistence_button_text()

