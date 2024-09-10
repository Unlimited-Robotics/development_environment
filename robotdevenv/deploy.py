import argparse
from robotdevenv.singleton import Singleton
from robotdevenv.constants import LOCAL_SRC_PATH
from robotdevenv.git import RobotDevRepository


class RobotDevDeployError(Exception):
    pass


class RobotDevDeploy(Singleton):

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.PATH_REPO: str = ''

        args: argparse.Namespace = None
        try:
            parser: argparse.ArgumentParser = argparse.ArgumentParser()
            parser.add_argument('-r', '--repo', type=str, required=True)
            args = parser.parse_args()
        except:
            # print('No arguments provided or invalid arguments')
            RobotDevDeployError('No arguments provided or invalid arguments')

        if not args.repo:
            # print('Repository name not provided')
            RobotDevDeployError('Repository name not provided')

        self.PATH_REPO = LOCAL_SRC_PATH + args.repo

    def deploy_repository(self):

        repo = RobotDevRepository(self.PATH_REPO)
        # repo, repo_url = check_repository_existance(PATH_REPO)
        # fetching_repository(repo, repo_url)
        # check_branch_name(repo)
        # check_changes_whitout_commit(repo)
        # check_local_and_remote_pointing_to_the_same_commit(repo)
        # check_if_commit_is_pointing_to_a_tag(repo)
        # print('Deploy Process Completed!')
