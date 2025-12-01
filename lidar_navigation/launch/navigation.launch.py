"""
Launch All Navigation Nodes
"""

from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='lidar_navigation',
            executable='robokit_driver',
            name='driver',
            output='screen'
        ),
        Node(
            package='lidar_navigation',
            executable='localization',
            name='localization',
            output='screen'
        ),
        Node(
            package='lidar_navigation',
            executable='controller',
            name='controller',
            output='screen'
        ),
        Node(
            package='lidar_navigation',
            executable='path_manager',
            name='path_manager',
            output='screen'
        ),
    ])

