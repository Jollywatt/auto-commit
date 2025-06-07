#!/usr/bin/env python3
import os
import time
import threading
from termcolor import cprint
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

# Filename suffixes to ignore (swap, backup, temp)
IGNORE_SUFFIXES = ['.swp', '.swx', '~', '.tmp', '.temp']

class FileWatcher(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a cooldown priod
    for things to settle before triggering the change handler.
    """
    def __init__(self, dir, callback, cooldown=1):
        self.dir = dir # directory to watch
        self.callback = callback # to call after file event
        self.cooldown = cooldown # minimum delay after event before callback

        self.file_observer = Observer()
        self.timer = None
        self.lock = threading.Lock()
        self.verbose = True

    def info(self, message):
        if self.verbose:
            cprint(message, "dark_grey")

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
                self.info("Restarted cooldown timer...")
            else:
                self.info("Starting cooldown timer...")
            self.timer = threading.Timer(self.cooldown, self.handle_change)
            self.timer.start()

    def handle_change(self):
        self.info("Change event triggered.")
        self.callback()
        self.timer = None
        self.info("Finished handling; watching...")

    def start_watching(self):
        self.file_observer.schedule(self, self.dir, recursive=True)
        self.file_observer.start()
        self.info(f"Watching {self.dir!r}")

        try:
            while True:
                time.sleep(1)
        finally:
            self.file_observer.stop()
            self.file_observer.join()