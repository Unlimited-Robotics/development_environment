from robotdevenv.component import RobotDevComponent as Component
from robotdevenv.robot import RobotDevRobot as Robot

from robotdevenv.git import RobotDevGitHandler as GitHandler


class RobotDevSyncHandler():

    def __get_default_ws_name():
        return GitHandler.get_email().split('@')[0]
    

    
    

    def sync_to_robot(
                component:Component,
                robot:Robot,
            ):
        print(f'🔁💻 Synchronizing to remote host \'{robot.name}\'...')
        print(robot.get_remote_home())
        # print(RobotDevSyncHandler.__get_default_workspace_name())
