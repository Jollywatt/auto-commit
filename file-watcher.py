import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Choose a directory to watch (e.g., your Git repo root)
PATH_TO_WATCH = "/Users/ryanbarouki/Documents/Coding/test_auto_commit/"
GIT_REPO = "/Users/ryanbarouki/Documents/Coding/test_auto_commit/"

# Filename suffixes to ignore (swap, backup, temp files)
IGNORE_SUFFIXES = [
    '.swp',   # Vim swap
    '.swx',   # Vim backup
    '~',      # Emacs/Vim backup
    '.tmp',   # Generic temp
    '.temp',  # Generic temp
]

class CommitOnSaveHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Ignore directories and Git internals
        path = event.src_path
        if event.is_directory or '.git' in event.src_path:
            return
        for suffix in IGNORE_SUFFIXES:
            if path.endswith(suffix):
                return
        # Skip hidden files
        name = os.path.basename(path)
        if name.startswith('.'):
            return
        # Skip files without an extension (e.g., atomic save temp files)
        _, ext = os.path.splitext(name)
        if not ext:
            return
        # Stage all changes
        subprocess.run(['git', 'add', '-A'], cwd=GIT_REPO)
        # Commit with a simple message
        msg = f"Auto-commit: modified {event.src_path}"
        subprocess.run(['git', 'commit', '-m', msg], cwd=GIT_REPO)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

if __name__ == '__main__':
    observer = Observer()
    handler = CommitOnSaveHandler()
    observer.schedule(handler, path=PATH_TO_WATCH, recursive=True)
    observer.start()
    print(f"Watching for modifications in {PATH_TO_WATCH}...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher...")
        observer.stop()
    observer.join()
