import os, re, datetime, time, signal, sys, requests
from decisions import GEMINI_API_URL, GEMINI_API_KEY

class SessionLogger:
    def __init__(self, repo_path, verbose=True):
        self.repo_path = repo_path
        self.verbose = verbose
        self.log_path = self._make_log_path()
        open(self.log_path, 'w').close()
        if self.verbose:
            print(f"[INFO] Logging session to {self.log_path!r}")
        signal.signal(signal.SIGINT, self._on_exit)

    def _make_log_path(self):
        logs_dir = os.path.join(self.repo_path, '.commit_logs')
        os.makedirs(logs_dir, exist_ok=True)

        today = datetime.date.today().strftime("%d_%m_%Y")
        pattern = re.compile(rf"session_{today}-(\d+)\.log$")
        existing = [
            int(m.group(1))
            for f in os.listdir(logs_dir)
            if (m := pattern.match(f))
        ]
        inst = max(existing or [0]) + 1
        return os.path.join(logs_dir, f"session_{today}-{inst}.log")

    def log_change(self, description: str):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_path, 'a') as f:
            f.write(f"[{ts}] {description}\n")

    def _on_exit(self, signum, frame):
        print("\n[INFO] Summarizing session before exit…")
        self._summarize_and_append()
        sys.exit(0)

    def _summarize_and_append(self):
        with open(self.log_path) as f:
            logtext = f.read()
        prompt = (
            "You are a code-review assistant. Here is today's session log:\n\n"
            f"{logtext}\n\nWrite a high-level summary in bullet points."
        )
        if GEMINI_API_KEY:
            try:
                resp = requests.post(
                    f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                    json={"contents":[{"parts":[{"text":prompt}]}]},
                    timeout=20
                )
                resp.raise_for_status()
                data = resp.json()
                summary = (data.get('candidates') or data.get('contents'))[0]['content']['parts'][0]['text']
            except Exception as e:
                summary = f"LLM summary error: {e}"
        else:
            summary = "No API key—skipping summary."

        with open(self.log_path, 'a') as f:
            f.write("\n=== Session Summary ===\n")
            f.write(summary + "\n")
        if self.verbose:
            print(f"[INFO] Session summary written to {self.log_path!r}")
