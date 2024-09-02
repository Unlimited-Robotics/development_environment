import yaml
import pathlib
import argparse

from robotdevenv.ssh import RobotDevSSHHandler as SSHHandler
from robotdevenv.environment import DEV_ENV_PATH


LOCALHOST_DEFAULT_PLATFORM = 'x86_64'
ROBOTS_INFO_FILE_NAME = 'robots.yaml'


class RobotDevRobotError(Exception): pass


class RobotDevRobot:

    def __init__(self, 
                parser:argparse.ArgumentParser
            ):
        parser.add_argument('-r', '--robot', type=str, required=True)
        args = dict(parser.parse_known_args()[0]._get_kwargs())
        name = args['robot']
        is_local = (name=='localhost')

        if is_local:
            platform = LOCALHOST_DEFAULT_PLATFORM
        else:
            robots_host_info_file_path = DEV_ENV_PATH / ROBOTS_INFO_FILE_NAME

            try:
                with open(robots_host_info_file_path, 'r') as file:
                    robots_host_info = yaml.safe_load(file)
            except FileNotFoundError:
                raise RobotDevRobotError(
                    f'File \'{ROBOTS_INFO_FILE_NAME}\' not found.'
                )
            
            try:
                robot_host_info = robots_host_info[name]
            except KeyError:
                raise RobotDevRobotError(
                    f'Robot \'{name}\' not found in file '
                    f'\'{ROBOTS_INFO_FILE_NAME}\'.'
                )
            
            try:
                platform = robot_host_info['platform']
            except KeyError as field:
                raise RobotDevRobotError(
                    f'Field \'{field}\' not found for robot \'{name}\' in '
                    f'file \'{ROBOTS_INFO_FILE_NAME}\'.'
                )
        
        # Public attributes
        self.name = name
        self.is_local = is_local
        self.platform = platform


    def get_remote_home(self):
        return pathlib.Path(SSHHandler.run_remote_get_output(
            host_alias=self.name,
            command='echo \'$HOME\'',
        ))
