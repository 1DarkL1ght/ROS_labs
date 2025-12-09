from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'switch_threshold',
            default_value='0.5',
            description='Distance threshold for automatic target switching'
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
        
        TimerAction(
            period=3.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'service', 'call', '/spawn', 'turtlesim/srv/Spawn', 
                         '{x: 2.0, y: 2.0, theta: 0.0, name: "turtle3"}'],
                    output='screen'
                )
            ]
        ),
        
        Node(
            package='ex0402b',
            executable='turtle_tf2_broadcaster',
            name='turtle1_tf2_broadcaster',
            parameters=[{'turtle_name': 'turtle1'}]
        ),
        
        Node(
            package='ex0402b',
            executable='turtle2_tf2_broadcaster',
            name='turtle2_tf2_broadcaster'
        ),
        
        Node(
            package='ex0402b',
            executable='turtle_tf2_broadcaster',
            name='turtle3_tf2_broadcaster',
            parameters=[{'turtle_name': 'turtle3'}]
        ),
        
        Node(
            package='ex0402b',
            executable='target_switcher',
            name='target_switcher',
            output='screen'
        ),
        
        Node(
            package='ex0402b',
            executable='turtle_controller',
            name='turtle_controller',
            output='screen',
            parameters=[{
                'switch_threshold': LaunchConfiguration('switch_threshold')
            }]
        ),
        
        Node(
            package='ex0402b',
            executable='keyboard_listener',
            name='keyboard_listener',
            output='screen'
        ),
        
        Node(
            package='turtlesim',
            executable='turtle_teleop_key',
            name='teleop_key',
            output='screen',
            prefix='xterm -e'
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', 'install/ex0402b/share/ex0402b/rviz/multi_target.rviz']
        )
    ])
