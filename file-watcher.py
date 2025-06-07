import time
import threading # used for timers

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

class DebouncedHandler(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a warmdown priod
    for things to settle before triggering the change handler.
    """
    def __init__(self, warmdown=1.0):
        self.warmdown = warmdown
        self.timer = None
        self.lock = threading.Lock()
        self.verbose = True

    def on_any_event(self, event: FileSystemEvent):
        with self.lock:
            if self.timer:
                self.timer.cancel()
                if self.verbose: print("Restarted warmdown timer...")
            else:
                if self.verbose: print("Starting warmdown timer...")
            self.timer = threading.Timer(self.warmdown, lambda: self.handle_change(event))
            self.timer.start()

    def handle_change(self, event):
        self.timer = None
        if self.verbose: print("Change event triggered.")


def main():
    event_handler = DebouncedHandler(warmdown=2)
    observer = Observer()
    observer.schedule(event_handler, "demo", recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()