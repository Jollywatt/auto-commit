import subprocess
import os

class VCSHandler:
    def __init__(self, path):
        self.path = path

class GitHandler(VCSHandler):
    def run_cmd(self, args: list[str] | str):
        if type(args) is str: args = [args]
        cmd = ['git', *args]
        result = subprocess.run(cmd, cwd=self.path, stdout=subprocess.PIPE)
        print(f"run: {cmd}")
        if result.stderr:
            print("Error:", result.stderr.decode("utf-8"))
        return result.stdout.decode("utf-8")

    def repo_is_valid(self):
        git_dir = os.path.join(self.path, '.git')
        return os.path.isdir(git_dir)
    
    def init_repo(self):
        print(self.run_cmd('init'))

    def get_diff_summary(self):
        return self.run_cmd(['status', '--short'])

    def get_diff_details(self):
        return self.run_cmd('diff')

    def commit(self, message):
        self.run_cmd(['add', '-A'])
        self.run_cmd(['commit', '--message', message])

class JujutsuHandler(VCSHandler):
    def run_cmd(self, args: list[str] | str):
        if type(args) is str: args = [args]
        result = subprocess.run(
            # run a jujutsu command using the jj binary in the virtual env
            ['pixi', 'run', 'git',
             '--config', 'user.name=autocommit',
             '--config', 'user.email=dummy@autocommit.org',
             *args],
            cwd=self.path,
            stdout=subprocess.PIPE,
        )
        print(f"run: jj {' '.join(args)}")
        return result.stdout.decode("utf-8")

    def repo_is_valid(self):
        jj_dir = os.path.join(self.path, '.jj')
        return os.path.isdir(jj_dir)
    
    def init_repo(self):
        # create a git-compatible jj repo
        print(self.run_jj_cmd(['git', 'init', '--colocate']))

    def get_diff_summary(self):
        return self.run_cmd(['diff', '--summary'])

    def get_diff_details(self):
        return self.run_cmd(['diff', '--git'])