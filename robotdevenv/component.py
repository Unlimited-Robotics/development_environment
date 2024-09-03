import argparse
import yaml

from robotdevenv.robot import RobotDevRobot
from robotdevenv.singleton import Singleton

from robotdevenv.constants import DEV_ENV_PATH
from robotdevenv.constants import IMAGE_NAME_TEMPLATE
from robotdevenv.constants import CONTAINER_NAME_TEMPLATE
from robotdevenv.constants import ROBOT_GENERIC_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_GENERIC_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_BUILD_PATH
from robotdevenv.constants import ROBOT_SRC_PATH
from robotdevenv.constants import FOLDER_SRC


class RobotDevComponentError(Exception): pass


class RobotDevComponent(Singleton):

    def __init__(self, 
                parser:argparse.ArgumentParser,
                robot:RobotDevRobot
            ):
        
        parser.add_argument('-c', '--component', type=str, required=True)
        args = dict(parser.parse_known_args()[0]._get_kwargs())
        full_name = args['component']

        try:
            repo, name = full_name.split('/')
        except ValueError:
            raise RobotDevComponentError(
                f'Invalid component name \'{full_name}\'. It must have '
                'the format \'<repo>/<component>\'.'
            )
        
        local_path = DEV_ENV_PATH / FOLDER_SRC / repo / 'components' / name
        component_desc_path = local_path / f'{name}.yaml'

        try:
            with open(component_desc_path, 'r') as file:
                component_desc = yaml.safe_load(file)
        except FileNotFoundError:
            raise RobotDevComponentError(
                f'Profile description file \'{component_desc_path}\' not found.'
            )
        
        version = component_desc['version']
        
        if 'src' in component_desc:
            src = component_desc['src']
        else:
            src = []

        if 'ros_pkgs' in component_desc:
            ros_pkgs = component_desc['ros_pkgs']
        else:
            ros_pkgs = []

        if 'display' in component_desc:
            display = component_desc['display']
        else:
            display = False

        if 'sound' in component_desc:
            sound = component_desc['sound']
        else:
            sound = False

        if 'devices' in component_desc:
            devices = component_desc['devices']
        else:
            devices = False

        dockerfile_path = local_path / 'dockerfiles' / \
            f'{robot.platform}.dockerfile'
        if not dockerfile_path.is_file():
            raise RobotDevComponentError(
                f'Dockerfile: \'{dockerfile_path}\' not found.'
            )
        
        image_name = IMAGE_NAME_TEMPLATE.format(
            repo=repo,
            component=name,
            platform=robot.platform,
            version=version,
        )

        container_name = CONTAINER_NAME_TEMPLATE.format(
            repo=repo,
            component=name,
        )

        host_path = \
            robot.get_host_ws_path() / FOLDER_SRC / repo / 'components' / name

        # Private attributes
        self.__robot = robot

        # Public attributes
        self.full_name = full_name
        self.repo = repo
        self.name = name
        self.local_path = local_path
        self.host_path = host_path
        self.version = version
        self.src = src
        self.ros_pkgs = ros_pkgs
        self.display = display
        self.sound = sound
        self.devices = devices
        self.dockerfile_path = dockerfile_path
        self.image_name = image_name
        self.container_name = container_name


    def get_volumes(self):

        host_ws_path = self.__robot.get_host_ws_path()

        ## General build folder
        dir_host_build_base = host_ws_path / 'build' / self.full_name
        ## Generic static data folder
        dir_host_generic_static_data = host_ws_path / 'generic_static_data'
        ## Generic persistent data folder
        dir_host_generic_persistent_data = host_ws_path / 'generic_persistent_data'
        ## Component static data folder
        dir_host_component_static_data = self.host_path / 'component_static_data'
        ## Component persistent data folder
        dir_host_component_persistent_data = host_ws_path / 'component_persistent_data' / self.full_name

        volumes = [
                (dir_host_build_base, ROBOT_BUILD_PATH),
                (dir_host_generic_static_data, ROBOT_GENERIC_STATIC_DATA_PATH, 'ro'),
                (dir_host_generic_persistent_data, ROBOT_GENERIC_PERSISTENT_DATA_PATH),
                (dir_host_component_static_data, ROBOT_COMPONENT_STATIC_DATA_PATH, 'ro'),
                (dir_host_component_persistent_data, ROBOT_COMPONENT_PERSISTENT_DATA_PATH),
            ]
            
        if self.src:
            for src_component in self.src:
                dir_host_src_component = host_ws_path / 'src' / src_component
                volumes.append(
                    (dir_host_src_component, f'{ROBOT_SRC_PATH}/{src_component}', 'ro'),
                )   
        
        return volumes
