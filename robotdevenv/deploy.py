import argparse
import git
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
        except Exception:
            print('No arguments provided or invalid arguments')
            RobotDevDeployError('❌ No arguments provided or invalid arguments')

        if not args.repo:
            print('Repository name not provided')
            RobotDevDeployError('❌ Repository name not provided')

        self.PATH_REPO = LOCAL_SRC_PATH / args.repo

    def deploy_repository(self):

        repository: RobotDevRepository = None
        try:
            repository: RobotDevRepository = RobotDevRepository(self.PATH_REPO)
        except Exception as e:
            print(
                f'❌ Repository \'{self.PATH_REPO}\' not found. Check if it exists in src folder.')
            exit()

        repository.fetching_repository()
        repository.check_branch_name()
        repository.check_changes_whitout_commit()
        repository.check_local_and_remote_pointing_to_the_same_commit()
        repository.check_if_commit_is_pointing_to_a_tag()
        print('✅ Deploy Process Completed!')
