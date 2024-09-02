import yaml
import os
import pathlib
import subprocess
from typing import List

from robotdevenv.bash import run_bash_command
from robotdevenv.sync import create_run_component_script
from robotdevenv.sync import get_remote_dev_directory
from robotdevenv.git import get_git_email, get_env_version
from robotdevenv.ssh import RobotDevSSHError

from robotdevenv.constants import IMAGE_NAME_TEMPLATE
from robotdevenv.constants import ROBOT_COMPONENT_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_PROFILE_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_GENERIC_STATIC_DATA_PATH
from robotdevenv.constants import ROBOT_CONFIG_PATH, ROBOT_BUILD_PATH
from robotdevenv.constants import ROBOT_ROS_PKGS_PATH, ROBOT_NAME
from robotdevenv.constants import ROBOT_BASE_PATH, ROBOT_SRC_PATH
from robotdevenv.constants import ROBOT_GENERIC_PERSISTENT_DATA_PATH
from robotdevenv.constants import ROBOT_COMPONENT_PERSISTENT_DATA_PATH
from robotdevenv.constants import ENV_CONFIG_PATH, ROBOT_COMMANDS_PATH


class DockerLaunchError(Exception): pass
    

def get_image_name(
            component_repo: str,
            component_name: str,
            component_desc: dict,
            robot_host_desc: dict,
        ):
    return IMAGE_NAME_TEMPLATE.format(
            repo=component_repo,
            component=component_name,
            platform=robot_host_desc['platform'],
            version=component_desc['version'],
        )


def set_env_file(
            path_env_file: pathlib.Path,
            env: RobotDevEnvironment,
            path_dir_env: pathlib.Path,
            docker_command: str,
            env_vars: dict,
        ):
    local_env_path = env.dev_env_path / path_env_file
    remote_env_path = path_dir_env / path_env_file
    # Check if the file locally exist
    if local_env_path.is_file():
        # If yes, set the remote file in the commands
        print('Using env file:')
        print(f'  {remote_env_path}')
        docker_command += f'  --env-file={(remote_env_path)} \\\n'
        # And collect them form the local
        with open(local_env_path, 'r') as file:
            for line in file:
                line = line.strip()
                line = line.replace(' ','')
                if (not line.startswith('#')) and ('=' in line):
                    key, value = line.split('=', 1)
                    env_vars[key] = value

    return docker_command



