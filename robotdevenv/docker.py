import subprocess
from typing import List, Dict

from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot
from robotdevenv.singleton import Singleton

from robotdevenv.constants import DEV_ENV_PATH


class RobotDevDockerHandler(Singleton):

    def __init__(self,
                component:Component,
                robot:Robot,
            ):
        self.__component:Component = component
        self.__robot:Robot = robot


    def build_image(self):
        
        docker_build_context_path = self.__component.local_path

        docker_build_command = f'cd {DEV_ENV_PATH} && '

        if not self.__robot.is_local:
            docker_build_command += f'DOCKER_HOST=ssh://{self.__robot.name} '

        docker_build_command += (
            'docker build '
            f'--tag {self.__component.image_name} '
            f'-f {self.__component.dockerfile_path} '
            f'{docker_build_context_path}'
        )

        subprocess.run(
            docker_build_command, 
            shell=True, 
            check=True,
        )
        print()


    def run_command(self,
                command: str,
                volumes: List[tuple]=[],
                env_files: List[str]=[],
                env_vars: Dict[str, str]=[],
                interactive=False,
                detached_mode=False,
            ):

        docker_command = ''

        if self.__component.display:
            docker_command += 'DISPLAY=:0 xhost +local:* && '

        if not self.__robot.is_local:
            docker_command += f'DOCKER_HOST=ssh://{self.__robot.name} \\\n'

        docker_command += (
                'docker run \\\n'
                '  --tty \\\n'
                '  --privileged \\\n'
                '  --network=host \\\n'
                '  --pid=host \\\n'
            )
            

        if not self.__robot.platform == 'jetsonorinagx':
            docker_command += '  --runtime nvidia \\\n'

        docker_command += f'  --name {self.__component.container_name}\\\n'

        # Interactive mode
        if interactive:
            docker_command += '  -it \\\n'
            docker_command += '  --rm \\\n'
        # Detached mode
        elif detached_mode:
            docker_command +=  '  -d \\\n'
            docker_command += f'  -e=DETACHED_MODE=true \\\n'
        # Not interactive not attached mode
        else:
            docker_command += '  --rm \\\n'

        # Display
        if self.__component.display:
            docker_command +=  '  -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \\\n'
            docker_command += f'  -e=DISPLAY=:0 \\\n'
            docker_command +=  '  -v=${XDG_RUNTIME_DIR}/gdm/Xauthority:/root/.Xauthority \\\n'
            docker_command += f'  -v=/tmp/.X11-unix:/tmp/.X11-unix:rw  \\\n'

        # Sound
        if self.__component.sound:
            docker_command +=  '  -v /etc/alsa:/etc/alsa \\\n'
            docker_command +=  '  -v /usr/share/alsa:/usr/share/alsa \\\n'
            docker_command +=  '  -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            docker_command +=  '  -e PULSE_COOKIE=/root/.config/pulse/cookie \\\n'
            docker_command +=  '  -v ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            docker_command +=  f'  -v {self.__robot.get_remote_home()}/.config/pulse/cookie:/root/.config/pulse/cookie \\\n'
        
        # Env Files
        for env_file in env_files:
            docker_command += f'  --env-file={env_file} \\\n'

        # Env Variables
        for key, value in env_vars.items():
            docker_command += f'  -e={key}={value} \\\n'

        # Volumes
        for volume in volumes:
            volume_str = [str(s) for s in volume]
            docker_command += f'  -v={":".join(volume_str)} \\\n'

        # Command
        docker_command += f'  \\\n{command}\\\n \\\n'

        print(docker_command)

        subprocess.run(
            docker_command, 
            shell=True, 
            check=True,
        )
