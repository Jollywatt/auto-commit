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

# Directory to watch (must be inside a Git repo)
PATH_TO_WATCH = "/Users/ryanbarouki/Documents/Coding/test_auto_commit/"
GIT_REPO = PATH_TO_WATCH

# Filename suffixes to ignore (swap, backup, temp)
IGNORE_SUFFIXES = ['.swp', '.swx', '~', '.tmp', '.temp']

class DebouncedCommitHandler(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a warmdown period
    before staging and committing changes.
    """
    def __init__(self, warmdown=1.0):
        self.warmdown = warmdown
        self.timer = None
        self.lock = threading.Lock()
        self.pending_event = None

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
            self.pending_event = event
            if self.timer:
                self.timer.cancel()
                print("Reset debounce timer...")
            else:
                print("Starting debounce timer...")
            self.timer = threading.Timer(self.warmdown, self.handle_change)
            self.timer.start()

    def handle_change(self):
        with self.lock:
            event = self.pending_event
            self.timer = None
            self.pending_event = None

        # Stage and commit
        name = os.path.basename(event.src_path)
        subprocess.run(['git', 'add', '-A'], cwd=GIT_REPO)

        diff_proc = subprocess.run(
            ['git', 'diff', '--cached'], cwd=GIT_REPO,
            stdout=subprocess.PIPE, text=True
        )
        diff_text = diff_proc.stdout

        msg = self.generate_commit_message(diff_text)
        msg = f"Auto-commit: modified {name}"
        subprocess.run(['git', 'commit', '-m', msg], cwd=GIT_REPO)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

    def generate_commit_message(self, diff):
        pass

if __name__ == '__main__':
    observer = Observer()
    handler = DebouncedCommitHandler(warmdown=2.0)
    observer.schedule(handler, path=PATH_TO_WATCH, recursive=True)
    observer.start()
    print(f"Watching {PATH_TO_WATCH}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
    observer.join()
