import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist
import numpy as np
from cv_bridge import CvBridge

class DepthObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('depth_obstacle_avoidance')
        
        self.publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Image,
            '/depth_camera/image',
            self.depth_callback,
            10
        )
        
        # Параметры
        self.linear_speed = 0.25         
        self.stop_distance = 0.9         
        self.central_region_ratio = 0.4   
        
        self.obstacle_detected = False

        self.bridge = CvBridge()
        
        self.timer = self.create_timer(0.1, self.timer_callback)

    def depth_callback(self, msg: Image):
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="32FC1")
            
            h, w = depth_image.shape
            crop_h = int(h * self.central_region_ratio)
            crop_w = int(w * self.central_region_ratio)
            
            center_y = h // 2
            center_x = w // 2
            
            central_region = depth_image[
                center_y - crop_h//2 : center_y + crop_h//2,
                center_x - crop_w//2 : center_x + crop_w//2
            ]
            
            valid_depth = central_region[
                (central_region > 0.05) & (central_region < 100.0)
            ]
            
            if valid_depth.size > 0:
                min_depth = np.min(valid_depth)
                self.obstacle_detected = min_depth < self.stop_distance
            else:
                self.obstacle_detected = False 
                
        except Exception as e:
            self.get_logger().warn(f'Error processing depth image: {e}')
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
    node = DepthObstacleAvoidance()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()