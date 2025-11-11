cmake_minimum_required(VERSION 3.8)
project(full_name_message)

# По умолчанию используется C++14. Вы можете изменить это при необходимости.
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

# Указываем, где искать CMake-модули (например, Findament_cmake.cmake)
if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Находим необходимые пакеты для сборки.
find_package(geometry_msgs REQUIRED)
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# Объявляем файлы интерфейсов, которые нужно сгенерировать.
rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/FullNameSumService.msg"
  "srv/FullNameSumService.srv"
  DEPENDENCIES geometry_msgs # Add packages that above messages depend on, in this case geometry_msgs for Sphere.msg
)

# Указываем зависимости для сборки.
ament_export_dependencies(rosidl_default_runtime)

# Объявляем зависимости для сборки пакета.
ament_package()
