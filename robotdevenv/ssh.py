import subprocess


class RobotDevSSHError(Exception): pass


class RobotDevSSHHandler():

    def run_remote_get_output(
                host_alias:str,
                command:str,
                force_bash:bool=False,
            ):
        local_command = f'ssh {host_alias} '
        
        if force_bash:
            local_command += f'"bash -c \\"{command}\\""'
        else:
            local_command += command

        process = subprocess.run(
            local_command,
            shell=True,
            capture_output=True,
            text=True,
        )
        
        if process.returncode != 0:
                raise RobotDevSSHError(process.stderr)

        return process.stdout