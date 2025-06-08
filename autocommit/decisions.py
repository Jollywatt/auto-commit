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

DEFAULT_COMMIT_FREQ = """\
Don't commit if I only change a couple words.
But do commit before I delete a file or a lot of words, so I can get it back!
"""

DEFAULT_DETAIL_LEVEL = """\
Limit to one line or ten words.
"""

class ActionDecider:
    commit_freq = DEFAULT_COMMIT_FREQ
    detail_level = DEFAULT_DETAIL_LEVEL

    def __init__(self):
        pass

    def should_be_new_change(self, report):
        """
        Decide whether now is a good time to commit and start a new change.
        """

        if report['n_files_affected'] == 0: return False # no changs
        diff = report['gitdiff']

        prompt = f"""You are an automated reviewer whose sole job is to decide whether a set of changes is ready to be committed.
        User's commit frequency preference: {self.commit_freq!r}
        OUTPUT:
        - ONLY output "yes" or "no".
        - Do not output any other text, comments, or punctuation.
        Here is the diff:
        ```
        {diff}
        ```
        """

        decision = self.ask_gemini(prompt)
        print(decision.lower(), "yes" in decision.lower())
        return True if "yes" in decision.lower() else False
    
    def ask_gemini(self, prompt):
        url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"
        payload = {
            "contents": [
                {"parts": [{"text": f"{prompt}"}]}
            ]
        }
        headers = {'Content-Type': 'application/json'}

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

        prompt = f"You are a Git commit message assistant. Write a clear, concise,\
                imperative commit message based on the following staged diff.\
                Do not try to guess the user's intention.\
                Just state what changed.\
                Use present-tense verbs, don't repeat yourself.\
                User's requested level of detail: {self.detail_level!r}\
                Diff: {gitdiff}"
        try:
            return self.ask_gemini(prompt)

        except Exception as e:
            print(f"Gemini API error: {e}")
            return default_msg
