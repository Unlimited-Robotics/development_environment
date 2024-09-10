import os
import yaml
import pathlib

from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot
from robotdevenv.docker import RobotDevDockerHandler as DockerHandler
from robotdevenv.singleton import Singleton
from robotdevenv.git import RobotDevGitHandler

from robotdevenv.constants import FILE_ROS_DOMAINS_PATH
from robotdevenv.constants import DEV_ENV_PATH
from robotdevenv.constants import FOLDER_CONFIG
from robotdevenv.constants import ROBOT_NAME
from robotdevenv.constants import ROBOT_BASE_PATH
from robotdevenv.constants import ROBOT_GENERIC_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_GENERIC_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_CONFIG_PATH
from robotdevenv.constants import ROBOT_COMMANDS_PATH
from robotdevenv.constants import ROBOT_BUILD_PATH
from robotdevenv.constants import ROBOT_SRC_PATH
from robotdevenv.constants import FOLDER_COMMANDS
from robotdevenv.constants import GLOBAL_CONFIG_PATH


class RobotDevRunError(Exception): pass


class RobotDevRunHandler(Singleton):

    def __init__(self,
                component:Component,
                robot:Robot,
            ):
        self.__component = component
        self.__robot = robot
        self.__docker_handler = DockerHandler(self.__component, self.__robot)


    def __update_env_from_file(self,
                env_vars: dict,
                path_env_file: pathlib.Path,
            ):
        with open(path_env_file, 'r') as file:
            for line in file:
                line = line.strip()
                line = line.replace(' ','')
                if (not line.startswith('#')) and ('=' in line):
                    key, value = line.split('=', 1)
                    env_vars[key] = value


    def run_command(self,
                command:str,
                interactive=False,
                detached_mode=False,
                config_origin=None,
            ):
        
        if config_origin is not None and \
                config_origin not in ['global', 'devenv', 'component']:
            raise RobotDevRunError(
                f'Configuration origin \'{config_origin}\' not valid.'
            )

        if(container_info := self.__docker_handler.get_running_container_info()) is None:

            # ROS Domain ID definition
            with open(FILE_ROS_DOMAINS_PATH, 'r') as file:
                ros_domain_ids = yaml.safe_load(file)
            git_email = RobotDevGitHandler.get_email()
            if git_email not in ros_domain_ids:
                raise RobotDevRunError(
                        f'{git_email} not defined in {FILE_ROS_DOMAINS_PATH}'
                    )
            ros_domain_id = ros_domain_ids[git_email]

            # Config folder definition
            config_path_global = GLOBAL_CONFIG_PATH
            config_path_devenv = DEV_ENV_PATH / FOLDER_CONFIG
            config_path_component = self.__component.local_path / FOLDER_CONFIG

            if config_origin=='global':
                config_path=config_path_global
                print('⚙️  Using global configuration folder:')
            elif config_origin=='devenv':
                if not config_path_devenv.is_dir():
                    raise RobotDevRunError(
                        f'Configuration folder not found in development '
                        'environment root folder'
                    )
                config_path=config_path_devenv
                print(
                    '⚙️  Using configuration folder from development environment:'
                )
            elif config_origin=='component':
                if not config_path_component.is_dir():
                    raise RobotDevRunError(
                        f'Configuration folder not found in component folder'
                    )
                config_path=config_path_component
                print('⚙️  Using configuration folder from component:')
            elif config_path_component.is_dir():
                config_path = config_path_component
                print('⚙️  Using configuration folder from component:')
            elif config_path_devenv.is_dir():
                config_path = config_path_devenv
                print(
                    '⚙️  Using configuration folder from development environment:'
                )
            print(f'   - {config_path}')
            print()

            # Env Definition
            env_vars_from_files = {}
            env_files_paths = []

            local_env_path = self.__component.local_path / 'env'
            if local_env_path.is_file():
                env_files_paths.append(local_env_path)
                self.__update_env_from_file(env_vars_from_files, local_env_path)

            local_env_path = DEV_ENV_PATH / FOLDER_CONFIG / 'env' / 'env'
            if local_env_path.is_file():
                env_files_paths.append(local_env_path)
                self.__update_env_from_file(env_vars_from_files, local_env_path)
            
            local_env_path = DEV_ENV_PATH / FOLDER_CONFIG / 'env' / \
                            f'{self.__component.container_name}.env'
            if local_env_path.is_file():
                env_files_paths.append(local_env_path)
                self.__update_env_from_file(env_vars_from_files, local_env_path)

            print('🌎 Using env files:')
            for env_file_path in env_files_paths:
                print(f'  - {env_file_path}')
            print()

            env_vars = {
                'IDHOST': self.__robot.name,
                'IDCOMPONENT': self.__component.name,
                'ROBOT_NAME': ROBOT_NAME,
            }

            if 'ROS_DOMAIN_ID' in env_vars_from_files:
                env_vars['ROS_DOMAIN_ID'] = env_vars_from_files['ROS_DOMAIN_ID']
                print('⚠️  Using \'ROS_DOMAIN_ID\' from files instead of static one.')
                print()
            else:
                env_vars['ROS_DOMAIN_ID'] = ros_domain_id

            # Volumes
            volumes = self.__component.get_volumes()
            volumes.append(
                (config_path, ROBOT_CONFIG_PATH, 'ro')
            )

            if (self.__component.local_path / FOLDER_COMMANDS).is_dir():
                volumes.append(
                    (self.__component.host_path / FOLDER_COMMANDS, ROBOT_COMMANDS_PATH)
                )

            self.__docker_handler.run_command(
                command=command,
                env_files=env_files_paths,
                env_vars=env_vars,
                volumes=volumes,
                interactive=interactive,
                detached_mode=detached_mode,
            )

        else:
            running_image = container_info['Config']['Image']
            if running_image == self.__component.image_dev_name:
                if not command:
                    command = 'bash'
                print(
                    f'ℹ️  Container \'{self.__component.container_name}\' already running, '
                    f'executing \'{command}\' inside it\n'
                )
                self.__docker_handler.exec_command(
                    command=command, 
                    interactive=interactive
                )
            else:
                raise RobotDevRunError(
                    f'Container \'{self.__component.container_name}\' '
                    'already running another version of the image: '
                    f'\'{running_image}\'.'
                )
