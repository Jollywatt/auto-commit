import os
import subprocess
import argparse
from watching import FileWatcher
from decisions import ActionDecider
from repos import GitHandler


class AutoCommitWorker:
    def __init__(self, repopath):
        self.repopath = repopath
        self.watcher = FileWatcher(self.repopath, self.handle_change)
        self.decider = ActionDecider()
        self.vcs = GitHandler(self.repopath)
        
        if not self.vcs.repo_is_valid():
            self.vcs.init_repo()


    def inspect_current_change(self):
        summary = self.vcs.get_diff_summary()
        gitdiff = self.vcs.get_diff_details()
    
        return {
            'n_files_affected': summary.count('\n'),
            'summary': summary,
            'gitdiff': gitdiff,
        }
    

    def start_watching(self):
        self.watcher.start_watching()

    def handle_change(self):
        # Stage and commit
        report = self.inspect_current_change()
        
        if self.decider.should_be_new_change(report):
            desc = self.decider.describe_change(report)

            print(f"Description from Gemini:\n{desc}\n~")
            self.vcs.commit(message=desc)





if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Path to existing repository to watch.")
    args = parser.parse_args()

    main = AutoCommitWorker(args.repo)
    main.start_watching()