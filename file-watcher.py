#!/usr/bin/env python3
"""
Auto-commit on file save with debounce using watchdog,
ignoring temporary files, swap files, and atomic save artifacts.

This script watches a directory for file modifications and automatically
stages and commits changes to Git after a warmdown period, filtering out
nuisance files and only committing 'real' files with extensions.

"""
import os
import subprocess
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler

# Filename suffixes to ignore (swap, backup, temp)
IGNORE_SUFFIXES = ['.swp', '.swx', '~', '.tmp', '.temp']


class DebouncedHandler(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a warmdown priod
    for things to settle before triggering the change handler.
    """
    def __init__(self, callback, warmdown=1.0):
        self.warmdown = warmdown
        self.timer = None
        self.lock = threading.Lock()
        self.verbose = True
        self.callback = callback

    def on_any_event(self, event: FileSystemEvent):
        path = event.src_path
        # Skip directories, git internals, ignored suffixes, hidden, or no-ext
        if event.is_directory or '.git' in path:
            return
        name = os.path.basename(path)
        if name.startswith('.'):
            return
        if not os.path.splitext(name)[1]:
            return
        for suffix in IGNORE_SUFFIXES:
            if path.endswith(suffix):
                return
            
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
        self.callback()


class AutoCommitWorker:
    def __init__(self, repopath):
        self.repopath = repopath
        self.change_observer = Observer()
        self.change_handler = DebouncedHandler(self.handle_change)
    
    def start_watching(self):
        self.change_observer.schedule(self.change_handler, self.repopath, recursive=True)
        self.change_observer.start()

        try:
            while True:
                time.sleep(1)
        finally:
            self.change_observer.stop()
            self.change_observer.join()

    def handle_change(self):
        # Stage and commit
        report = self.inspect_current_change()
        print(report)

    def inspect_current_change(self):
        result = subprocess.run([
            'pixi', 'run', 'jj', 'diff',
            '--repository', self.repopath,
            '--summary',
        ], stdout=subprocess.PIPE)
        return result.stdout.decode("utf-8")


def main():
    main = AutoCommitWorker("./demo")
    main.start_watching()

if __name__ == '__main__':
    main()