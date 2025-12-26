import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
import math

class ObstacleAvoidanceNode(Node):
    def __init__(self):
        super().__init__('lidar_obstacle_avoidance')
        
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )
        
        self.linear_speed = 0.3 
        self.stop_distance = 1.0 
        self.front_angle = 30 
        
        self.obstacle_detected = False
        
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        
    def scan_callback(self, msg):
        ranges = msg.ranges
        min_distance = float('inf')
        
        angle_min = msg.angle_min
        angle_increment = msg.angle_increment
        num_ranges = len(ranges)
        front_angle_rad = math.radians(self.front_angle)
        
        for i in range(num_ranges):
            angle = angle_min + i * angle_increment
            if abs(angle) <= front_angle_rad:
                if ranges[i] > 0 and ranges[i] < min_distance: 
                    min_distance = ranges[i]
        
        if min_distance < self.stop_distance:
            self.obstacle_detected = True
        else:
            self.obstacle_detected = False

    def timer_callback(self):
        msg = Twist()
        if not self.obstacle_detected:
            msg.linear.x = self.linear_speed
            msg.angular.z = 0.0
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
        
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidanceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()