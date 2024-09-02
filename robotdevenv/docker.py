import subprocess

from robotdevenv.component import RobotDevComponent
from robotdevenv.robot import RobotDevRobot

from robotdevenv.environment import DEV_ENV_PATH


class RobotDevDockerHandler():

    def build_image(
                component:RobotDevComponent,
                robot:RobotDevRobot,
            ):
        
        docker_build_context_path = component.folder_path

        docker_build_command = f'cd {DEV_ENV_PATH} && '

        if not robot.is_local:
            docker_build_command += f'DOCKER_HOST=ssh://{robot.name} '

        docker_build_command += (
            'docker build '
            f'--tag {component.image_name} '
            f'-f {component.dockerfile_path} '
            f'{docker_build_context_path}'
        )

        subprocess.run(
            docker_build_command, 
            shell=True, 
            check=True,
        )
        print()
