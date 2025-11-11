#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
import math
import time
import threading

from cleaning_robot_interfaces.action import CleaningTask


class CleaningActionServer(Node):
    def __init__(self):
        super().__init__('cleaning_action_server')
        
        self._action_server = ActionServer(self, CleaningTask, 'cleaning_task', self.execute_callback)
        self.current_pose = Pose()
        self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)
        self.vel_pub = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
        self.cleaned_points = 0.0
        
        self.get_logger().info('Cleaning Action Server started')

    def pose_callback(self, msg):
        self.current_pose = msg

    def update_cleaned_points(self, last_x, last_y):
        rclpy.spin_once(self, timeout_sec=0.01)
        dx = self.current_pose.x - last_x
        dy = self.current_pose.y - last_y
        dist = math.sqrt(dx**2 + dy**2)
        self.cleaned_points += dist

    def move_to_point(self, target_x, target_y, timeout=10.0):
        """Движение к конкретной точке"""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            dx = target_x - self.current_pose.x
            dy = target_y - self.current_pose.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < 0.1:
                return True
            
            angle_to_target = math.atan2(dy, dx)
            angle_diff = angle_to_target - self.current_pose.theta
            
            # Нормализуем угол
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            twist = Twist()
            
            if abs(angle_diff) > 0.2:
                # Сначала поворачиваемся
                twist.angular.z = 2.0 if angle_diff > 0 else -2.0
            else:
                # Двигаемся к цели
                twist.linear.x = min(1.5, distance * 2.0)
                twist.angular.z = 4.0 * angle_diff
            
            self.vel_pub.publish(twist)
            rclpy.spin_once(self, timeout_sec=0.1)
        
        return False

    def move_straight(self, target_x, target_y, distance_to_travel, timeout=10.0):
        """Движение по прямой на определенное расстояние"""
        start_time = time.time()
        start_x, start_y = self.current_pose.x, self.current_pose.y
        
        # Вычисляем целевой угол
        dx = target_x - start_x
        dy = target_y - start_y
        target_angle = math.atan2(dy, dx)
        
        while (time.time() - start_time) < timeout:
            # Текущее пройденное расстояние
            current_dx = self.current_pose.x - start_x
            current_dy = self.current_pose.y - start_y
            current_distance = math.sqrt(current_dx**2 + current_dy**2)
            
            if current_distance >= distance_to_travel:
                return True
            
            # Коррекция угла
            angle_diff = target_angle - self.current_pose.theta
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi
            
            twist = Twist()
            twist.linear.x = 1.5
            twist.angular.z = 4.0 * angle_diff
            
            self.vel_pub.publish(twist)
            rclpy.spin_once(self, timeout_sec=0.1)
        
        return False

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing goal...')
        feedback_msg = CleaningTask.Feedback()
        result = CleaningTask.Result()
        
        # Сбрасываем счетчик перед выполнением задачи
        self.cleaned_points = 0.0
        
        task_type = goal_handle.request.task_type

        if task_type == 'clean_square':
            square_side = goal_handle.request.area_size
            self.get_logger().info(f'Cleaning square with side: {square_side}')
            
            # Определяем границы квадрата относительно текущей позиции
            half_side = square_side / 2.0
            center_x, center_y = self.current_pose.x, self.current_pose.y
            
            min_x = max(0.5, center_x - half_side)
            max_x = min(10.5, center_x + half_side)
            min_y = max(0.5, center_y - half_side)
            max_y = min(10.5, center_y + half_side)
            
            # Параметры зигзагообразного паттерна
            resolution = 0.3  # расстояние между линиями
            current_y = min_y
            direction = 1  # 1: вправо, -1: влево
            
            # Расчет общего количества проходов для прогресса
            total_passes = int((max_y - min_y) / resolution) + 1
            completed_passes = 0
            
            # Двигаемся к начальной точке (нижний левый угол)
            if not self.move_to_point(min_x, min_y):
                self.get_logger().warn('Failed to reach starting point')
            
            # Зигзагообразное движение по всей площади
            while min_y <= current_y <= max_y:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.success = False
                    return result
                
                # Определяем начальную и конечную точки для этого прохода
                if direction == 1:
                    start_x = min_x
                    end_x = max_x
                else:
                    start_x = max_x
                    end_x = min_x
                
                # Сохраняем позицию до движения
                last_x, last_y = self.current_pose.x, self.current_pose.y
                
                # Двигаемся к началу строки
                if not self.move_to_point(start_x, current_y):
                    self.get_logger().warn(f'Failed to reach start of row at y={current_y:.2f}')
                    continue
                
                # Двигаемся по всей строке
                line_distance = abs(end_x - start_x)
                if not self.move_straight(end_x, current_y, line_distance):
                    self.get_logger().warn(f'Failed to complete row at y={current_y:.2f}')
                    continue
                
                # Обновляем счетчик убранных точек
                self.update_cleaned_points(last_x, last_y)
                
                completed_passes += 1
                progress = min(100, int((completed_passes / total_passes) * 100))
                
                # Отправляем feedback
                feedback_msg.progress_percent = progress
                feedback_msg.current_cleaned_points = int(self.cleaned_points)
                feedback_msg.current_x = self.current_pose.x
                feedback_msg.current_y = self.current_pose.y
                goal_handle.publish_feedback(feedback_msg)
                
                self.get_logger().info(f'Completed row {completed_passes}/{total_passes} at y={current_y:.2f}')
                
                # Переходим к следующей строке
                current_y += resolution
                direction *= -1  # меняем направление
            
            # Останавливаемся
            stop_twist = Twist()
            self.vel_pub.publish(stop_twist)

        elif task_type == 'clean_circle':         
            radius = goal_handle.request.area_size
            speed = 1.5
            start_radius = 0.1
            
            self.get_logger().info(f'Cleaning circle with radius: {radius}')
            
            while start_radius <= radius:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.success = False
                    return result
                
                center_x = self.current_pose.x
                center_y = self.current_pose.y
                ang_speed = speed / max(start_radius, 0.1)  # избегаем деления на 0
                
                twist = Twist()
                twist.linear.x = speed
                twist.angular.z = ang_speed
                self.vel_pub.publish(twist)

                time.sleep(1)
                self.update_cleaned_points(center_x, center_y)
                
                feedback_msg.progress_percent = min(int((start_radius / radius) * 100), 100)
                feedback_msg.current_cleaned_points = int(self.cleaned_points)
                feedback_msg.current_x = self.current_pose.x 
                feedback_msg.current_y = self.current_pose.y
                goal_handle.publish_feedback(feedback_msg)

                start_radius += 0.05

            # Останавливаемся
            twist = Twist()
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.vel_pub.publish(twist)
            
        elif task_type == 'return_home':
            target_x = goal_handle.request.target_x
            target_y = goal_handle.request.target_y
            
            self.get_logger().info(f'Returning home to: ({target_x}, {target_y})')
            
            last_x, last_y = self.current_pose.x, self.current_pose.y
            
            dx = target_x - self.current_pose.x
            dy = target_y - self.current_pose.y
            distance = math.sqrt(dx**2 + dy**2)
            
            while distance > 0.1:
                if goal_handle.is_cancel_requested:
                    goal_handle.canceled()
                    result.success = False
                    return result
                    
                feedback_msg.current_x = self.current_pose.x
                feedback_msg.current_y = self.current_pose.y
                goal_handle.publish_feedback(feedback_msg)
                
                twist = Twist()
                dx = target_x - self.current_pose.x
                dy = target_y - self.current_pose.y
                distance = math.sqrt(dx**2 + dy**2)
                angle_to_target = math.atan2(dy, dx)
                angle_diff = angle_to_target - self.current_pose.theta
                
                # Нормализуем угол
                while angle_diff > math.pi:
                    angle_diff -= 2 * math.pi
                while angle_diff < -math.pi:
                    angle_diff += 2 * math.pi
                
                twist.linear.x = min(1.0, distance * 2.0)
                twist.angular.z = 4.0 * angle_diff
                self.vel_pub.publish(twist)
                rclpy.spin_once(self, timeout_sec=0.1)
            
            # Останавливаемся
            stop_twist = Twist()
            self.vel_pub.publish(stop_twist)
            self.update_cleaned_points(last_x, last_y)
            
        else:
            self.get_logger().info('Unknown task type...')
            goal_handle.abort()
            result.success = False
            return result

        goal_handle.succeed()
        result.success = True
        result.total_distance = self.cleaned_points
        result.cleaned_points = int(self.cleaned_points)
        
        self.get_logger().info(f'Task completed successfully! Cleaned points: {result.cleaned_points}')
        return result


def main(args=None):
    rclpy.init(args=args)
    cleaning_action_server = CleaningActionServer()
    
    try:
        rclpy.spin(cleaning_action_server)
    except KeyboardInterrupt:
        pass
    finally:
        # Останавливаем черепаху
        stop_msg = Twist()
        stop_msg.linear.x = 0.0
        stop_msg.angular.z = 0.0
        cleaning_action_server.vel_pub.publish(stop_msg)
        
        cleaning_action_server.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()