import pathlib
import os

ROBOT_NAME = 'gary'

# DIRECTORIES

## Container Gary folder 
ROBOT_BASE_PATH = pathlib.Path(os.environ['ROBOT_BASE_PATH'])
## Container src path
DIR_SRC = ROBOT_BASE_PATH / 'src'
## Container ros packages source code
DIR_ROS_SRC = DIR_SRC / 'ros_pkgs'
## Container general build folder
DIR_BUILD_BASE = ROBOT_BASE_PATH / 'build'
## Container generic data folder
DIR_GENERIC_STATIC_DATA = ROBOT_BASE_PATH / 'generic_static_data'
## Container ROS specific build folder
DIR_ROS_BUILD_BASE = DIR_BUILD_BASE / 'ros_pkgs'
## Container ROS specific build sub-folder
DIR_ROS_BUILD = DIR_ROS_BUILD_BASE / 'build'
DIR_ROS_INSTALL = DIR_ROS_BUILD_BASE / 'install'
DIR_ROS_LOG = DIR_ROS_BUILD_BASE / 'log'
