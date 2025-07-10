# core/input_blocker.py

from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
import time # For potential future delays in blocking/unblocking

class InputBlocker:
    """
    Blocks mouse and keyboard input to enforce focus during specific periods.
    This is like locking the control panel during a critical mission phase –
    no accidental button presses or escapes!
    """
    def __init__(self, app_instance):
        # Reference to the main application instance (for logging/debugging purposes)
        self.app = app_instance 
        self.is_blocking = False # Flag to track current blocking state
        self.mouse_listener = None
        self.keyboard_listener = None

    def block_input(self):
        """
        Starts listeners that intercept all mouse and keyboard events, preventing them from reaching applications.
        If input is already blocked, it does nothing.
        """
        if self.is_blocking:
            return # Input is already blocked, no need to re-block.

        self.is_blocking = True
        print("Blocking mouse and keyboard input...")

        # Mouse listener: returns False for all events, effectively consuming them.
        # on_move: prevents mouse movement
        # on_click: prevents mouse clicks
        # on_scroll: prevents mouse scrolling
        self.mouse_listener = MouseListener(
            on_move=lambda x, y: False,
            on_click=lambda x, y, button, pressed: False,
            on_scroll=lambda x, y, dx, dy: False
        )
        # Keyboard listener: returns False for all events, consuming key presses and releases.
        self.keyboard_listener = KeyboardListener(
            on_press=lambda key: False,
            on_release=lambda key: False
        )

        # Start the listeners in their own threads.
        # This allows the GUI to remain responsive while input is blocked.
        self.mouse_listener.start()
        self.keyboard_listener.start()
        print("Mouse and keyboard input blocked.")

    def unblock_input(self):
        """
        Stops the mouse and keyboard listeners, returning control to the user.
        If input is not currently blocked, it does nothing.
        """
        if not self.is_blocking:
            return # Input is not blocked, no need to unblock.

        self.is_blocking = False
        print("Unblocking mouse and keyboard input...")

        # Stop the listeners. This releases the hooks on mouse and keyboard events.
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.mouse_listener = None # Clear the reference
        if self.keyboard_listener:
            self.keyboard_listener.stop()
            self.keyboard_listener = None # Clear the reference
        print("Mouse and keyboard input unblocked.")

