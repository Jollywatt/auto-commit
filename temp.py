#!/usr/bin/env python3
"""
Auto-commit on file save with debounce using watchdog,
ignoring temporary files, swap files, and atomic save artifacts.
Integrates Gemini API to generate contextual commit messages based on staged diffs.

Requirements:
    pip install watchdog requests

Environment:
    Set GEMINI_API_KEY env var for authentication.
"""
import os
import subprocess
import time
import threading
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()

# Filename suffixes to ignore (swap, backup, temp)
IGNORE_SUFFIXES = ['.swp', '.swx', '~', '.tmp', '.temp']

# Gemini API endpoint and key
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class DebouncedHandler(FileSystemEventHandler):
    """
    Watch for file changes, but wait for a warmdown period
    for things to settle before triggering the change handler.
    """
    def __init__(self, callback, warmdown=1.0, verbose=True):
        self.warmdown = warmdown
        self.timer = None
        self.lock = threading.Lock()
        self.callback = callback
        self.verbose = verbose

    def on_any_event(self, event: FileSystemEvent):
        path = event.src_path
        # Skip directories, git internals, ignored suffixes, hidden, or no-ext
        if event.is_directory or '.git' in path:
            return
        name = os.path.basename(path)
        if name.startswith('.') or not os.path.splitext(name)[1]:
            return
        for suffix in IGNORE_SUFFIXES:
            if path.endswith(suffix):
                return

        with self.lock:
            if self.timer:
                self.timer.cancel()
                if self.verbose: print("Restarted debounce timer...")
            else:
                if self.verbose: print("Starting debounce timer...")
            # Store last event path for commit message context
            self.last_path = path
            self.timer = threading.Timer(self.warmdown, self._trigger)
            self.timer.start()

    def _trigger(self):
        self.timer = None
        if self.verbose: print("Debounce period over, triggering change handler.")
        # Call the provided callback with the path of last change
        self.callback(self.last_path)

class AutoCommitWorker:
    """
    Encapsulates the observer and commit logic, using a DebouncedHandler.
    """
    def __init__(self, repopath, warmdown=2.0):
        self.repopath = repopath
        self.observer = Observer()
        self.handler = DebouncedHandler(callback=self.handle_change,
                                        warmdown=warmdown)

    def start(self):
        self.observer.schedule(self.handler, self.repopath, recursive=True)
        self.observer.start()
        print(f"Watching {self.repopath} with debounce={self.handler.warmdown}s...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping watcher...")
            self.observer.stop()
        self.observer.join()

    def handle_change(self, path):
        # Stage changes
        subprocess.run(['git', 'add', '-A'], cwd=self.repopath, check=True)
        # Get staged diff
        diff_proc = subprocess.run(
            ['git', 'diff', '--cached'], cwd=self.repopath,
            stdout=subprocess.PIPE, text=True
        )
        diff_text = diff_proc.stdout
        # Generate commit message
        commit_msg = self.generate_commit_message(diff_text, path)
        # Commit
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=self.repopath, check=True)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {commit_msg}")


    def generate_commit_message(self, diff: str, path: str) -> str:
        """
        Summarize the diff into a commit message via Gemini API (using Google Generative Language).
        Falls back to a default message if API unavailable or on error.
        """
        filename = os.path.basename(path)
        default_msg = f"Auto-commit: modified {filename}"
        if not GEMINI_API_KEY:
            return default_msg
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"You are a Git commit message assistant. Write a clear, concise,\
                imperative commit message based on the following staged diff.\
                Focus on what changed and why, use present-tense verbs,\
                and limit the message to one to ten lines. Diff: {diff}"}]}
            ]
        }
        headers = {'Content-Type': 'application/json'}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            # Extract generated content
            parts = (
                data.get('candidates', [])
                or data.get('contents', [])
            )
            # Flatten to text
            text = parts[0]['content']['parts'][0]['text']
            return text
            # print(parts)
            # if parts and isinstance(parts[0], dict):
            #     # For beta API: candidates -> [{"content": ...}]
            #     text = parts[0].get('content') or parts[0].get('parts', [{}])[0].get('text')
            # if not text:
            #     return default_msg
            # # Return first line as commit message
            # return text.strip().split('\n')[0]
        except Exception as e:
            print(f"Gemini API error: {e}")
            return default_msg

def main():
    # Prompt for directory or use current
    repo = '/Users/ryanbarouki/Documents/Coding/test_auto_commit/' or os.getcwd()
    worker = AutoCommitWorker(repo)
    worker.start()

if __name__ == '__main__':
    main()
