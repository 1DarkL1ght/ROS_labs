#!/usr/bin/env python3

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
import sys

from cleaning_robot_interfaces.action import CleaningTask

class CleaningActionClient(Node):
    def __init__(self):
        super().__init__('cleaning_action_client')
        self._action_client = ActionClient(self, CleaningTask, 'cleaning_task')
        self.step = 0
        self.get_logger().info('Cleaning Action Client started')

    def send_goal(self, task_type, area_size=0.0, target_x=0.0, target_y=0.0):
        self.get_logger().info('Waiting for action server...')
        self._action_client.wait_for_server()
        
        goal_msg = CleaningTask.Goal()
        goal_msg.task_type = task_type
        goal_msg.area_size = area_size
        goal_msg.target_x = target_x
        goal_msg.target_y = target_y

        self.get_logger().info('Sending goal...')
        future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rejected :(')
            return
        
        self.get_logger().info('Goal accepted :)')
        
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Task completed: {result.success}')
        self.get_logger().info(f'Cleaned points: {result.cleaned_points}')
        self.get_logger().info(f'Total distance: {result.total_distance:.2f} meters')
        
        # Continue with next task or shutdown
        if hasattr(self, 'task_sequence') and self.task_sequence:
            next_task = self.task_sequence.pop(0)
            self.execute_task(next_task)
        else:
            rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        self.get_logger().info(
            f'Feedback: percent {feedback_msg.feedback.progress_percent}%, '
            f'cleaned {feedback_msg.feedback.current_cleaned_points}, '
            f'pos ({feedback_msg.feedback.current_x:.2f}, {feedback_msg.feedback.current_y:.2f})')


def main(args=None):
    rclpy.init(args=args)
    
    client = CleaningActionClient()
    client.send_goal(task_type='clean_circle', area_size=3.0, target_x=10.0, target_y=10.0)
    
    try:
        rclpy.spin(client)
    except KeyboardInterrupt:
        client.get_logger().info('Task sequence interrupted')
    finally:
        client.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
