#!/usr/bin/env python3
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

# Filename suffixes to ignore (swap, backup, temp)
IGNORE_SUFFIXES = ['.swp', '.swx', '~', '.tmp', '.temp']

class FileWatcher(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a cooldown priod
    for things to settle before triggering the change handler.
    """
    def __init__(self, dir, callback, cooldown=1.0):
        self.dir = dir # directory to watch
        self.callback = callback # to call after file event
        self.cooldown = cooldown # minimum delay after event before callback

        self.file_observer = Observer()
        self.timer = None
        self.lock = threading.Lock()
        self.verbose = True

    def on_any_event(self, event: FileSystemEvent):
        path = event.src_path
        name = os.path.basename(path)

        # skip directories, git internals, ignored suffixes, hidden, or no-ext
        if event.is_directory or '.git/' in path or '.jj/' in path: return
        if name.startswith('.'): return
        if not os.path.splitext(name)[1]: return
        for suffix in IGNORE_SUFFIXES:
            if path.endswith(suffix): return
        
        # start cooldown timer
        with self.lock:
            if self.timer:
                self.timer.cancel()
                if self.verbose: print("Restarted cooldown timer...")
            else:
                if self.verbose: print("Starting cooldown timer...")
            self.timer = threading.Timer(self.cooldown, self.handle_change)
            self.timer.start()

    def handle_change(self):
        self.timer = None
        if self.verbose: print("Change event triggered.")
        self.callback()

    def start_watching(self):
        self.file_observer.schedule(self, self.dir, recursive=True)
        self.file_observer.start()
        if self.verbose: print(f"Watching {self.dir!r}")

        try:
            while True:
                time.sleep(1)
        finally:
            self.file_observer.stop()
            self.file_observer.join()