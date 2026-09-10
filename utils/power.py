import ctypes
import os
import platform
import subprocess
import threading
import time

# Windows Constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002

class KeepAwake:
    """
    A context manager to prevent the system and screen from sleeping.
    Works on Windows, macOS, and Linux.
    """
    def __init__(self):
        self.os_type = platform.system()
        self._mac_process = None
        self._linux_process = None
        
    def __enter__(self):
        self.awake()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.sleep()

    def awake(self):
        try:
            if self.os_type == 'Windows':
                ctypes.windll.kernel32.SetThreadExecutionState(
                    ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED
                )
            elif self.os_type == 'Darwin':
                # macOS
                self._mac_process = subprocess.Popen(['caffeinate', '-dim'])
            elif self.os_type == 'Linux':
                # Try xdotool to simulate keypress or just systemd-inhibit
                # We can try to inhibit idle via dbus
                try:
                    self._linux_process = subprocess.Popen(
                        ['systemd-inhibit', '--what=idle:sleep', '--who=ScreenGallery', '--why="Playing slideshow"', 'sleep', 'infinity']
                    )
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"Failed to prevent sleep: {e}")

    def sleep(self):
        try:
            if self.os_type == 'Windows':
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            elif self.os_type == 'Darwin':
                if self._mac_process:
                    self._mac_process.terminate()
                    self._mac_process = None
            elif self.os_type == 'Linux':
                if self._linux_process:
                    self._linux_process.terminate()
                    self._linux_process = None
        except Exception as e:
            print(f"Failed to restore sleep settings: {e}")

if __name__ == '__main__':
    with KeepAwake():
        print("System is kept awake. Waiting 5 seconds...")
        time.sleep(5)
    print("Done.")
