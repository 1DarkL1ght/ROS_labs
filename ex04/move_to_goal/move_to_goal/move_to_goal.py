#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math
import sys

class MoveToGoal(Node):
    def __init__(self, target_x, target_y, target_theta):
        super().__init__('move_to_goal')
        
        self.target_x = target_x
        self.target_y = target_y
        self.target_theta = target_theta
        
        # Текущая позиция черепахи
        self.current_pose = Pose()
        self.has_pose = False
        
        # Публикатор для управления скоростью
        self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        
        # Подписчик для получения текущей позиции
        self.subscription = self.create_subscription(
            Pose,
            '/turtle1/pose',
            self.pose_callback,
            10
        )
        
        # Таймер для управления движением
        self.timer = self.create_timer(0.1, self.control_loop)  # 10 Hz
        
        # Параметры управления
        self.linear_tolerance = 0.05  # метров (уменьшили)
        self.angular_tolerance = 0.02  # радиан (уменьшили)
        self.max_linear_speed = 2.0
        self.max_angular_speed = 2.0
        self.min_linear_speed = 0.1   # минимальная скорость для точного подъезда
        self.min_angular_speed = 0.1
        
        # Состояния управления
        self.state = "TURN_TO_GOAL"  # TURN_TO_GOAL -> MOVE_TO_GOAL -> TURN_TO_FINAL -> DONE
        
        self.get_logger().info(f'Moving to goal: x={target_x}, y={target_y}, theta={target_theta}')

    def pose_callback(self, msg):
        self.current_pose = msg
        self.has_pose = True

    def control_loop(self):
        if not self.has_pose:
            return
            
        twist_msg = Twist()
        
        # Вычисляем ошибки
        dx = self.target_x - self.current_pose.x
        dy = self.target_y - self.current_pose.y
        distance_to_goal = math.sqrt(dx**2 + dy**2)
        
        # Вычисляем желаемый угол к цели
        target_angle = math.atan2(dy, dx)
        angle_error = self.normalize_angle(target_angle - self.current_pose.theta)
        
        # Вычисляем ошибку конечной ориентации
        final_angle_error = self.normalize_angle(self.target_theta - self.current_pose.theta)
        
        # Конечный автомат управления
        if self.state == "TURN_TO_GOAL":
            # Поворачиваем к цели
            angular_speed = self.calculate_angular_speed(angle_error)
            twist_msg.angular.z = angular_speed
            
            if abs(angle_error) < self.angular_tolerance:
                self.state = "MOVE_TO_GOAL"
                self.get_logger().info('Aligned with goal, starting movement')
                
        elif self.state == "MOVE_TO_GOAL":
            # Движемся к цели
            linear_speed = self.calculate_linear_speed(distance_to_goal)
            twist_msg.linear.x = linear_speed
            
            # Небольшая коррекция угла во время движения
            angular_speed = self.calculate_angular_speed(angle_error) * 0.3
            twist_msg.angular.z = angular_speed
            
            if distance_to_goal < self.linear_tolerance:
                self.state = "TURN_TO_FINAL"
                self.get_logger().info('Position reached, adjusting final orientation')
                
        elif self.state == "TURN_TO_FINAL":
            # Корректируем конечную ориентацию
            angular_speed = self.calculate_angular_speed(final_angle_error)
            twist_msg.angular.z = angular_speed
            
            if abs(final_angle_error) < self.angular_tolerance:
                self.state = "DONE"
                twist_msg.linear.x = 0.0
                twist_msg.angular.z = 0.0
                self.get_logger().info('Goal reached!')
                self.timer.cancel()
                
        elif self.state == "DONE":
            twist_msg.linear.x = 0.0
            twist_msg.angular.z = 0.0
        
        # Публикуем команду скорости
        self.publisher_.publish(twist_msg)
        
        # Логируем прогресс (реже, чтобы не засорять вывод)
        if self.get_clock().now().nanoseconds % 5e9 < 1e8:  # Каждые 5 секунд
            self.get_logger().info(f'State: {self.state}, Distance: {distance_to_goal:.3f}, Pos: ({self.current_pose.x:.2f}, {self.current_pose.y:.2f})')

    def calculate_linear_speed(self, distance):
        """Вычисляет линейную скорость с dead-zone и насыщением"""
        if distance > 1.0:
            return self.max_linear_speed
        elif distance > 0.3:
            return max(distance * 1.5, self.min_linear_speed)
        else:
            return max(distance * 1.0, self.min_linear_speed)

    def calculate_angular_speed(self, angle_error):
        """Вычисляет угловую скорость с dead-zone и насыщением"""
        if abs(angle_error) > 0.5:
            return math.copysign(self.max_angular_speed, angle_error)
        elif abs(angle_error) > 0.1:
            return math.copysign(max(abs(angle_error) * 3.0, self.min_angular_speed), angle_error)
        else:
            return math.copysign(max(abs(angle_error) * 2.0, self.min_angular_speed), angle_error)

    def normalize_angle(self, angle):
        """Нормализует угол в диапазон [-pi, pi]"""
        while angle > math.pi:
            angle -= 2.0 * math.pi
        while angle < -math.pi:
            angle += 2.0 * math.pi
        return angle

def main(args=None):
    rclpy.init(args=args)
    
    # Проверяем аргументы командной строки
    if len(sys.argv) != 4:
        print("Usage: ros2 run move_to_goal move_to_goal <x> <y> <theta>")
        print("Example: ros2 run move_to_goal move_to_goal 5.0 5.0 0.0")
        return 1
    
    try:
        target_x = float(sys.argv[1])
        target_y = float(sys.argv[2])
        target_theta = float(sys.argv[3])
    except ValueError:
        print("Error: All parameters must be numbers")
        return 1
    
    # Проверяем допустимость координат
    if target_x < 0 or target_x > 11 or target_y < 0 or target_y > 11:
        print("Error: Coordinates must be in range [0, 11]")
        return 1
    
    node = MoveToGoal(target_x, target_y, target_theta)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Останавливаем черепаху перед выходом
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.angular.z = 0.0
        node.publisher_.publish(stop_msg)
        
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
