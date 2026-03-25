import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro


def generate_launch_description():

    pkg = get_package_share_directory('conveyor_belt')
    xacro_file = os.path.join(pkg, 'urdf', 'conveyor_belt.urdf.xacro')

    # Belt 1 — moves in positive direction (left)
    xml1 = xacro.process(xacro_file, mappings={'namespace': 'belt1', 'max_velocity': '0.3'})

    # Belt 2 — moves in negative/reverse direction (right), placed 2 m away on Y axis
    xml2 = xacro.process(xacro_file, mappings={'namespace': 'belt2', 'max_velocity': '-0.3'})

    # Launch Gazebo
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    world = os.path.join(pkg, 'worlds', 'empty_world.world')

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')
        ),
        launch_arguments={'world': world}.items()
    )
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')
        )
    )

    # Publish descriptions
    pub1 = Node(
        package='conveyor_belt',
        executable='robot_description_publisher.py',
        name='robot_description_publisher_1',
        output='screen',
        arguments=['-xml_string', xml1, '-robot_description_topic', '/robot_description_1']
    )
    pub2 = Node(
        package='conveyor_belt',
        executable='robot_description_publisher.py',
        name='robot_description_publisher_2',
        output='screen',
        arguments=['-xml_string', xml2, '-robot_description_topic', '/robot_description_2']
    )

    # Robot state publishers
    rsp1 = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_1',
        parameters=[{'use_sim_time': True, 'robot_description': xml1}],
        remappings=[('/robot_description', '/robot_description_1')],
        output='screen'
    )
    rsp2 = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_2',
        parameters=[{'use_sim_time': True, 'robot_description': xml2}],
        remappings=[('/robot_description', '/robot_description_2')],
        output='screen'
    )

    # Spawn belt 1 at y=0
    spawn1 = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_belt1',
        output='screen',
        arguments=[
            '-entity', 'belt1',
            '-x', '-0.8', '-y', '0.0', '-z', '0.8',
            '-Y', '1.5708',
            '-topic', '/robot_description_1'
        ]
    )

    # Spawn belt 2 at y=4 (spaced apart)
    spawn2 = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_belt2',
        output='screen',
        arguments=[
            '-entity', 'belt2',
            '-x', '0.8', '-y', '0.0', '-z', '0.8',
            '-Y', '1.5708',
            '-topic', '/robot_description_2'
        ]
    )

    return LaunchDescription([
        gzserver,
        gzclient,
        pub1,
        pub2,
        rsp1,
        rsp2,
        TimerAction(period=5.0, actions=[spawn1]),
        TimerAction(period=6.0, actions=[spawn2]),
    ])
