import os
import subprocess
import argparse
from watching import FileWatcher
from decisions import ActionDecider


class AutoCommitWorker:
    def __init__(self, repopath):
        self.repopath = repopath
        self.watcher = FileWatcher(self.repopath, self.handle_change)
        self.decider = ActionDecider()
        
        if not self.repo_is_valid():
            self.init_repo()
    
    def run_jj_cmd(self, args: list[str] | str):
        if type(args) is str: args = [args]
        result = subprocess.run(
            # run a jujutsu command using the jj binary in the virtual env
            ['pixi', 'run', 'jj', *args],
            cwd=self.repopath,
            stdout=subprocess.PIPE,
        )
        print(f"run: jj {' '.join(args)}")
        return result.stdout.decode("utf-8")

    def repo_is_valid(self):
        jj_dir = os.path.join(self.repopath, '.jj')
        return os.path.isdir(jj_dir)
    
    def init_repo(self):
        # create a git-compatible jj repo
        print(self.run_jj_cmd(['git', 'init', '--colocate']))

    def inspect_current_change(self):
        summary = self.run_jj_cmd(['diff', '--summary'])
        details = self.run_jj_cmd(['diff', '--git'])
        stats = self.run_jj_cmd(['diff', '--stat'])
    
        return {
            'n_files_affected': summary.count('\n'),
            'summary': summary,
            'details': details,
            'stats': stats,
        }
    
    def new_change(self):
        self.run_jj_cmd('new') # start a new commit

    def squash_change_with_last(self):
        self.run_jj_cmd('squash')

    def start_watching(self):
        self.watcher.start_watching()

    def handle_change(self):
        # Stage and commit
        report = self.inspect_current_change()
        
        if self.decider.should_be_new_change(report):
            self.new_change()
        else:
            self.squash_change_with_last()

        print(report)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Path to existing repository to watch.")
    args = parser.parse_args()

    main = AutoCommitWorker(args.repo)
    main.start_watching()