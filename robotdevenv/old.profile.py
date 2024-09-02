import argparse
import yaml
import dataclasses
from robotdevenv.git import get_git_email
from typing import List, Tuple

from robotdevenv.environment import get_environment


DIR_DEV_PROFILES = \
    get_environment().dev_env_path / 'profiles'
DIR_DEV_COMPONENTS = \
    get_environment().dev_env_path / 'components'
FILE_LOCAL_CONFIG = get_environment().dev_env_path / 'local_config.yaml'
FILE_ROBOTS = get_environment().dev_env_path / 'robots.yaml'

VALID_BUILD_TYPES = ['devel', 'prod']


class RobotDevProfileError(Exception): pass


@dataclasses.dataclass
class RobotDevComponent:
    component: str
    platform: str
    host_ip: str
    host_user: str
    ssh_port: int
    ros_pkgs: List[str]
    src: List[str]
    display: bool
    sound: bool
    devices: bool


GARY_COMPONENT_DEFAULT_VALUES = {
    'host_user': 'user',
    'ssh_port': 22,
    'ros_pkgs': [],
    'src': [],
    'display': False,
    'sound': False,
    'devices': False,
}


@dataclasses.dataclass
class RobotDevProfile:
    components: List[RobotDevComponent]


@dataclasses.dataclass
class RobotDevLocalConfig:
    robot: str
    profile: str
    build_type: str
    workspace: str


LOCAL_CONFIGS_LIST = [f.name for f in dataclasses.fields(RobotDevLocalConfig)]


def get_dev_profile(
            profile:str=None,
            update_config_file:bool=True,
        ) -> Tuple[RobotDevProfile, RobotDevLocalConfig]:
    
    available_profiles = [
            folder.name 
            for folder in DIR_DEV_PROFILES.iterdir() 
            if folder.is_dir()
        ]

    try:
        with open(FILE_LOCAL_CONFIG, 'r') as file:
            local_config = yaml.safe_load(file)
    except FileNotFoundError:
        local_config = {
                'robot': None,
                'profile': None,
                'build_type': 'devel',
                'workspace': get_git_email().split('@')[0],
            }
        
    if profile is not None:
        local_config['profile'] = profile

    parser = argparse.ArgumentParser()
    for field in LOCAL_CONFIGS_LIST:
        parser.add_argument(f'--{field}', type=str, required=False)
    args = dict(parser.parse_known_args()[0]._get_kwargs())

    for field in LOCAL_CONFIGS_LIST:
        if args[field] is not None:
            local_config[field] = args[field]

        if local_config[field] is None:
            raise RobotDevProfileError(
                    f'Config \'{field}\' not in \'{FILE_LOCAL_CONFIG}\', '
                    f'so it must be set as command argument.'
                )

    if local_config['profile'] not in available_profiles:
        raise RobotDevProfileError(
                f'Profile \'{local_config["profile"]}\' not found.'
            )
    
    if local_config['build_type'] not in VALID_BUILD_TYPES:
        raise RobotDevProfileError(
                f'Build type \'{local_config["build_type"]}\' not valid.'
            )

    if update_config_file:
        with open(FILE_LOCAL_CONFIG, 'w') as file:
            yaml.dump(local_config, file, default_flow_style=False)

    with open(FILE_ROBOTS) as file:
        robots_file_dict = yaml.safe_load(file)
    robot_config = robots_file_dict[local_config['robot']]

    profile_name = local_config['profile']
    print(f'👤 Working profile: \'{profile_name}\'')

    with open(DIR_DEV_PROFILES / f'{profile_name}' \
                / f'{profile_name}.yaml', 'r'
            ) as file:
        dev_profile_dict = yaml.safe_load(file)
    dev_profile = RobotDevProfile(components=[])
    for component in dev_profile_dict['components']:
        for robot_key in robot_config:
            if robot_key not in component:
                component[robot_key] = robot_config[robot_key]
        for default_key in GARY_COMPONENT_DEFAULT_VALUES:
            if default_key not in component:
                component[default_key] = \
                    GARY_COMPONENT_DEFAULT_VALUES[default_key]

        try:
            component_yaml = DIR_DEV_COMPONENTS / component["component"] / f'{component["component"]}.yaml'
            with open(component_yaml, 'r') as file:
                dev_component_dict = yaml.safe_load(file)
        except FileNotFoundError:
            dev_component_dict = None
            raise RobotDevProfileError(
                    f'Component \'{component["component"]}\' description '
                    'file not found.'
                )
        
        if dev_component_dict is not None:

            for key in dev_component_dict:
                component[key] = dev_component_dict[key]

            # # Load ros packages from component file
            # if (not component['ros_pkgs']) and \
            #         ('ros_pkgs' in dev_component_dict):
            #     component['ros_pkgs'] = dev_component_dict['ros_pkgs']
            # # Load src items from component file
            # if (not component['src']) and \
            #         ('src' in dev_component_dict):
            #     component['src'] = dev_component_dict['src']

            if component['host_ip'] == 'localhost':
                component['host_user'] = ''
                component['ssh_port'] = None

            dev_profile.components.append(RobotDevComponent(**component))

        
    print()

    return (
            dev_profile,
            RobotDevLocalConfig(**local_config),
            parser
        )
