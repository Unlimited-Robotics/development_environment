import pathlib
import subprocess


FILE_SSH_CONFIG = pathlib.Path.home() / '.ssh' / 'config'


class RobotDevSSHError(Exception): pass


def get_ssh_control_path(
            component:RobotDevComponent, 
        ):
    return f'/tmp/control-{component.host_user}-{component.host_ip}'


def run_ssh_command(
            component:RobotDevComponent, 
            command:str, 
            force_bash:bool=False,
            interactive:bool=False,
            capture_output = False,
        ):
    local_command = 'ssh '
    local_command += '-o ControlMaster=auto '
    local_command += f'-o ControlPath={get_ssh_control_path(component)} '
    local_command += '-o ControlPersist=yes '

    if interactive:
        local_command += '-t '
    if component.ssh_port > 0:
        local_command += f'-p {component.ssh_port} '

    local_command += f'{component.host_user}@{component.host_ip} '

    if force_bash:
        local_command += f'"bash -c \\"{command}\\""'
    else:
        local_command += command

    cmd = subprocess.run(
                local_command,
                shell=True,
                capture_output=capture_output,
                text=capture_output,
            )
    
    if cmd.returncode != 0:
        if interactive:
            return
        else:
            raise RobotDevSSHError(cmd.stderr)


    return cmd.stdout

    # raise RuntimeError

    # try:
    #     return subprocess.run(
    #             local_command,
    #             shell=True,
    #             check=True,
    #             # capture_output=capture_output,
    #             # text=capture_output
    #         ).stdout
    # except Exception as e:
    #     if interactive:
    #         pass
    #     else:
    #         print(type(e))
    #         print(dir(e))
    #         print(e.output)
    #         raise e
