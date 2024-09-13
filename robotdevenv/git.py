import git
import pathlib
import subprocess

from robotdevenv.constants import DEPLOY_BRANCH


class RobotDevGitError(Exception): pass


class RobotDevGitHandler:

    def get_email():
        try:
            return subprocess.check_output(
                ['git', 'config', 'user.email']
            ).decode().strip()

        except subprocess.CalledProcessError as e:
            raise RobotDevGitError(
                'Can not get git email, make sure you already defined it'
            )


class RobotDevRepositoryHandler:

    def __init__(self, 
                repo_path: pathlib.Path,
            ):
        repo_name = repo_path.name

        try:
            # Create object if the path is correct
            repo = git.Repo(repo_path)
            # Getting the repo url
            repo_url:git.Remote = repo.remotes.origin.url
        except git.exc.NoSuchPathError as e:
            raise RobotDevGitError(
                f'Repository \'{repo_name}\' not found. Check if it exists in '
                'src folder.'
            )
        
        # Public attributes
        self.repo_name = repo_name
        self.repo = repo
        self.repo_url = repo_url


    def fetch(self):
        self.repo.remotes.origin.fetch()


    def assert_deploy_branch(self, branch_name: str = DEPLOY_BRANCH):
        if self.repo.active_branch.name != branch_name:
            raise RobotDevGitError(
                f'Repository \'{self.repo_name}\' not in branch '
                f'\'{DEPLOY_BRANCH}\'.'
            )


    def assert_no_local_changes(self):
        if self.repo.is_dirty():
            print(f'There are uncommitted changes.')
            raise RobotDevGitError(
                f'Repository \'{self.repo_name}\' has uncommited changes.'
            )


    def assert_branch_updated(self, branch_name: str = DEPLOY_BRANCH):
        local_commit = self.repo.heads[branch_name].commit.hexsha
        remote_commit = \
            self.repo.remotes.origin.refs[branch_name].commit.hexsha
        if local_commit != remote_commit:
            raise RobotDevGitError(
                f'Branch \'{DEPLOY_BRANCH}\' of repo \'{self.repo_name}\' not '
                'updated with the remote.'
            )
        

    def get_tags(self):
        if not self.repo.tags:
            raise RobotDevGitError(
                f'Repository \'{self.repo_name}\' does not have tags.'
            )
        return self.repo.tags


    def get_last_tag(self):
        return self.get_tags()[-1]


    def is_pointing_to_tag(self, branch_name: str = DEPLOY_BRANCH):
        last_local_commit = self.repo.heads[branch_name].commit
        last_tag: git.Tag = self.get_last_tag()
        return last_tag.commit == last_local_commit


    def assert_no_pointing_to_tag(self, branch_name: str = DEPLOY_BRANCH):
        if self.is_pointing_to_tag():
            raise RobotDevGitError(
                f'Repository \'{self.repo_name}\' pointing to a tag.'
            )


    def assert_pointing_to_tag(self):
        if not self.is_pointing_to_tag():
            raise RobotDevGitError(
                f'Repository \'{self.repo_name}\' not pointing to a tag.'
            )
        


    def create_commit(self, message: str):
        print(f'    📩 Creating commit with message: {message}')
        self.repo.git.add(all=True)
        self.repo.index.commit(message)


    def create_tag(self, tag_name: str):
        print(f'    🏷  Creating tag: {tag_name}')
        self.repo.create_tag(tag_name)


    def push_repository(self):
        print('    🚀 Pushing repository...')
        self.repo.remotes.origin.push()
        self.repo.remotes.origin.push(tags=True)
