import subprocess


class RobotDevSSHError(Exception): pass


class RobotDevSSHHandler():

    def run_remote_get_output(
                host_alias: str,
                command: str,
            ):
        local_command = f'ssh {host_alias} '
        

        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        
        if process.returncode != 0:
                raise RobotDevSSHError(process.stderr)

        return process.stdout