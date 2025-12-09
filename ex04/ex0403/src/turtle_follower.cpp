#include <memory>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "geometry_msgs/msg/point.hpp"
#include "turtlesim/msg/pose.hpp"
#include "tf2_ros/transform_broadcaster.h"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"
#include "tf2/utils.h"

class TurtleFollower : public rclcpp::Node
{
public:
    TurtleFollower() : Node("turtle_follower"), tf_buffer_(this->get_clock()), tf_listener_(tf_buffer_)
    {
        // Declare parameter
        this->declare_parameter<double>("delay", 5.0);
        delay_ = this->get_parameter("delay").as_double();
        RCLCPP_INFO(this->get_logger(), "Starting turtle follower with delay: %f seconds", delay_);

        // Publisher for turtle2 velocity
        cmd_vel_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle2/cmd_vel", 10);

        // Subscriber for turtle1 pose
        turtle1_pose_sub_ = this->create_subscription<turtlesim::msg::Pose>(
            "/turtle1/pose", 10,
            std::bind(&TurtleFollower::turtle1_pose_callback, this, std::placeholders::_1));

        // Subscriber for turtle2 pose (to publish its transform and for control)
        turtle2_pose_sub_ = this->create_subscription<turtlesim::msg::Pose>(
            "/turtle2/pose", 10,
            std::bind(&TurtleFollower::turtle2_pose_callback, this, std::placeholders::_1));

        // Timer for control loop
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&TurtleFollower::control_loop, this));

        // Wait for TF data to accumulate
        start_time_ = this->now();
        tf_ready_ = false;
    }

private:
    void turtle1_pose_callback(const turtlesim::msg::Pose::SharedPtr msg)
    {
        // Store turtle1 pose
        turtle1_pose_ = msg;

        // Broadcast transform for turtle1
        geometry_msgs::msg::TransformStamped t;
        t.header.stamp = this->now();
        t.header.frame_id = "world";
        t.child_frame_id = "turtle1";
        t.transform.translation.x = msg->x;
        t.transform.translation.y = msg->y;
        t.transform.translation.z = 0.0;

        // Convert yaw to quaternion
        tf2::Quaternion q;
        q.setRPY(0, 0, msg->theta);
        t.transform.rotation.x = q.x();
        t.transform.rotation.y = q.y();
        t.transform.rotation.z = q.z();
        t.transform.rotation.w = q.w();

        tf_broadcaster_.sendTransform(t);
    }

    void turtle2_pose_callback(const turtlesim::msg::Pose::SharedPtr msg)
    {
        // Store turtle2 pose
        turtle2_pose_ = msg;

        // Broadcast transform for turtle2
        geometry_msgs::msg::TransformStamped t;
        t.header.stamp = this->now();
        t.header.frame_id = "world";
        t.child_frame_id = "turtle2";
        t.transform.translation.x = msg->x;
        t.transform.translation.y = msg->y;
        t.transform.translation.z = 0.0;

        // Convert yaw to quaternion
        tf2::Quaternion q;
        q.setRPY(0, 0, msg->theta);
        t.transform.rotation.x = q.x();
        t.transform.rotation.y = q.y();
        t.transform.rotation.z = q.z();
        t.transform.rotation.w = q.w();

        tf_broadcaster_.sendTransform(t);
        
        // Mark TF as ready after we have some data
        if (!tf_ready_) {
            auto current_time = this->now();
            auto elapsed = (current_time - start_time_).seconds();
            if (elapsed > delay_ + 1.0) {  // Wait extra second to be safe
                tf_ready_ = true;
                RCLCPP_INFO(this->get_logger(), "TF system ready, starting follower behavior");
            }
        }
    }

    void control_loop()
    {
        if (!turtle1_pose_ || !turtle2_pose_ || !tf_ready_) {
            if (!tf_ready_) {
                auto current_time = this->now();
                auto elapsed = (current_time - start_time_).seconds();
                RCLCPP_INFO_THROTTLE(this->get_logger(), *this->get_clock(), 2000, 
                                    "Waiting for TF history to build up... (%f/%f seconds)", elapsed, delay_ + 1.0);
            }
            return;
        }

        try {
            // Get the transform from world to turtle1 at past time
            auto past = this->now() - rclcpp::Duration::from_seconds(delay_);
            
            geometry_msgs::msg::TransformStamped transform;
            try {
                transform = tf_buffer_.lookupTransform(
                    "world", "turtle1", past, rclcpp::Duration::from_seconds(0.1));
            } catch (tf2::ExtrapolationException &ex) {
                RCLCPP_DEBUG(this->get_logger(), "TF2 extrapolation: %s", ex.what());
                return;
            }

            // Extract target position in world frame
            double target_x = transform.transform.translation.x;
            double target_y = transform.transform.translation.y;

            // Get current turtle2 position
            double current_x = turtle2_pose_->x;
            double current_y = turtle2_pose_->y;
            double current_theta = turtle2_pose_->theta;

            // Calculate control command in world coordinates
            auto cmd_vel = geometry_msgs::msg::Twist();

            double dx = target_x - current_x;
            double dy = target_y - current_y;
            double distance = std::sqrt(dx*dx + dy*dy);

            // Calculate desired angle in world frame
            double target_angle_world = std::atan2(dy, dx);
            
            // Calculate angle difference relative to turtle2's current orientation
            double angle_diff = target_angle_world - current_theta;
            
            // Normalize angle to [-pi, pi]
            while (angle_diff > M_PI) angle_diff -= 2 * M_PI;
            while (angle_diff < -M_PI) angle_diff += 2 * M_PI;

            // Only move if we're not too close
            if (distance > 0.1) {
                cmd_vel.linear.x = 1.5 * distance;
                cmd_vel.angular.z = 4.0 * angle_diff;
                
                // Limit the velocities
                cmd_vel.linear.x = std::min(cmd_vel.linear.x, 2.0);
                cmd_vel.angular.z = std::max(std::min(cmd_vel.angular.z, 2.0), -2.0);
            } else {
                // Stop if we're close enough
                cmd_vel.linear.x = 0.0;
                cmd_vel.angular.z = 0.0;
            }

            cmd_vel_pub_->publish(cmd_vel);

        } catch (tf2::TransformException &ex) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000, "TF2 exception: %s", ex.what());
        }
    }

    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle1_pose_sub_;
    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr turtle2_pose_sub_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_pub_;
    rclcpp::TimerBase::SharedPtr timer_;

    tf2_ros::Buffer tf_buffer_;
    tf2_ros::TransformListener tf_listener_;
    tf2_ros::TransformBroadcaster tf_broadcaster_{this};

    turtlesim::msg::Pose::SharedPtr turtle1_pose_;
    turtlesim::msg::Pose::SharedPtr turtle2_pose_;
    double delay_;
    rclcpp::Time start_time_;
    bool tf_ready_;
};

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<TurtleFollower>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}