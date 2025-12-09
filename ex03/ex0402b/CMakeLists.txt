cmake_minimum_required(VERSION 3.8)
project(ex0402b)

# Default to C++17:
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Finding dependencies:
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Generating messages:
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/CurrentTarget.msg"
  DEPENDENCIES geometry_msgs std_msgs
)

# Getting the typesupport target for our messages:
rosidl_get_typesupport_target(cpp_typesupport_target ${PROJECT_NAME} "rosidl_typesupport_cpp")

# Including directories:
include_directories(include)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_cpp)

# Creating executables:
add_executable(target_switcher src/target_switcher.cpp)
ament_target_dependencies(target_switcher 
  rclcpp geometry_msgs tf2_ros tf2_geometry_msgs std_msgs
)

add_executable(turtle_controller src/turtle_controller.cpp)
ament_target_dependencies(turtle_controller 
  rclcpp geometry_msgs tf2_ros tf2_geometry_msgs std_msgs std_srvs turtlesim
)
# Linking with the typesupport target:
target_link_libraries(turtle_controller ${cpp_typesupport_target})

add_executable(turtle_tf2_broadcaster src/turtle_tf2_broadcaster.cpp)
ament_target_dependencies(turtle_tf2_broadcaster 
  rclcpp geometry_msgs tf2_ros tf2_geometry_msgs std_msgs turtlesim
)

add_executable(turtle2_tf2_broadcaster src/turtle2_tf2_broadcaster.cpp)
ament_target_dependencies(turtle2_tf2_broadcaster 
  rclcpp geometry_msgs tf2_ros tf2_geometry_msgs std_msgs turtlesim
)

add_executable(keyboard_listener src/keyboard_listener.cpp)
ament_target_dependencies(keyboard_listener 
  rclcpp std_msgs std_srvs
)

# Installing executables:
install(TARGETS
  target_switcher
  turtle_controller
  turtle_tf2_broadcaster
  turtle2_tf2_broadcaster
  keyboard_listener
  DESTINATION lib/${PROJECT_NAME}
)

# Installing launch files:
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

# Installing RViz config:
install(DIRECTORY rviz
  DESTINATION share/${PROJECT_NAME}
)

# Installing message directory:
install(DIRECTORY msg
  DESTINATION share/${PROJECT_NAME}
)

# Installing include directory:
install(DIRECTORY include/
  DESTINATION include
)

# Exporting dependencies:
ament_export_dependencies(
  rclcpp
  geometry_msgs
  turtlesim
  tf2_ros
  tf2_geometry_msgs
  std_msgs
  std_srvs
  rosidl_default_runtime
)

ament_package()
