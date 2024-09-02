import subprocess


global_env_version = ''


class RobotDevGitError(Exception): pass
class RobotDevSyncError(Exception): pass


def get_git_email():
    try:
        return subprocess.check_output(
                ['git', 'config', 'user.email']
            ).decode().strip()

    except subprocess.CalledProcessError as e:
        raise RobotDevSyncError(
                'Can not get git email, make sure you already defined it'
            )

def get_env_version():
    global global_env_version
    if global_env_version == '':
        tags = subprocess.check_output(
                    ['git', 'tag', '--points-at', 'HEAD']
                ).decode().strip().split('\n')
        if tags and tags[0]!='':
            global_env_version = tags[0]
        branch_name = subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD']
                ).decode().strip()
        if branch_name=='HEAD':
            raise RobotDevGitError(
                    'Developent environment git repository is in a detached '
                    'commit'
                )
        global_env_version = branch_name
    global_env_version = global_env_version.replace('/', '_')
    return global_env_version