import pathlib
import subprocess
from typing import List, Tuple
import os
import tempfile
from robotdevenv.git import get_git_email
from robotdevenv.profile import RobotDevComponent, RobotDevLocalConfig
from robotdevenv.environment import RobotDevEnvironment
from robotdevenv.ssh import run_ssh_command, get_ssh_control_path
from robotdevenv.constants import ROBOT_NAME


class RobotDevRSyncError(Exception): pass


def rsync_to_host(
            component:RobotDevComponent,
            source:pathlib.Path, 
            destination:pathlib.Path,
        ):
    rsync_command = (
        'rsync '
        '--copy-links '
        '-e "ssh '
            '-o ControlMaster=auto '
            f'-o ControlPath={get_ssh_control_path(component)} '
            '-o ControlPersist=yes '
            f'-p {component.ssh_port} '
        '" '
        '--checksum --archive --verbose --stats --delete '
        f'{source} '
        f'{component.host_user}@{component.host_ip}:{destination}'
    )
    res = subprocess.run(
            rsync_command, shell=True, capture_output=True, text=True
        )
    if res.returncode!=0:
        raise RobotDevRSyncError(res.stderr)


def copy_to_host(
            component:RobotDevComponent,
            source:pathlib.Path, 
            destination:pathlib.Path,
        ):
    scp_command = (
        'scp -o ControlMaster=auto '
        f'-o ControlPath={get_ssh_control_path(component)} '
        '-o ControlPersist=yes '
        f'-P {component.ssh_port} '
        f'{source} '
        f'{component.host_user}@{component.host_ip}:{destination}'
    )
    res = subprocess.run(
            scp_command, shell=True, capture_output=True, text=True
        )
    if res.returncode!=0:
        raise RobotDevRSyncError(res.stderr)


def get_remote_dev_directory(
            config: RobotDevLocalConfig,
            component: RobotDevComponent,
        ):
    remote_dev_dir = (
            f'/home/{component.host_user}/dev_workspace/{ROBOT_NAME}/'
            f'{config.workspace}'
        )
        
    return pathlib.Path(remote_dev_dir)


def get_default_workspace():
    return  get_git_email().split('@')[0]


def create_run_component_script(
            config:RobotDevLocalConfig,
            component:RobotDevComponent,
            content:str,
        ):
    with tempfile.NamedTemporaryFile(
                delete=False, 
                mode='w', 
                suffix='.sh'
            ) as temp_file:
        temp_file.write(content)
        temp_file_name = temp_file.name

    os.chmod(temp_file_name, 0o755)

    if component.host_ip=='localhost':
        pass
    else:
        remote_dev_dir = get_remote_dev_directory(config, component)
        dest_path = remote_dev_dir / 'components' / f'{component.component}.sh'
        copy_to_host(component, temp_file_name, dest_path)


def sync_folders_to_host(
            component:RobotDevComponent,
            folders_pairs:List[Tuple[pathlib.Path, pathlib.Path]]
        ):
    print(f'🔁💻 Synchronizing to remote host \'{component.host_ip}\'...')
    for origin_dir, destination_dir in folders_pairs:
        run_ssh_command(
                component=component, 
                command=f'mkdir -p {destination_dir}',
                capture_output=True,
            )
        rsync_to_host(component, origin_dir, destination_dir)
    print('Remote host synchronized')
    print()
    

def check_workspace(
            config:RobotDevLocalConfig,
            only_warning=False,
        ):
    default_workspace = get_default_workspace()
    if config.workspace != default_workspace:
        print(
                '⚠️ ⚠️  You are trying to sync to the workspace '
                f'\'{config.workspace}\', but your default workspace is '
                f'\'{default_workspace}\', be mindful that you can interrupt'
                'or affect other\'s work.'
            )
        if only_warning:
            print()
            return
        response = input('Do you want to proceed? [y/n] ')
        if response.lower().replace(' ', '') != 'y':
            print('Aborted')
            exit(1)
        print()


def get_components_to_sync(
            component_name:str,
            env:RobotDevEnvironment,
        ):
    components_to_sync = set()
    
    # Look for depencencies or base images
    local_components_path = env.dev_env_path / pathlib.Path('components')
    this_component_path = local_components_path / component_name

    if not this_component_path.is_dir():
        raise RobotDevRSyncError(
                f'Component \'{component_name}\' does not exist.'
            )
    
    this_dockerfiles_path = this_component_path / 'dockerfiles'
    
    for platform_path in this_dockerfiles_path.iterdir():
        base_dockerfiles = list(platform_path.glob("00.*.base"))
        if len(base_dockerfiles)>1:
            raise RobotDevRSyncError(
                    f'Component \'{component_name}\' has more than one '
                    'base docker image.'
                )
        for base_dockerfile in base_dockerfiles:
            dep_name = \
                base_dockerfile.name.replace('00.','').replace('.base','')
            components_to_sync.update(get_components_to_sync(dep_name, env))

    components_to_sync.add(component_name)

    return components_to_sync


def sync_component_data(
            config:RobotDevLocalConfig,
            component:RobotDevComponent, 
            env:RobotDevEnvironment,
        ):
    
    local_components_path = env.dev_env_path / pathlib.Path('components')
    remote_dev_dir = get_remote_dev_directory(config, component)

    components_to_sync = get_components_to_sync(
            component_name=component.component,
            env=env,
        )
    
    local_cache_path = env.dev_env_path / 'local_cache' / config.profile / component.component
    
    local_cache_path.mkdir(parents=True, exist_ok=True)

    # (origin, destination)
    folders_pairs = [
        (
            env.dev_env_path / '.dockerignore',
            remote_dev_dir
        ),(
            local_cache_path,
            remote_dev_dir / 'local_cache' / config.profile,
        ),(
            env.dev_env_path / 'generic_static_data',
            remote_dev_dir
        ),(
            env.dev_env_path / 'generic_persistent_data',
            remote_dev_dir
        ),(
            env.dev_env_path / 'profiles',
            remote_dev_dir
        ),(
            env.dev_env_path / 'config',
            remote_dev_dir
        )
    ]

    for component_to_sync in components_to_sync:
        folders_pairs.append((
            local_components_path / component_to_sync,
            remote_dev_dir / pathlib.Path('components')
        ))

    if component.src:
        for src_component in component.src:
            folders_pairs.append((
                    env.dev_env_path / 'src' / src_component,
                    remote_dev_dir / 'src',
                ))
    
    # Git now always keep the writting and reading permissions (problem with 
    # hash generation of docker), only keep the execution permissions. So we 
    # standarize as rw?r-?r-?. (everyone can read, only user can write, and 
    # the execution is kept).
    for source_folder, _ in folders_pairs:
        try:
            # Only files inside the components folder
            source_folder.relative_to(local_components_path)
            for file_path in source_folder.rglob('**/*'):
                if file_path.is_file():
                    permissions = file_path.stat().st_mode
                    # The writting permission of user group is revoked
                    new_permissions = permissions & ~0o020
                    file_path.chmod(new_permissions)
        except ValueError:
            pass

    sync_folders_to_host(component, folders_pairs)