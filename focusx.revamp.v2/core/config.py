# core/config.py

# --- Application-wide Configuration ---
# Think of this as the main control panel for our FocusX app.
# All the core settings that don't change during a session are stored here.

class AppConfig:
    # Colors for the UI - chosen to be easy on the eyes and modern.
    # Like a well-designed website, these colors guide the user experience.
    COLORS = {
        'bg': '#f0f2f5',       # Light gray background, soft on the eyes
        'primary': '#4CAF50',  # Google-esque green, for go-getters!
        'warning': '#FFC107',  # A warm amber, like a gentle caution light
        'danger': '#F44336',   # Red, for serious "do not touch" moments!
        'text': '#333333',     # Dark gray for sharp, readable text
        'secondary_text': '#666666', # Lighter gray for less critical info
        'border': '#DDDDDD'    # Subtle border color
    }

    # NTP Servers for time synchronization.
    # These are like highly accurate atomic clocks keeping our app on schedule.
    NTP_SERVERS = [
        'pool.ntp.org',
        'time.google.com',
        'time.windows.com',
        'time.apple.com'
    ]

    # Break activity messages.
    # Short, friendly reminders to make the most of break time, like little notes from a helpful friend!
    BREAK_ACTIVITIES = [
        "Time to stretch like a cat waking from a nap!",
        "Grab a drink, hydrate that super brain!",
        "Look out the window, give your eyes a digital detox!",
        "Do a quick dance party in your chair, no judgment here!",
        "Tidy up your battle station – a clean space, a clear mind!",
        "Quick power walk around the room, get those steps in!",
        "Just breathe. Seriously, deep breaths are like a mental reset button."
    ]

    # Scheduled task name for persistence.
    # This is the secret handshake for our app to keep running even after reboots or accidental shutdowns.
    TASK_NAME = "FocusX_Hardcore_Mode"

    # Default window dimensions.
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 400

