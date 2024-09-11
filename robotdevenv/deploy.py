import re
import argparse
from pathlib import Path
import yaml
from robotdevenv.singleton import Singleton
from robotdevenv.constants import LOCAL_SRC_PATH
from robotdevenv.git import RobotDevRepository


class RobotDevDeployError(Exception):
    pass


class RobotDevDeploy(Singleton):

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        self.PATH_REPO: str = ''
        self.MANIFEST_PATH: str = ''
        self.COMPONENTS_PATH: str = ''
        self.LAST_VERSION_MAIN_REPO: str = ''
        self.NEW_VERSION: str = ''

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
        self.MANIFEST_PATH = self.PATH_REPO / 'manifest.yaml'
        self.COMPONENTS_PATH = self.PATH_REPO / 'components'

    def deploy_repository(self):

        repository: RobotDevRepository = self.__get_repo_from_path(
            self.PATH_REPO)

        # repository.fetching_repository()
        # repository.check_branch_name()
        # repository.check_changes_whitout_commit()
        # repository.check_local_and_remote_pointing_to_the_same_commit()
        # repository.check_if_commit_is_not_pointing_to_a_tag()
        # self.__last_tag_same_as_manifest(repository.get_all_tags())

        # self._subprocess_repository_dependencies()
        self.LAST_VERSION_MAIN_REPO = repository.get_all_tags()[-1]

        print(
            f'🏅 Last version {repository.repo_name}: {self.LAST_VERSION_MAIN_REPO}')

        self.__check_version_format()
        self.__check_version_order()
        self.__check_version_mayor()

        print('✅ Deploy Process Completed!')

    # Get repository from path and check if it exists
    def __get_repo_from_path(self, path_repo) -> RobotDevRepository:
        repository: RobotDevRepository = None
        try:
            repository: RobotDevRepository = RobotDevRepository(path_repo)
        except Exception as e:
            print(
                f'❌ Repository \'{path_repo}\' not found. Check if it exists in src folder.')
            exit()

        return repository

    def __last_tag_same_as_manifest(self, tags) -> None:

        if tags == []:
            print('❌ There are no tags in the repository.')
            exit()

        manifest: dict = {}
        version_manifest: str = ''

        # Get manifest file in the repo folder
        try:
            with open(self.MANIFEST_PATH, 'r') as file:
                manifest = yaml.safe_load(file)
        except FileNotFoundError:
            print(f'❌ File \'{self.MANIFEST_PATH}\' not found.')

        # Get manifest version
        version_manifest = manifest.get('version')
        if version_manifest == None:
            print('❌ File \'{self.MANIFEST_PATH}\' not have \'version\' key.')
            exit()

        # Check version from manifest file is the same as the last tag
        last_tag: str = tags[-1].name
        if version_manifest == last_tag:
            print(
                f'✅ The last tag: {last_tag}  is the same as {version_manifest} in the manisfes.yaml file')
        else:
            print(
                f'❌ The last tag: {last_tag} is not the same as {version_manifest} in the manisfes.yaml file')
            print('Exiting...')
            exit()

    def _subprocess_repository_dependencies(self) -> None:

        print(f'⚙️  DEPENDENCY PROCESS  ⚙️')

        folder_dependencies: list = self.__get_folders_dependencies()

        dependencies_yaml_files: list = self.__get_files_dependencies(
            folder_dependencies)

        dependencies_list: set[str] = self.__get_src_dependencies(
            dependencies_yaml_files)

        dependencies_repo_list: list = self.__get_dependency_repo_list(
            dependencies_list)

        self.__fetch_dependency_repo(dependencies_repo_list)

        self.__check_changes_whitout_commit(dependencies_repo_list)

        self.__check_pointing_to_tag(dependencies_repo_list)

    # Browse through the components folder and get all folders

    def __get_folders_dependencies(self) -> list:

        print(f'📂  Getting folders dependencies...')

        self.COMPONENTS_PATH
        path = Path(self.COMPONENTS_PATH)

        folder_list = [folder for folder in path.iterdir()
                       if folder.is_dir()]

        return folder_list

    # Browse through the every component folder looking for yaml files
    def __get_files_dependencies(self, folder_list_dependencies: list) -> list:

        print(f'📃  Getting files dependencies...')

        list_files_dependencies = []
        for folder in folder_list_dependencies:
            path: Path = Path(folder)

            # Get only yaml files
            for file in path.iterdir():
                if file.is_file() and (file.suffix == '.yaml' or file.suffix == '.yml'):
                    list_files_dependencies.append(file)
        return list_files_dependencies

    # Get src dependencies from yaml files. Return a list dependencies without duplicates
    def __get_src_dependencies(self, list_files_dependencies: list) -> list:

        src_dependencies_list: set[str] = set()  # A set to avoid duplicates

        try:
            for yaml_file in list_files_dependencies:
                with open(yaml_file, 'r') as file:
                    data: dict = yaml.safe_load(file)
                    src_dependencies: list = data.get('src')

                    if src_dependencies:
                        for dependency in src_dependencies:
                            src_dependencies_list.add(dependency)
        except Exception as e:
            print(f'❌ File \'{yaml_file}\' not found.')
            exit()

        # Remove the current repository from the list
        src_dependencies_list.remove(self.PATH_REPO.name)

        print(f'    📦 Dependencies found: {src_dependencies_list}')
        return src_dependencies_list

    def __get_dependency_repo_list(self, list_dependencies: set) -> list:

        print(f'🗄️  Getting list of dependency repositories...')

        repo_dependencies_list: list = []
        for dependency in list_dependencies:
            LOCAL_PATH_REPOSITORY = LOCAL_SRC_PATH / dependency
            repo_dependencies_list.append(
                self.__get_repo_from_path(LOCAL_PATH_REPOSITORY))

        return repo_dependencies_list

    def __fetch_dependency_repo(self, repo_dependencies_list: list[RobotDevRepository]) -> None:

        print(f'🔻  Fetching dependency repositories...')

        for repo in repo_dependencies_list:
            repo.fetching_repository()

    def __check_changes_whitout_commit(self, repo_dependencies_list: list[RobotDevRepository]) -> None:

        print(f'🟠  Check changes without commit...')

        for repo in repo_dependencies_list:
            repo.check_changes_whitout_commit()

    def __check_pointing_to_tag(self, repo_dependencies_list: list[RobotDevRepository]) -> None:

        print(f'🟡  Check pointing to tag...')

        for repo in repo_dependencies_list:
            print(f'    📦 Check if {repo.repo_name} is pointing to last Tag!')
            repo.check_if_commit_is_pointing_to_a_tag()

    def __check_version_format(self) -> None:

        print(f'🏷️  Check version format...')

        new_version: str = input(f'     ⌨ Please type the new version: ')
        pattern = r'^(\d+)\.(\d+)(\.beta)?$'
        coincidence = re.match(pattern, new_version)

        if coincidence is None:
            print('❌ Version format is not valid. Exiting...')
            exit()
        else:
            print('     🟢 Version format is valid!')
            self.NEW_VERSION = new_version

    def __get_version_tuple(self, version: str) -> tuple[int, int, bool]:

        pattern = r'^(\d+)\.(\d+)(\.beta)?$'
        coincidence = re.match(pattern, version)

        mayor = int(coincidence.group(1))
        minor = int(coincidence.group(2))
        is_beta = coincidence.group(3) is None

        return (mayor, minor, is_beta)

    def __check_version_order(self) -> None:

        print(f'🏷️  Check version order...')

        last_version_tuple = self.__get_version_tuple(str(
            self.LAST_VERSION_MAIN_REPO))
        new_version_tuple = self.__get_version_tuple(str(self.NEW_VERSION))

        # print(f'     ➡️  Last version: {last_version_tuple}')
        # print(f'     ➡️  New version: {new_version_tuple}')

        if new_version_tuple > last_version_tuple:
            print('     🟢 Version order is valid!')
        else:
            print('❌ Version order is not valid. Exiting...')
            exit()

    def __check_version_mayor(self) -> None:

        last_version_tuple = self.__get_version_tuple(str(
            self.LAST_VERSION_MAIN_REPO))
        new_version_tuple = self.__get_version_tuple(str(self.NEW_VERSION))

        if new_version_tuple[0] > last_version_tuple[0]:
            answer: str = input(
                'Are you sure you want to deploy this mayor version? (y/n): ')

            if answer == 'y':
                print('Continuing the deployment process...')
            else:
                print('Exiting...')
                exit()

    def __get_repo_from_path(self, path: Path) -> RobotDevRepository:
        return RobotDevRepository(path)
