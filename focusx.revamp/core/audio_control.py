# core/audio_control.py

from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class AudioControl:
    """
    Manages system audio muting and unmuting.
    This is like the sound engineer for your focus environment, silencing distractions.
    """
    def __init__(self, app_instance):
        # We need a reference to the main app (primarily for logging/printing, not direct GUI interaction).
        self.app = app_instance 
        self.audio_interface = None # Will hold the IAudioEndpointVolume object

        self._init_audio_control()

    def _init_audio_control(self):
        """
        Initializes the pycaw audio control capabilities.
        It attempts to get the interface to control the default audio endpoint (speakers).
        """
        try:
            # Get the default audio device (speakers).
            devices = AudioUtilities.GetSpeakers()
            # Activate the IAudioEndpointVolume interface for this device.
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            # Cast the interface to the correct COM pointer type.
            self.audio_interface = cast(interface, POINTER(IAudioEndpointVolume))
            print("Audio control initialized successfully.")
        except Exception as e:
            # If initialization fails (e.g., pycaw not fully set up, no audio device),
            # print an error but don't stop the app. The app can still run without audio control.
            print(f"Could not initialize audio control: {e}")
            self.audio_interface = None # Ensure it's None if initialization fails

    def mute_audio(self):
        """
        Mutes the system's default audio output.
        Shhh! Time to silence the world and listen to your thoughts.
        """
        if self.audio_interface:
            try:
                # SetMute(1, None) mutes the audio.
                self.audio_interface.SetMute(1, None)
                print("Audio muted.")
            except Exception as e:
                print(f"Could not mute audio: {e}")
        else:
            print("Audio control not initialized, cannot mute.")

    def unmute_audio(self):
        """
        Unmutes the system's default audio output.
        Break time! Let the sounds of freedom (or notifications) roll in!
        """
        if self.audio_interface:
            try:
                # SetMute(0, None) unmutes the audio.
                self.audio_interface.SetMute(0, None)
                print("Audio unmuted.")
            except Exception as e:
                print(f"Could not unmute audio: {e}")
        else:
            print("Audio control not initialized, cannot unmute.")

