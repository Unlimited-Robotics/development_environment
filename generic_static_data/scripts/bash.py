import subprocess
import os


def run_bash_command(
            command, 
            env, 
            bash=False, 
            ignore_command_error=False
        ):
    if bash:
        command = f'bash -c "{command}"'
    try:
        subprocess.run(
                command,
                shell=True, 
                check=True,
                env=dict(os.environ, **env)
            )
    except subprocess.CalledProcessError as e:
        if not ignore_command_error:
            raise e
