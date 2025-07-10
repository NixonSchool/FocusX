import os
import threading
import time
import psutil # Robust process management

class TaskKiller:
    def __init__(self, app_instance):
        self.app = app_instance
        self._task_manager_monitor_active = False
        self._task_manager_thread = None

    def start_task_manager_monitoring(self):
        # Only activate for Windows.
        if os.name != 'nt':
            return

        # Return if monitoring is already active.
        if self._task_manager_monitor_active:
            return

        # Set flag and start monitoring thread.
        self._task_manager_monitor_active = True
        self._task_manager_thread = threading.Thread(target=self._monitor_task_manager_loop, daemon=True)
        self._task_manager_thread.start()

    def stop_task_manager_monitoring(self):
        # Return if not currently monitoring.
        if not self._task_manager_monitor_active:
            return

        # Signal thread to stop.
        self._task_manager_monitor_active = False
        if self._task_manager_thread and self._task_manager_thread.is_alive():
            pass

    def _monitor_task_manager_loop(self):
        # Monitors and terminates Task Manager during work sessions.
        while self._task_manager_monitor_active and self.app.timer.is_running and self.app.timer.is_work_session:
            try:
                # Iterate processes, requesting pid and name.
                for proc in psutil.process_iter(['pid', 'name']):
                    # Check for Task Manager (case-insensitive).
                    if proc.info['name'].lower() == 'taskmgr.exe':
                        # Task Manager found, attempt termination.
                        try:
                            proc.kill() # Terminate process.
                        except psutil.AccessDenied:
                            # Insufficient privileges.
                            pass
                        except psutil.NoSuchProcess:
                            # Process already terminated.
                            pass
                        except Exception:
                            # Catch other termination errors.
                            pass
                        break # Exit inner loop once handled.
            except psutil.NoSuchProcess:
                # Process terminated during iteration.
                pass
            except Exception:
                # Catch general iteration errors.
                pass

            # Check every 1 second.
            time.sleep(1)

        self._task_manager_monitor_active = False # Ensure flag is false.
