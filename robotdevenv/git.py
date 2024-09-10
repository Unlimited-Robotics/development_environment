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
        pass

    def __check_repository_existance(repo_path: str = None) -> tuple[git.Repo, git.Remote]:

        print(f'Checking if repository \'{repo_path}\' exists...')
        try:
            # Create object if the path is correct
            repo: git.Repo = git.Repo(repo_path)

            # Getting the repo url
            repo_url: git.Remote = repo.remotes.origin.url

        except git.InvalidGitRepositoryError:
            print(
                f'Repository \'{repo_path}\' not found. Check if it exists in src folder.')
            exit()
        except Exception as e:
            print(e)
            print(f'Exiting...')

        print(f'Repository \'{repo_path}\' found!')
        return repo, repo_url

    def fetching_repository(repo: git.Repo, repo_url: git.Remote):
        print(f'Fetching repository \'{repo_url}\'...')

        try:
            fetch_info: git.FetchInfo = repo.remotes.origin.fetch()

            for info in fetch_info:
                print(f'Fetched {info.ref} -> {info.commit}')

        except Exception as e:
            print(f'Could not fetch repository. {e}')
            print(f'Exiting...')

        print(f'Repository \'{repo_url}\' fetched!')

    def check_branch_name(self, repo: git.Repo, branch_name: str = 'main'):
        print(
            f'Checking if the repository is in the \'{branch_name}\' branch...')

        current_branch: str = repo.active_branch.name

        if current_branch != branch_name:
            print(
                'Current branch is not the main branch. Please checkout it. Exiting...')
            exit()

        print(f'You are in the \'{current_branch}\' branch!')

    def __check_changes_whitout_commit(self, repo: git.Repo):
        print('Checking if there are changes without commit...')

        if repo.is_dirty():
            print(
                f'There are uncommitted changes. Please commit them.')

            # Index = Stagging area.
            # Diff method compares the staggin area with the last confirmed commit in the repo
            # None = Last commit, we could compare with other commits
            for item in repo.index.diff(None):
                print(f'Changes without commit: {item.a_path}')
            print(f'Exiting!')
            exit()

        print('No changes without commit!')

    def __check_local_and_remote_pointing_to_the_same_commit(self, repo: git.Repo, branch_name: str = 'main'):

        local_branch = repo.heads[branch_name]
        local_commit = local_branch.commit.hexsha

        remote_branch = repo.remotes.origin.refs[branch_name]
        remote_commit = remote_branch.commit.hexsha

        if local_commit != remote_commit:
            print(
                'Local and remote branches are not pointing to the same commit. Exiting...')
            print(f'Local commit: {local_commit}')
            print(f'Remote commit: {remote_commit}')
            exit()

        print(
            f'Local and remote branches are pointing to the same commit! {local_commit}')

    def __check_if_commit_is_pointing_to_a_tag(self, repo: git.Repo, branch_name: str = 'main'):
        last_local_commit = repo.heads[branch_name].commit

        for tag in repo.tags:
            if tag.commit == last_local_commit:
                print('The last local commit is pointing to a tag. Exiting...')
                exit()

        print('The last local commit is not pointing to a tag!')
