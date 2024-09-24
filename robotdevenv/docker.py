import subprocess
import json
from typing import List, Dict
from enum import Enum

from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot

from robotdevenv.constants import DEV_ENV_PATH
from robotdevenv.constants import FOLDER_SRC
from robotdevenv.constants import DEPLOY_DOCKER_REPO_ENDPOINT
from robotdevenv.constants import GENERIC_PROD_DOCKERFILE


class BuildImageType(Enum):
    DEVEL = 0
    PROD = 1


class RobotDevDockerHandler:

    def __init__(self,
                component:Component,
                robot:Robot,
            ):
        self.component:Component = component
        self.robot:Robot = robot
        
    
    def build_image(self, build_type:BuildImageType, metadata={}):

        if build_type==BuildImageType.DEVEL:
            docker_build_context_path = self.component.local_path
            tag = self.component.image_name_dev
            dockerfile = self.component.dockerfile_path
        elif build_type==BuildImageType.PROD:
            docker_build_context_path = DEV_ENV_PATH / FOLDER_SRC
            tag = self.component.image_name_prod
            dockerfile = GENERIC_PROD_DOCKERFILE

        docker_build_command = f'cd {DEV_ENV_PATH} && '

        if not self.robot.is_local:
            docker_build_command += f'DOCKER_HOST=ssh://{self.robot.name} '

        docker_build_command += (
            'docker build '
            f'--build-arg REGISTRY_ENDPOINT={DEPLOY_DOCKER_REPO_ENDPOINT} '
            f'--build-arg REPOS_LIST=\'{" ".join(self.component.src)}\' '
            f'--build-arg PACKAGES_LIST=\'{" ".join(self.component.ros_pkgs)}\' '
            # '--progress=plain '
            f'--tag {tag} '
        )

        for key in metadata:
            docker_build_command += f'--build-arg {key}=\'{metadata[key]}\' '

        if build_type==BuildImageType.PROD:
            docker_build_command += f'--build-arg FROM={self.component.image_name_dev} '

        docker_build_command += f'-f {dockerfile} '
        docker_build_command += f'{docker_build_context_path}'

        print(docker_build_command)

        subprocess.run(
            docker_build_command, 
            shell=True, 
            check=True,
        )
        print()

    
    def push_image(self, build_type:BuildImageType):

        if build_type==BuildImageType.DEVEL:
            tag = self.component.image_name_dev
        elif build_type==BuildImageType.PROD:
            tag = self.component.image_name_prod

        docker_build_command = f'cd {DEV_ENV_PATH} && '

        if self.robot.is_local:
            ssh_prefix = ''
        else:
            ssh_prefix = f'DOCKER_HOST=ssh://{self.robot.name}'

        # print('HOLA')
        # print(tag)
        # print(self.component.version_dev)
        # print(self.component.version_prod)
        version = tag.split(f':{self.robot.platform}.')[-1]
        if version.endswith('.dev'):
            tag_latest = tag.replace(version, 'latest-dev')
        elif version.endswith('.beta'):
            tag_latest = tag.replace(version, 'latest-beta')
        else:
            tag_latest = tag.replace(version, 'latest')

        docker_build_command += (
            f'{ssh_prefix} docker tag {tag} {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag} && '
            f'{ssh_prefix} docker tag {tag} {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag_latest} && '
            f'{ssh_prefix} docker push {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag} && '
            f'{ssh_prefix} docker push {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag_latest} && '
            f'{ssh_prefix} docker rmi {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag} && '
            f'{ssh_prefix} docker rmi {DEPLOY_DOCKER_REPO_ENDPOINT}/{tag_latest}'
        )

        subprocess.run(
            docker_build_command, 
            shell=True, 
            check=True,
        )

        print()


    def pull_image(self, image:str):
        if self.robot.is_local:
            ssh_prefix = ''
        else:
            ssh_prefix = f'DOCKER_HOST=ssh://{self.robot.name}'

        docker_build_command = (
            f'{ssh_prefix} docker pull {DEPLOY_DOCKER_REPO_ENDPOINT}/{image} && '
            f'{ssh_prefix} docker tag {DEPLOY_DOCKER_REPO_ENDPOINT}/{image} {image} && '
            f'{ssh_prefix} docker rmi {DEPLOY_DOCKER_REPO_ENDPOINT}/{image}'
        )

        subprocess.run(
            docker_build_command, 
            shell=True, 
            check=True,
        )
        print()


    def pull_images(self, version:str):
        if version.endswith('.dev'):
            images_to_pull = [
                f'{self.component.image_name_base}.{version}',
            ]
        else:
            images_to_pull = [
                f'{self.component.image_name_base}.{version}',
                f'{self.component.image_name_base}.{version.replace(".beta","")}.dev',
            ]
        
        for image in images_to_pull:
            self.pull_image(image)


    def get_running_container_info(self):
        docker_command = ''
        if not self.robot.is_local:
            docker_command += f'DOCKER_HOST=ssh://{self.robot.name} \\\n'
        docker_command += "docker inspect " 
        docker_command += self.component.container_name

        try:
            process = subprocess.run(
                docker_command,
                shell=True, 
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(process.stdout)[0]
        except subprocess.CalledProcessError:
            return None
        

    def get_running_containers_and_images(self):
        docker_command = ''
        if not self.robot.is_local:
            docker_command += f'DOCKER_HOST=ssh://{self.robot.name} \\\n'
        docker_command += 'docker ps -a --format \'{{.Names}}: {{.Image}}\''
        try:
            process = subprocess.run(
                docker_command,
                shell=True, 
                check=True,
                capture_output=True,
                text=True,
            )
            containers_list = []
            for line in process.stdout.split('\n'):
                if line.strip():
                    line_split = line.split(':')
                    if len(line_split)==3:
                        containers_list.append((
                            line_split[0].strip(),
                            line_split[1].strip(),
                            line_split[2].strip(),
                        ))
            return containers_list

        except subprocess.CalledProcessError:
            return []


    def run_command(self,
                command: str,
                volumes: List[tuple]=[],
                env_files: List[str]=[],
                env_vars: Dict[str, str]=[],
                interactive=False,
                detached_mode=False,
            ):

        docker_command = ''

        if self.component.display:
            docker_command += 'DISPLAY=:0 xhost +local:* && '

        if not self.robot.is_local:
            docker_command += f'DOCKER_HOST=ssh://{self.robot.name} \\\n'

        docker_command += (
                'docker run \\\n'
                '  --tty \\\n'
                '  --privileged \\\n'
                '  --network=host \\\n'
                '  --pid=host \\\n'
            )

        if self.robot.platform == 'jetsonorinagx':
            docker_command += '  --runtime nvidia \\\n'

        docker_command += f'  --name {self.component.container_name}\\\n'

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
        if self.component.display:
            docker_command +=  '  -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \\\n'
            docker_command += f'  -e=DISPLAY=:0 \\\n'
            docker_command +=  '  -v=${XDG_RUNTIME_DIR}/gdm/Xauthority:/root/.Xauthority \\\n'
            docker_command += f'  -v=/tmp/.X11-unix:/tmp/.X11-unix:rw  \\\n'

        # Sound
        if self.component.sound:
            docker_command +=  '  -v /etc/alsa:/etc/alsa \\\n'
            docker_command +=  '  -v /usr/share/alsa:/usr/share/alsa \\\n'
            docker_command +=  '  -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            docker_command +=  '  -e PULSE_COOKIE=/root/.config/pulse/cookie \\\n'
            docker_command +=  '  -v ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            docker_command +=  f'  -v {self.robot.get_remote_home()}/.config/pulse/cookie:/root/.config/pulse/cookie \\\n'

        # Devices
        if self.component.devices:
            docker_command +=  '  -v /dev:/dev \\\n'
            docker_command +=  '  -v /run/udev:/run/udev:ro \\\n'

        # System
        if self.component.system: 
            docker_command +=  '  -v /sys/kernel/debug/clk:/clk:ro \\\n'
            
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

        # Image
        docker_command += f'  {self.component.image_name_dev} \\\n'

        # Command
        docker_command += f'  \\\n{command}\\\n \\\n'

        try:
            subprocess.run(
                docker_command, 
                shell=True, 
                check=True,
            )
        except subprocess.CalledProcessError as e:
            if not interactive:
                raise e


    def exec_command(self,
                command: str,
                interactive=False,
            ):

        docker_command = ''

        if not self.robot.is_local:
            docker_command += f'DOCKER_HOST=ssh://{self.robot.name} \\\n'

        docker_command += 'docker exec '

        if interactive:
            docker_command += '-it '

        docker_command += f'{self.component.container_name} {command}'

        try:
            subprocess.run(
                docker_command, 
                shell=True, 
                check=True,
            )
        except subprocess.CalledProcessError as e:
            if not interactive:
                raise e

