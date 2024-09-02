import subprocess

from robotdevenv.ssh import run_ssh_command


def run_bash_command(
            component:RobotDevComponent,
            command:str,
            force_bash:bool = False,
            interactive:bool = False,
            capture_output = False,
        ):
    if component.host_ip=='localhost':
        return subprocess.run(
                command, 
                shell=True, 
                check=True,
                capture_output=capture_output,
                text=capture_output,
            ).stdout
    else:
        return run_ssh_command(
                component, 
                command, 
                interactive=interactive,
                force_bash=force_bash,
                capture_output = capture_output,
            )