def run_command_inside_container(
            env: RobotDevEnvironment,
            config: RobotDevLocalConfig,
            component: RobotDevComponent,
            command: str,
            volumes: List[tuple]=[],
            interactive=False,
            detached_mode=False,
            ignore_command_error=False,
        ):
    path_ros_domains = env.dev_env_path / 'users_ros_domains.yaml'
    with open(path_ros_domains, 'r') as file:
        domains = yaml.safe_load(file)
    git_email = get_git_email()
    if git_email not in domains:
        raise DockerLaunchError(
                f'{git_email} not defined in {path_ros_domains}'
            )
    ros_domain = domains[git_email]

    image_name = IMAGE_NAME_TEMPLATE.format(
            component=component.component,
            build_type=config.build_type,
            platform=component.platform,
            version=get_env_version(),
        )
    if component.host_ip=='localhost':
        path_dir_env = env.dev_env_path
    else:
        path_dir_env = get_remote_dev_directory(config, component)

    user_id = get_git_email().split('@')[0]
    container_name = f'{component.component}.{user_id}'

    # Robot Configuration PATH

    if ENV_CONFIG_PATH in os.environ:
        robot_configuration_path = pathlib.Path(os.environ[ENV_CONFIG_PATH])
        using_global_config_path = True
    else:
        robot_configuration_path = pathlib.Path(f'{path_dir_env}/config')
        using_global_config_path = False
    
    print('Using configuration folder:')
    print(f'  {robot_configuration_path}')

    # Is container already running?

    try:
        cmd_output = run_bash_command(
                component=component,
                command=f"docker container ls | grep {container_name}", 
                interactive=interactive, 
                capture_output=True,
            )
        if cmd_output is None:
            cont_already_running = False
        else:    
            cont_already_running = True
    except subprocess.CalledProcessError as e:
        cont_already_running = False
    except RobotDevSSHError:
        cont_already_running = False

    docker_command = ''

    if component.display:
        docker_command += 'DISPLAY=:0 xhost +local:* && '

    if not cont_already_running:
        # Base docker command
        docker_command += (
                'docker run \\\n'
                '  --tty \\\n'
                '  --privileged \\\n'
                '  --network=host \\\n'
                '  --pid=host \\\n'
            )
        
        if component.platform == 'jetsonorinagx':
            docker_command += '  --runtime nvidia \\\n'
        
        # Container name
        docker_command += f'  --name {container_name}\\\n'
        
        # Static environment variables
        docker_command += f'  -e=IDHOST={component.host_ip} \\\n'
        docker_command += f'  -e=IDCOMPONENT={component.component} \\\n'
        docker_command += f'  -e=ROBOT_NAME={ROBOT_NAME} \\\n'
        docker_command += f'  -e=ROBOT_BASE_PATH={ROBOT_BASE_PATH} \\\n'
        docker_command += f'  -e=ROBOT_GENERIC_STATIC_DATA_PATH={ROBOT_GENERIC_STATIC_DATA_PATH} \\\n'
        docker_command += f'  -e=ROBOT_GENERIC_PERSISTENT_DATA_PATH={ROBOT_GENERIC_PERSISTENT_DATA_PATH} \\\n'
        docker_command += f'  -e=ROBOT_COMPONENT_STATIC_DATA_PATH={ROBOT_COMPONENT_STATIC_DATA_PATH} \\\n'
        docker_command += f'  -e=ROBOT_COMPONENT_PERSISTENT_DATA_PATH={ROBOT_COMPONENT_PERSISTENT_DATA_PATH} \\\n'
        docker_command += f'  -e=ROBOT_PROFILE_STATIC_DATA_PATH={ROBOT_PROFILE_STATIC_DATA_PATH} \\\n'
        docker_command += f'  -e=ROBOT_CONFIG_PATH={ROBOT_CONFIG_PATH} \\\n'
        docker_command += f'  -e=ROBOT_BUILD_PATH={ROBOT_BUILD_PATH} \\\n'
        docker_command += f'  -e=ROBOT_SRC_PATH={ROBOT_SRC_PATH} \\\n'
        docker_command += f'  -e=ROBOT_ROS_PKGS_PATH={ROBOT_ROS_PKGS_PATH} \\\n'

        # Display
        if component.display:
            docker_command +=  '  -e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \\\n'
            docker_command += f'  -e=DISPLAY=:0 \\\n'
            docker_command +=  '  -v=${XDG_RUNTIME_DIR}/gdm/Xauthority:/root/.Xauthority \\\n'
            docker_command += f'  -v=/tmp/.X11-unix:/tmp/.X11-unix:rw  \\\n'

        # Sound
        if component.sound:
            docker_command +=  '  -v /etc/alsa:/etc/alsa \\\n'
            docker_command +=  '  -v /usr/share/alsa:/usr/share/alsa \\\n'
            docker_command +=  '  -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            docker_command +=  '  -e PULSE_COOKIE=/root/.config/pulse/cookie \\\n'
            docker_command +=  '  -v ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \\\n'
            # TODO: Why explicit "gary":
            docker_command +=  '  -v /home/gary/.config/pulse/cookie:/root/.config/pulse/cookie \\\n'

        # Devices
        if component.devices:
            docker_command +=  '  -v /dev:/dev \\\n'
            docker_command +=  '  -v /run/udev:/run/udev:ro \\\n'

        # Environment variables file

        env_vars = {}

        docker_command = set_env_file(
                pathlib.Path('profiles') / config.profile / 'env',
                env=env, path_dir_env=path_dir_env, 
                docker_command=docker_command, env_vars=env_vars,
            )

        docker_command = set_env_file(
                pathlib.Path('components') / component.component / 'env',
                env=env, path_dir_env=path_dir_env, 
                docker_command=docker_command, env_vars=env_vars,
            )

        docker_command = set_env_file(
                pathlib.Path('config') / 'env' / 'env',
                env=env, path_dir_env=path_dir_env, 
                docker_command=docker_command, env_vars=env_vars,
            )

        docker_command = set_env_file(
                pathlib.Path('config') / 'env' / f'{component.component}.env',
                env=env, path_dir_env=path_dir_env, 
                docker_command=docker_command, env_vars=env_vars,
            )

        if 'ROS_DOMAIN_ID' in env_vars:
            print()
            print('⚠️  Using \'ROS_DOMAIN_ID\' from files instead of static one.')
        else:
            docker_command += f'  -e=ROS_DOMAIN_ID={ros_domain} \\\n'

        print()

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

        # Volumes
        docker_command += (
                f'  -v={path_dir_env}/components/{component.component}/component_static_data:{ROBOT_COMPONENT_STATIC_DATA_PATH} \\\n'
                f'  -v={path_dir_env}/component_persistent_data/{component.component}:{ROBOT_COMPONENT_PERSISTENT_DATA_PATH} \\\n'
                f'  -v={path_dir_env}/profiles/{config.profile}/profile_static_data:{ROBOT_PROFILE_STATIC_DATA_PATH} \\\n'
                f'  -v={robot_configuration_path}:{ROBOT_CONFIG_PATH} \\\n'
            )
        for volume in volumes:
            volume_str = [str(s) for s in volume]
            docker_command += f'  -v={":".join(volume_str)} \\\n'
        # Check if commands folder available
        if (env.dev_env_path / 'components'/ component.component / 'commands').is_dir():
            docker_command += f'  -v={path_dir_env/"components"/component.component/"commands"}:{ROBOT_COMMANDS_PATH}'

        # Create file for local execution
        docker_command += f'  {image_name} \\\n'
        local_run_file = f'#!/bin/bash\n\n{docker_command}'
        local_run_file += '  \\\n$@\\\n \\\n'
        create_run_component_script(
                config=config,
                component=component,
                content=local_run_file
            )

        # Add command
        docker_command += f'  \\\n{command}\\\n \\\n'
        
        try:
            run_bash_command(component, docker_command, interactive=interactive)
        except subprocess.CalledProcessError as e:
            if not ignore_command_error:
                raise e

    else:
        if not command:
            command = 'bash'
        print(
                f'  ℹ️  Container \'{container_name}\' already running, '
                f'executing \'{command}\' inside it\n'
            )
        docker_command = 'docker exec '
        if interactive:
            docker_command += '-it '
        docker_command += f'{container_name} {command}'
        run_bash_command(
                component,
                docker_command, 
                interactive=interactive,
            )
