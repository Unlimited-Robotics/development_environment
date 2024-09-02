import subprocess


class RobotDevGitError(Exception): pass


class RobotDevGitHandler():

    def get_email():
        try:
            return subprocess.check_output(
                    ['git', 'config', 'user.email']
                ).decode().strip()

        except subprocess.CalledProcessError as e:
            raise RobotDevGitError(
                    'Can not get git email, make sure you already defined it'
                )
