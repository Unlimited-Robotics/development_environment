import pathlib

from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot
from robotdevenv.git import RobotDevGitHandler as GitHandler

from robotdevenv.constants import REMOTE_HOST_WORKSPACES_FOLDER_NAME


class RobotDevSyncHandler():

    def get_default_ws_name():
        return GitHandler.get_email().split('@')[0]
    

    
    

    def sync_to_robot(
                component:Component,
                robot:Robot,
            ):
        print(f'🔁💻 Synchronizing to remote host \'{robot.name}\'...')

        remote_ws_path = robot.get_remote_home() / \
                         REMOTE_HOST_WORKSPACES_FOLDER_NAME / \
                         RobotDevSyncHandler.get_default_ws_name

        print(remote_ws_path)

        # print(RobotDevSyncHandler.__get_default_workspace_name())
