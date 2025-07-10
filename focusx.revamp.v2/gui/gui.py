# gui/gui.py

import tkinter as tk
from tkinter import ttk, messagebox
import random

class GUI:
    def __init__(self, app_instance):
        self.app = app_instance
        self.root = self.app.root

        self.time_var = tk.StringVar(value="00:00")
        self.status_var = tk.StringVar(value="Set your focus and break times!")
        self.work_duration_minutes = tk.IntVar(value=50)
        self.rest_duration_minutes = tk.IntVar(value=10)

        self.overlay = None

    def setup_ui(self):
        self.root.configure(bg=self.app.config.COLORS['bg'])
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        main_frame = tk.Frame(self.root, bg=self.app.config.COLORS['bg'], bd=2, relief='flat')
        main_frame.pack(expand=True, fill='both', padx=30, pady=30)
        
        self.time_label = tk.Label(main_frame,
                                 textvariable=self.time_var,
                                 font=('Helvetica Neue', 60, 'bold'),
                                 fg=self.app.config.COLORS['primary'],
                                 bg=self.app.config.COLORS['bg'])
        self.time_label.pack(pady=20)
        
        self.status_label = tk.Label(main_frame,
                                   textvariable=self.status_var,
                                   font=('Helvetica Neue', 16),
                                   fg=self.app.config.COLORS['secondary_text'],
                                   bg=self.app.config.COLORS['bg'])
        self.status_label.pack(pady=10)

        work_frame = tk.Frame(main_frame, bg=self.app.config.COLORS['bg'])
        work_frame.pack(pady=5, fill='x')
        tk.Label(work_frame, text="Focus Time (30-50 min):", font=('Helvetica Neue', 12),
                 bg=self.app.config.COLORS['bg'], fg=self.app.config.COLORS['text']).pack(side='left', padx=5)
        self.work_slider = ttk.Scale(work_frame, from_=30, to=50, orient='horizontal',
                                     variable=self.work_duration_minutes, command=self.update_times_display)
        self.work_slider.pack(side='left', expand=True, fill='x', padx=5)
        self.work_time_label = tk.Label(work_frame, textvariable=self.work_duration_minutes,
                                        font=('Helvetica Neue', 12), bg=self.app.config.COLORS['bg'], fg=self.app.config.COLORS['primary'])
        self.work_time_label.pack(side='left', padx=5)
        
        rest_frame = tk.Frame(main_frame, bg=self.app.config.COLORS['bg'])
        rest_frame.pack(pady=5, fill='x')
        tk.Label(rest_frame, text="Break Time (2-10 min):", font=('Helvetica Neue', 12),
                 bg=self.app.config.COLORS['bg'], fg=self.app.config.COLORS['text']).pack(side='left', padx=5)
        self.rest_slider = ttk.Scale(rest_frame, from_=2, to=10, orient='horizontal',
                                    variable=self.rest_duration_minutes, command=self.update_times_display)
        self.rest_slider.pack(side='left', expand=True, fill='x', padx=5)
        self.rest_time_label = tk.Label(rest_frame, textvariable=self.rest_duration_minutes,
                                       font=('Helvetica Neue', 12), bg=self.app.config.COLORS['bg'], fg=self.app.config.COLORS['primary'])
        self.rest_time_label.pack(side='left', padx=5)

        button_frame = tk.Frame(main_frame, bg=self.app.config.COLORS['bg'])
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(button_frame,
                                    text="Start Focus Session",
                                    command=self.app.timer.start_timer,
                                    bg=self.app.config.COLORS['primary'],
                                    fg='white',
                                    font=('Helvetica Neue', 14, 'bold'),
                                    width=20,
                                    height=2,
                                    relief='raised',
                                    bd=0,
                                    activebackground=self.app.config.COLORS['primary'],
                                    activeforeground='white',
                                    cursor='hand2'
                                    )
        # Since 'stop_button' is removed, the 'start_button' is the only one in 'button_frame'.
        # We'll center it implicitly by making the 'button_frame' fill the available space.
        self.start_button.pack(side='top', padx=10, pady=5) # Changed to side='top' and added small pady for centering

        # Removed the Emergency Stop button block entirely.
        # This aligns with the "no stopping" rule.

        self.persistence_button = tk.Button(main_frame,
                                            text="Enable Hardcore Persistence",
                                            command=self.app.scheduler._toggle_persistence,
                                            bg=self.app.config.COLORS['primary'],
                                            fg='white',
                                            font=('Helvetica Neue', 12),
                                            width=30,
                                            height=1,
                                            relief='raised',
                                            bd=0,
                                            activebackground=self.app.config.COLORS['primary'],
                                            activeforeground='white',
                                            cursor='hand2'
                                            )
        # This button is already packed with side='top', anchor='center', so it remains centered.
        self.persistence_button.pack(pady=15, side='top', anchor='center')

        self.update_times_display()

    def update_times_display(self, *args):
        self.work_time_label.config(text=f"{self.work_duration_minutes.get()} min")
        self.rest_time_label.config(text=f"{self.rest_duration_minutes.get()} min")
        if not self.app.timer.is_running:
             self.time_var.set(f"{self.work_duration_minutes.get():02d}:00")

    def create_overlay(self):
        if self.overlay:
            return
            
        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes('-fullscreen', True, '-topmost', True, '-toolwindow', True)
        self.overlay.configure(bg='black')
        
        self.overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        message_label = tk.Label(self.overlay,
                               text=random.choice(self.app.config.BREAK_ACTIVITIES),
                               font=('Arial', 28, 'bold'),
                               fg='white',
                               bg='black',
                               wraplength=800,
                               justify='center')
        message_label.pack(expand=True)
        
        timer_label = tk.Label(self.overlay,
                             font=('Arial', 22),
                             fg='white',
                             bg='black')
        timer_label.pack(pady=30)
        
        def update_display():
            if self.overlay and self.overlay.winfo_exists():
                try:
                    minutes_str, seconds_str = self.time_var.get().split(':')
                    remaining = int(minutes_str) * 60 + int(seconds_str)
                except ValueError:
                    remaining = 0
                
                mins, secs = divmod(remaining, 60)
                timer_label.config(text=f"Break time remaining: {mins:02d}:{secs:02d}")
                
                if remaining % 5 == 0:
                    message_label.config(text=random.choice(self.app.config.BREAK_ACTIVITIES))
                
                self.overlay.after(1000, update_display)
        
        update_display()

    def on_closing(self):
        # Now, if any session is running (work or break), we prevent closing.
        # "Focus to the moon!" implies no stopping until the app is fully exited (e.g., system shutdown).
        if self.app.timer.is_running:
            self.show_info(
                "Hardcore Focus Active!",
                "There's no stopping now! This app is designed for continuous focus.\n"
                "Please complete your sessions or shut down your system.\n\n"
                "Why use a Pomodoro if you're going to bypass it? 🤔"
            )
        else:
            # Only allow closing if no session is running.
            self.root.destroy()

    def show_info(self, title, message):
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        messagebox.showwarning(title, message)

    def show_error(self, title, message):
        messagebox.showerror(title, message)

    def show_yesno(self, title, message):
        return messagebox.askyesno(title, message)

