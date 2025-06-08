import subprocess
import os

class VCSHandler:
    def __init__(self, path):
        self.path = path

    def run_cmd(self, args):
        if type(args) is str: args = [args]
        cmd = [*self.basecmd, *args]
        result = subprocess.run(cmd, cwd=self.path, stdout=subprocess.PIPE)
        if result.returncode != 0:
            print("Error running", cmd)
            print(result.stderr.decode("utf-8"))
        return result.stdout.decode("utf-8")


class GitHandler(VCSHandler):
    basecmd = ['git']

    def repo_is_valid(self):
        git_dir = os.path.join(self.path, '.git')
        return os.path.isdir(git_dir)
    
    def init_repo(self):
        print(self.run_cmd('init'))

    def get_diff_summary(self):
        return self.run_cmd(['status', '--short'])

    def get_diff_details(self):
        return self.run_cmd('diff')
    
    def get_log(self):
        return self.run_cmd('log')

    def commit(self, message):
        self.run_cmd(['add', '-A'])
        self.run_cmd(['commit', '--message', message])

class JujutsuHandler(VCSHandler):
    basecmd = [
        'pixi', 'run', 'git',
        '--config', 'user.name=autocommit',
        '--config', 'user.email=autocommit'
    ]

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