"""
This file contains logic related to
- deciding whether to start a new commit
- describing commits
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

class ActionDecider:
    def __init__(self):
        pass

    def should_be_new_change(self, report):
        """
        Decide whether now is a good time to commit and start a new change.
        """

        if report['n_files_affected'] == 0: return False # no changs

        return True
    
    def describe_change(self, report):
        """
        Summarize the diff into a commit message via Gemini API (using Google Generative Language).
        Falls back to a default message if API unavailable or on error.
        """
        summary = report['summary']
        gitdiff = report['gitdiff']

        default_msg = f"Auto-commit: \n{summary}"
        if not GEMINI_API_KEY:
            return default_msg
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"You are a Git commit message assistant. Write a clear, concise,\
                imperative commit message based on the following staged diff.\
                Focus on what changed and why, use present-tense verbs,\
                and limit the message to one to ten lines. Diff: {gitdiff}"}]}
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

        except Exception as e:
            print(f"Gemini API error: {e}")
            return default_msg
