from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'delay',
            default_value='5.0',
            description='Time delay in seconds for turtle follower'
        ),
        
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim'
        ),
        
        TimerAction(
            period=2.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn', 
                         '{x: 5.0, y: 5.0, theta: 0.0, name: "turtle2"}'],
                    output='screen'
                )
            ]
        ),

        Node(
            package='turtlesim',
            executable='turtle_teleop_key',
            name='teleop_key',
            output='screen',
            prefix='xterm -e'
        ),
        
        Node(
            package='ex0403',
            executable='turtle_follower',
            name='turtle_follower',
            parameters=[{
                'delay': LaunchConfiguration('delay')
            }]
        ),
    ])
