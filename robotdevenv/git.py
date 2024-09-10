import subprocess
import git


class RobotDevGitError(Exception):
    pass


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


class RobotDevRepository:

    def __init__(self, repo_path: str) -> None:

        self.repo: git.Repo = None
        self.repo_url: git.Remote = None
        self.repo_name = repo_path.name

        # print(f'  🔎  Checking if repository \'{repo_path}\' exists...')
        print(f'    🔎  Checking if repository \'{self.repo_name}\' exists...')
        # Create object if the path is correct
        self.repo = git.Repo(repo_path)

        # Getting the repo url
        self.repo_url = self.repo.remotes.origin.url

        # print(f'  👍 Repository \'{repo_path}\' found!')
        print(f'    👍 Repository \'{self.repo_name}\' found!')

    def fetching_repository(self):
        print(f'🔵  Fetching repository \'{self.repo_url}\'...')

        try:
            fetch_info: git.FetchInfo = self.repo.remotes.origin.fetch()

            for info in fetch_info:
                print(f'   📩 Fetched {info.ref} -> {info.commit}')

        except Exception as e:
            print(f'❌ Could not fetch repository. {e}')
            print(f'❌ Exiting...')

        print(f'   🟢 Repository fetched!')

    def check_branch_name(self, branch_name: str = 'main'):
        print(
            f'ℹ️  Checking if the repository is in the \'{branch_name}\' branch...')

        current_branch: str = self.repo.active_branch.name

        if current_branch != branch_name:
            print(
                '❌ Current branch is not the main branch. Please checkout it. Exiting...')
            exit()

        print(f'✅ You are in the \'{current_branch}\' branch!')

    def check_changes_whitout_commit(self):
        print('    🔎  Checking if there are changes without commit...')

        if self.repo.is_dirty():
            print(
                f'❌ There are uncommitted changes. Please commit them.')

            # Index = Stagging area.
            # Diff method compares the staggin area with the last confirmed commit in the repo
            # None = Last commit, we could compare with other commits
            for item in self.repo.index.diff(None):
                print(f'    🔎 Changes without commit: {item.a_path}')
            print(f'Exiting!')
            exit()

        print('    🟢 No changes without commit!')

    def check_local_and_remote_pointing_to_the_same_commit(self, branch_name: str = 'main'):

        local_branch = self.repo.heads[branch_name]
        local_commit = local_branch.commit.hexsha

        remote_branch = self.repo.remotes.origin.refs[branch_name]
        remote_commit = remote_branch.commit.hexsha

        if local_commit != remote_commit:
            print(
                '❌ Local and remote branches are not pointing to the same commit. Exiting...')
            print(f'    ➡️  Local commit: {local_commit}')
            print(f'    ➡️  Remote commit: {remote_commit}')
            exit()

        print(
            f'✅ Local and remote branches are pointing to the same commit! {local_commit}')

    # To check if the last local commit in the main branch is NOT pointing to a tag
    def check_if_commit_is_not_pointing_to_a_tag(self, branch_name: str = 'main'):

        if len(self.repo.tags) == 0:
            print(f'    ❌ There are no tags in the repository.')
            print(f'Exiting...')
            exit()

        last_local_commit = self.repo.heads[branch_name].commit
        last_tag: git.Tag = self.repo.tags[-1]

        if last_tag.commit == last_local_commit:
            print(f'    ❌ The last local commit is pointing to a tag.')
            print(f'        ➡️  Tag {last_tag}.')
            print(f'Exiting...')
            exit()

        print('✅ The last local commit is not pointing to a tag!')

    # To check if the last local commit in the current branch is pointing to a last tag
    def check_if_commit_is_pointing_to_a_tag(self):

        if len(self.repo.tags) == 0:
            print(f'    ❌ There are no tags in the repository.')
            print(f'Exiting...')
            exit()

        current_branch = self.repo.active_branch.name
        last_local_commit = self.repo.heads[current_branch].commit

        last_tag = self.repo.tags[-1]

        if last_tag.commit != last_local_commit:
            print(f'    ❌ The last local commit is not pointing to a tag.')
            print(f'        ➡️  Last tag: {last_tag}.')
            print(f'Exiting...')
            exit()

        print('✅ The last local commit is pointing to a tag!')

    def get_all_tags(self):
        if len(self.repo.tags) == 0:
            return []
        return self.repo.tags
