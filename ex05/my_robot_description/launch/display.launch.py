import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    pkg_name = 'my_robot_description'
    urdf_file_name = '01-myfirst.urdf'

    pkg_share = FindPackageShare(pkg_name)
    urdf_path = PathJoinSubstitution([pkg_share, 'urdf', urdf_file_name])

    install_dir = get_package_share_directory(pkg_name)

    try:
        urdf_tutorial_path = get_package_share_directory('urdf_tutorial')
        gz_resource_path = os.path.dirname(urdf_tutorial_path)
    except:
        gz_resource_path = os.path.dirname(install_dir)

    gz_resource_path += ":" + os.path.dirname(install_dir)

    path_to_my_models = '/home/vlada/ros2_ws/src/my_robot_description'
    gz_resource_path += ":" + path_to_my_models

    resource_env = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=gz_resource_path
    )

    robot_description_content = Command(['xacro ', urdf_path])
    robot_description = {'robot_description': robot_description_content}

    ros_gz_sim_pkg = get_package_share_directory('ros_gz_sim')
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_pkg, 'launch', 'gz_sim.launch.py')
        ),
        # launch_arguments={'gz_args': '-r /home/vlada/ros2_ws/src/my_robot_description/urdf/my_world.sdf'}.items(),
        # launch_arguments={'gz_args': '-r -v 4 --render-engine ogre /home/vlada/ros2_ws/src/my_robot_description/urdf/test_lidar.sdf'}.items(),
        launch_arguments={'gz_args': '-r gpu_lidar_sensor.sdf'}.items(),
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',
            '-name', 'my_robot',
            '-z', '0.2'
        ],
        output='screen'
    )

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description] 
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry@gz.msgs.Odometry',
            '/tf@tf2_msgs/msg/TFMessage@gz.msgs.Pose_V'
        ],
        output='screen'
    )

    rviz_config_path = PathJoinSubstitution([pkg_share, 'rviz', 'urdf.rviz'])
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_config_path],
        output='screen'
    )

    return LaunchDescription([
        resource_env,
        gazebo,
        node_robot_state_publisher,
        spawn_entity,
        bridge,
        rviz,
        # Node(
        #     package="my_robot_description",
        #     executable="controller",
        #     name="controller"
        # )
        # Node(
        #     package="my_robot_description",
        #     executable="stopper",
        #     name="stopper"
        # )
        Node(
            package="my_robot_description",
            executable="depth_stopper",
            name="depth_stopper"
        )
    ])