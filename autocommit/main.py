import argparse
from watching import FileWatcher
from decisions import ActionDecider
from repos import GitHandler, JujutsuHandler
from logfile import SessionLogger
from frontend import FrontendServer, FrontendData


class AutoCommitWorker:
    def __init__(self, repopath, backend='git'):
        self.repopath = repopath
        self.watcher = FileWatcher(self.repopath, self.handle_change)
        self.decider = ActionDecider()
        self.logger = SessionLogger(self.repopath)

        Vcs = {'git': GitHandler, 'jj': JujutsuHandler}[backend]
        self.vcs = Vcs(self.repopath)
        if not self.vcs.repo_is_valid():
            self.vcs.init_repo()

        self.frontend = FrontendServer()
        self.frontend.onconnect = lambda ws: self.send_log_to_frontend()
        self.frontend.onmessgae = self.handle_message_from_frontend
        self.frontend.start()

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
            # self.logger.log_change(desc)
            self.send_log_to_frontend()

    def send_log_to_frontend(self):
        log = self.vcs.get_log()

        data = FrontendData(
            path=self.repopath,
            log=log,
            commit_freq=self.decider.commit_freq,
            detail_level=self.decider.detail_level,
        )
        self.frontend.send_data(data)

    def handle_message_from_frontend(self, json):
        if 'commit_freq' in json:
            print("Applied user's commit freq pereference.")
            self.decider.commit_freq = json['commit_freq']
        elif 'detail_level' in json:
            print("Applied user's detail level pereference.")
            self.decider.detail_level = json['detail_level']
        else:
            print("[WARNING]", json)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="Path to existing repository to watch.")
    parser.add_argument("--use-jj", action="store_true", help="Use jj instead of git for version control.")
    args = parser.parse_args()

    main = AutoCommitWorker(args.repo, backend='jj' if args.use_jj else 'git')
    main.start_watching()