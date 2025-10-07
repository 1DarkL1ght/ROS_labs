# Copyright 2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node

from std_msgs.msg import String

from geometry_msgs.msg import Twist

class TextToCmdVel(Node):

	def __init__(self):
		super().__init__("text_to_cmd_vel")
        
		self.subscription = self.create_subscription(String, '/cmd_text', self.cmd_vel_text_callback, 10)
		self.publisher_ = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

		self.linear_speed = 1.0
		self.angular_speed = 1.5

	def cmd_vel_text_callback(self, msg):
		command = msg.data.lower().strip()
		twist_msg = Twist()
		if command == "move_forward":
			twist_msg.linear.x = self.linear_speed
			self.get_logger().info(f'Command received: {command} -> moving forward')

		elif command == "move_backward":
			twist_msg.linear.x = -self.linear_speed
			self.get_logger().info(f'Command received: {command} -> moving backward')

		elif command == "turn_left":
			twist_msg.angular.z = self.angular_speed
			self.get_logger().info(f'Command received: {command} -> turning left')

		elif command == "turn_right":
			twist_msg.angular.z = -self.angular_speed
			self.get_logger().info(f'Command received: {command} -> turning right')

		else:
			self.get_logger().warn(f'Unknown command: {command}')
			return

		self.publisher_.publish(twist_msg)


def main(args=None):
    rclpy.init(args=args)

    node = TextToCmdVel()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

