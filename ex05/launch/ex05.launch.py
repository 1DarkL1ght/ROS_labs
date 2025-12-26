from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory
import xacro

def generate_launch_description():
    pkg_dir = get_package_share_directory('robot_gazebo_sim')
    xacro_file = os.path.join(pkg_dir, 'urdf', 'my_robot.gazebo.xacro')
    robot_description = xacro.process_file(xacro_file).toxml()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(
                get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            )
        ]),
        launch_arguments={'gz_args': '-r gpu_lidar_sensor.sdf'}.items()
    )

    robot_state = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
    )

    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description',
                  '-name', 'differential_robot_8w',
                  '-z', '0.3',
                  '-x', '0', '-y', '0'],
        output='screen'
    )

    tf_lidar = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0','0','0','0','0','0','lidar_link','differential_robot_8w/lidar_link/lidar_sensor']
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            '/model/differential_robot_8w/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/depth_camera/image@sensor_msgs/msg/Image[gz.msgs.Image',
        ],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    avoidance_node = Node(
        package='robot_gazebo_sim',
        executable='depth_obstacle_avoidance',
        name='depth_obstacle_avoidance',
        output='screen'
    )

    rviz_config = os.path.join(pkg_dir, 'rviz', 'robot_depth_camera.rviz')
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': True}],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state,
        spawn,
        tf_lidar,
        bridge,
        avoidance_node,
        rviz,
    ])