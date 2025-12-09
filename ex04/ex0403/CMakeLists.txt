cmake_minimum_required(VERSION 3.8)
project(ex0403)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(turtlesim REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2 REQUIRED)

# Create executable
add_executable(turtle_follower src/turtle_follower.cpp)

# Specify libraries to link
ament_target_dependencies(turtle_follower
  rclcpp
  geometry_msgs
  turtlesim 
  tf2_ros
  tf2_geometry_msgs
  tf2
)

# Install executable
install(TARGETS
  turtle_follower
  DESTINATION lib/${PROJECT_NAME}
)
    
# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}
)

ament_package()