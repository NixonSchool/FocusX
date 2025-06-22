# core/scheduler.py

import os
import sys
import subprocess
import ctypes
import time

class Scheduler:
    def __init__(self, app_instance):
        self.app = app_instance
        self.task_name = self.app.config.TASK_NAME
        self.script_path = os.path.abspath(sys.argv[0])
        
        # Determine the path to pythonw.exe (console-less Python interpreter)
        # This is crucial for launching the wrapper and the main app silently.
        python_exe_base = os.path.basename(sys.executable)
        if python_exe_base.lower() == "python.exe":
            # If the current executable is python.exe, try to find pythonw.exe in the same directory.
            self.python_executable_silent = sys.executable.replace("python.exe", "pythonw.exe")
            # Fallback to python.exe if pythonw.exe isn't found (unlikely for standard Python installs)
            if not os.path.exists(self.python_executable_silent):
                self.python_executable_silent = sys.executable
        else:
            # If sys.executable is already pythonw.exe (or something else entirely), use it directly.
            self.python_executable_silent = sys.executable

    def _is_admin(self):
        if os.name == 'nt':
            import ctypes
            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except Exception as e:
                print(f"Error checking admin status: {e}")
                return False
        else:
            return os.getuid() == 0

    def _check_admin_and_prompt_persistence(self):
        if os.name != 'nt':
            self.app.gui.show_warning("Platform Warning", "Hardcore persistence features (Task Scheduler) are only supported on Windows.")
            return

        if not self._is_admin():
            self.app.gui.show_warning(
                "Administrator Rights Required",
                "To enable 'Hardcore Persistence' (auto-start and respawn),\n"
                "please run this application as Administrator at least once.\n"
                "This allows FocusX to set up a critical scheduled task for you."
            )
            if hasattr(self.app.gui, 'persistence_button'):
                self.app.gui.persistence_button.config(state='disabled')
        else:
            if hasattr(self.app.gui, 'persistence_button'):
                self.app.gui.persistence_button.config(state='normal')
            self._update_persistence_button_text()

    def _task_scheduler_exists(self):
        if os.name != 'nt':
            return False
        
        try:
            result = subprocess.run(
                ['schtasks', '/query', '/tn', self.task_name],
                capture_output=True, text=True, check=False
            )
            return self.task_name.lower() in result.stdout.lower()
        except Exception as e:
            print(f"Error checking task scheduler: {e}")
            return False

    def _add_to_task_scheduler(self):
        if os.name != 'nt':
            self.app.gui.show_warning("Platform Not Supported", "Task Scheduler is a Windows-specific feature.")
            return

        if not self._is_admin():
            self.app.gui.show_error(
                "Permission Denied",
                "Please run FocusX as Administrator to set up 'Hardcore Persistence'.\n"
                "This is necessary to create the scheduled task."
            )
            return

        if self._task_scheduler_exists():
            self.app.gui.show_info("Persistence Already On", "FocusX 'Hardcore Persistence' is already enabled!")
            self._update_persistence_button_text()
            return

        try:
            wrapper_script_path = os.path.join(os.path.dirname(self.script_path), "focusx_wrapper.py")
            self._create_wrapper_script(wrapper_script_path)

            # Use the silent Python executable (pythonw.exe) to launch the wrapper script.
            action_command_wrapper = f'"{self.python_executable_silent}" "{wrapper_script_path}"'
            
            command = [
                'schtasks', '/CREATE',
                '/TN', self.task_name,
                '/TR', action_command_wrapper,
                '/SC', 'ONLOGON',
                '/RL', 'HIGHEST',
                '/F'
            ]

            process = subprocess.run(command, capture_output=True, text=True, check=True)
            self.app.gui.show_info(
                "Persistence Enabled!",
                f"FocusX 'Hardcore Persistence' has been enabled!\n"
                f"It will now auto-start when you log in and attempt to respawn if terminated.\n"
                f"Output: {process.stdout.strip()}\nErrors: {process.stderr.strip()}"
            )
            self._update_persistence_button_text()
        except subprocess.CalledProcessError as e:
            self.app.gui.show_error(
                "Error Enabling Persistence",
                f"Failed to add to Task Scheduler. Make sure you have administrator rights.\n"
                f"Error: {e.stderr.strip()}"
            )
        except Exception as e:
            self.app.gui.show_error(
                "Unexpected Error",
                f"An unexpected error occurred while setting up persistence: {e}"
            )

    def _create_wrapper_script(self, path):
        # Pass the silent Python executable path to the wrapper script as well.
        wrapper_content = f"""import subprocess
import time
import sys
import os
import win32process

main_app_path = r"{self.script_path}"
python_exe = r"{self.python_executable_silent}" # Use the silent executable here

def is_focusx_running():
    try:
        output = subprocess.check_output(
            ['wmic', 'process', 'where', 'name="python.exe"', 'get', 'commandline', '/format:list'],
            text=True
        )
        return main_app_path.lower() in output.lower()
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        return False

def launch_focusx():
    try:
        # The wrapper should also use the silent executable when launching the main app.
        subprocess.Popen([python_exe, main_app_path], 
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                         close_fds=True)
    except Exception as e:
        pass

if __name__ == "__main__":
    time.sleep(10) 
    while True:
        if not is_focusx_running():
            launch_focusx()
        time.sleep(5)
"""
        try:
            with open(path, 'w') as f:
                f.write(wrapper_content)
            print(f"Wrapper script created at: {path}")
        except Exception as e:
            self.app.gui.show_error("Error Creating Wrapper", f"Could not create wrapper script: {e}")
            raise

    def _remove_from_task_scheduler(self):
        if os.name != 'nt':
            self.app.gui.show_warning("Platform Not Supported", "Task Scheduler is a Windows-specific feature.")
            return

        if not self._is_admin():
            self.app.gui.show_error(
                "Permission Denied",
                "Please run FocusX as Administrator to remove 'Hardcore Persistence'.\n"
                "This is necessary to delete the scheduled task."
            )
            return

        if not self._task_scheduler_exists():
            self.app.gui.show_info("Persistence Already Off", "FocusX 'Hardcore Persistence' is not enabled.")
            self._update_persistence_button_text()
            return

        try:
            process = subprocess.run(
                ['schtasks', '/DELETE', '/TN', self.task_name, '/F'],
                capture_output=True, text=True, check=True
            )
            self.app.gui.show_info(
                "Persistence Disabled!",
                f"FocusX 'Hardcore Persistence' has been disabled.\n"
                f"It will no longer auto-start or respawn.\n"
                f"Output: {process.stdout.strip()}\nErrors: {process.stderr.strip()}"
            )
            self._update_persistence_button_text()
        except subprocess.CalledProcessError as e:
            self.app.gui.show_error(
                "Error Disabling Persistence",
                f"Failed to remove from Task Scheduler. Make sure you have administrator rights.\n"
                f"Error: {e.stderr.strip()}"
            )
        except Exception as e:
            self.app.gui.show_error(
                "Unexpected Error",
                f"An unexpected error occurred while disabling persistence: {e}"
            )

    def _toggle_persistence(self):
        if self._task_scheduler_exists():
            self._remove_from_task_scheduler()
        else:
            self._add_to_task_scheduler()

    def _update_persistence_button_text(self):
        if hasattr(self.app.gui, 'persistence_button'):
            if self._task_scheduler_exists():
                self.app.gui.persistence_button.config(text="Disable Hardcore Persistence", bg=self.app.config.COLORS['danger'])
            else:
                self.app.gui.persistence_button.config(text="Enable Hardcore Persistence", bg=self.app.config.COLORS['primary'])

