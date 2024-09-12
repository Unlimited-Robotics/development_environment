import os
import re
import argparse
import yaml
import paramiko
import paramiko.ssh_exception
import xml.etree.ElementTree as xmlObj
import lxml.etree
from pathlib import Path
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
            raise RobotDevDeployError(
                '❌ No arguments provided or invalid arguments')

        if not args.repo:
            raise RobotDevDeployError('❌ Repository name not provided')

        self.PATH_REPO = LOCAL_SRC_PATH / args.repo
        self.MANIFEST_PATH = self.PATH_REPO / 'manifest.yaml'
        self.COMPONENTS_PATH = self.PATH_REPO / 'components'

    def deploy_repository(self):

        repository: RobotDevRepository = RobotDevRepository(self.PATH_REPO)
        repository.fetching_repository()
        repository.check_branch_name()
        repository.check_changes_whitout_commit()
        repository.check_local_and_remote_pointing_to_the_same_commit()
        repository.check_if_commit_is_not_pointing_to_a_tag()
        self.__last_tag_same_as_manifest(repository.get_all_tags())

        self.__subprocess_repository_dependencies()

        self.LAST_VERSION_MAIN_REPO = repository.get_all_tags()[-1]
        print(
            f'🏅 Last version {repository.repo_name}: {self.LAST_VERSION_MAIN_REPO}')

        # self.__check_version_format()
        # self.__check_version_order()
        # self.__check_version_mayor()
        # self.__check_building_host_available()
        # self.__update_manifest()
        # self.__update_packages_xml()
        # repository.create_commit(self.NEW_VERSION)
        # repository.create_tag(self.NEW_VERSION)
        # repository.push_repository()

        print()
        print('🎉🎉 Deploy Process Completed! 🎉🎉')

    def __last_tag_same_as_manifest(self, tags) -> None:

        if tags == []:
            raise RobotDevDeployError('❌ There are no tags in the repository.')

        manifest: dict = {}
        version_manifest: str = ''

        # Get manifest file in the repo folder
        try:
            with open(self.MANIFEST_PATH, 'r') as file:
                manifest = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevDeployError(
                f'❌ File \'{self.MANIFEST_PATH}\' not found.'
            )

        # Get manifest version
        version_manifest = manifest.get('version')
        if version_manifest == None:
            raise RobotDevDeployError(
                '❌ File \'{self.MANIFEST_PATH}\' not have \'version\' key.'
            )

        # Check version from manifest file is the same as the last tag
        last_tag: str = tags[-1].name
        if version_manifest == last_tag:
            print(
                f'✅ The last tag: {last_tag}  is the same as {version_manifest} in the manisfes.yaml file')
        else:
            raise RobotDevDeployError(
                f'❌ The last tag: {last_tag} is not the same as {version_manifest} in the manisfes.yaml file')

    def __subprocess_repository_dependencies(self) -> None:

        print()
        print(f'⚙️  DEPENDENCY PROCESS  ⚙️')
        print()

        folder_dependencies: list = self.__get_folders_dependencies()

        dependencies_yaml_files: list = \
            self.__get_files_dependencies(folder_dependencies)

        dependencies_list: set[str] = \
            self.__get_src_dependencies(dependencies_yaml_files)

        dependencies_repo_list: list = \
            self.__get_dependency_repo_list(dependencies_list)

        self.__fetch_dependency_repo(dependencies_repo_list)

        self.__check_changes_whitout_commit(dependencies_repo_list)

        self.__check_pointing_to_tag(dependencies_repo_list)

        print()

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
                    # Check if the yaml file has the same name as the folder
                    file_name_without_extension = file.name.split('.')[0]
                    if folder.name != file_name_without_extension:
                        raise RobotDevDeployError(
                            f'❌ The yaml file \033[1m{file_name_without_extension}\033[0m does not have the same name as the folder \033[1m{folder.name}\033[0m')
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
            raise RobotDevDeployError(f'❌ File \'{yaml_file}\' not found.')

        # Remove the current repository from the list
        src_dependencies_list.remove(self.PATH_REPO.name)

        print(f'    📦 Dependencies found: {src_dependencies_list}')
        return src_dependencies_list

    def __get_dependency_repo_list(self, list_dependencies: set) -> list:

        print(f'🗄️  Getting list of dependency repositories...')

        repo_dependencies_list: list = []
        for dependency in list_dependencies:
            LOCAL_PATH_REPOSITORY = LOCAL_SRC_PATH / dependency
            repo_dependency = RobotDevRepository(LOCAL_PATH_REPOSITORY)
            repo_dependencies_list.append(repo_dependency)

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

        print(f'🟡  Check dependencies pointing to tag...')

        for repo in repo_dependencies_list:
            print(f'    📦 Check if {repo.repo_name} is pointing to a Tag!')
            repo.check_if_commit_is_pointing_to_a_tag()

    def __check_version_format(self) -> None:

        print(f'🏷️  Check version format...')

        new_version: str = input(f'     ⌨ Please type the new version: ')
        pattern = r'^(\d+)\.(\d+)(\.beta)?$'
        coincidence = re.match(pattern, new_version)

        if coincidence is None:
            raise RobotDevDeployError(
                '❌ Version format is not valid. Exiting...')
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
            raise RobotDevDeployError(
                '❌ Version order is not valid. Exiting...')

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

    def __check_building_host_available(self):

        print(f'🏗️  Check building host available...')

        available_hosts: list[str] = self.__get_ssh_hosts()
        available_hosts.sort()

        print(f'     🕹️ Available hosts:')
        for host in available_hosts:
            print(f'     - {host}')

        build_host: str = input(
            f'     ⌨ Please enter the name of the building host: ')

        if build_host not in available_hosts:
            raise RobotDevDeployError(
                f'❌ Host {build_host} not found. Exiting...')

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()

        ssh_config = paramiko.SSHConfig()
        user_config_file = os.path.expanduser("~/.ssh/config")

        with open(user_config_file) as f:
            ssh_config.parse(f)

        config = ssh_config.lookup(build_host)

        if config is not None:
            try:
                host = config.get("hostname")
                user = config.get("user")
                ssh.connect(hostname=host, username=user)
                print(f'     🟢 Host {build_host}, {host} available!')
                ssh.close()
            except paramiko.ssh_exception.NoValidConnectionsError:
                raise RobotDevDeployError(
                    f'❌ Unable to connect to host {build_host}. Host: {host}, User: {user}')
            except paramiko.ssh_exception.AuthenticationException:
                raise RobotDevDeployError(
                    f'❌ Authentication failed for host {build_host}. Exiting...')
            except paramiko.ssh_exception.PasswordRequiredException:
                raise RobotDevDeployError(
                    f'❌ Password required for host {build_host}. Exiting...')
            except Exception:
                raise RobotDevDeployError(
                    f'❌ Host {build_host} not found. Exiting...')
            finally:
                ssh.close()

    def __get_ssh_hosts(self) -> list[str]:
        # print(f'🔑  Get ssh hosts...')

        ssh_config = paramiko.SSHConfig()
        try:
            user_config_file = os.path.expanduser("~/.ssh/config")
            with open(user_config_file) as f:
                ssh_config.parse(f)

        except Exception:
            raise RobotDevDeployError(
                '❌ SSH config file not found. Exiting...')

        # Getting hosts from the config file
        hosts: list[str] = [
            host for host in ssh_config.get_hostnames()]

        # Removing wildcards
        hosts = [host for host in hosts if '*' not in host]

        return hosts

    def __update_manifest(self) -> None:

        print(f'🔺  Update manifest file...')

        manifest: dict = {}

        # Get manifest file in the repo folder
        try:
            with open(self.MANIFEST_PATH, 'r') as file:
                manifest = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevDeployError(
                f'❌ File \'{self.MANIFEST_PATH}\' not found.')

        # Update manifest version
        if self.NEW_VERSION != '':
            manifest['version'] = self.NEW_VERSION
            with open(self.MANIFEST_PATH, 'w') as file:
                yaml.dump(manifest, file)

            print('     🟢 Manifest file updated.')
        else:
            raise RobotDevDeployError('❌ New version is empty. Exiting...')

    def __update_packages_xml(self) -> None:

        print(f'🔺  Update all packages.xml...')

        if self.NEW_VERSION == '':
            raise RobotDevDeployError('❌ New version is empty. Exiting...')

        path = Path(self.PATH_REPO)

        # Get list of package xml files
        list_path_packages_xml_files: list = []
        for folder in path.iterdir():
            if folder.is_dir() and not folder.name.endswith('.git') and not folder.name.startswith('components'):
                list_path_packages_xml_files.append(folder / 'package.xml')

        if len(list_path_packages_xml_files) == 0:
            raise RobotDevDeployError(
                '❌ No package.xml files found. Exiting...')

        for file in list_path_packages_xml_files:
            parser = lxml.etree.XMLParser(remove_blank_text=True)
            tree = lxml.etree.parse(file, parser)
            root = tree.getroot()

            version_tag = root.find('version')
            if version_tag is not None:
                version_tag.text = self.NEW_VERSION
                xml_str = lxml.etree.tostring(tree, pretty_print=True,
                                              xml_declaration=True,
                                              encoding='utf-8'
                                              ).decode("utf-8")

                xml_str = xml_str.replace(" encoding='utf-8'", '').strip()

                with open(file, 'w') as f:
                    f.write(xml_str)

        print('     🟢 All packages.xml updated.')
