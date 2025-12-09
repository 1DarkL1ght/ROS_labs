#include <memory>
#include <string>
#include <cmath>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <tf2_ros/transform_listener.h>
#include <tf2_ros/buffer.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/empty.hpp>
#include <turtlesim/msg/pose.hpp>

#include "ex0402b/msg/current_target.hpp"

class TurtleController : public rclcpp::Node
{
public:
  TurtleController()
  : Node("turtle_controller"), tf_buffer_(this->get_clock()), tf_listener_(tf_buffer_)
  {
    this->declare_parameter<double>("switch_threshold", 0.5);
    switch_threshold_ = this->get_parameter("switch_threshold").as_double();
    
    publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle2/cmd_vel", 1);
    target_pub_ = this->create_publisher<ex0402b::msg::CurrentTarget>("/current_target", 10);
    
    switch_service_ = this->create_service<std_srvs::srv::Empty>(
      "/switch_target",
      std::bind(&TurtleController::switch_target_callback, this, 
                std::placeholders::_1, std::placeholders::_2));
    
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      std::bind(&TurtleController::control_loop, this));
    
    targets_ = {"carrot1", "carrot2", "static_target"};
    current_target_index_ = 0;
    last_switch_time_ = this->get_clock()->now();
    
    RCLCPP_INFO(this->get_logger(), "Turtle controller started. Initial target: %s", 
                get_current_target().c_str());
    RCLCPP_INFO(this->get_logger(), "Switch target: ros2 service call /switch_target std_srvs/srv/Empty");
  }

private:
  std::string get_current_target()
  {
    return targets_[current_target_index_];
  }

  void switch_to_next_target()
  {
    current_target_index_ = (current_target_index_ + 1) % targets_.size();
    last_switch_time_ = this->get_clock()->now();
    RCLCPP_INFO(this->get_logger(), "Switched to target: %s", get_current_target().c_str());
  }

  void switch_target_callback(
    const std::shared_ptr<std_srvs::srv::Empty::Request>,
    std::shared_ptr<std_srvs::srv::Empty::Response>)
  {
    switch_to_next_target();
  }

  void control_loop()
  {
    std::string current_target = get_current_target();
    
    geometry_msgs::msg::TransformStamped transform;
    try {
      transform = tf_buffer_.lookupTransform(
        "turtle2", current_target, tf2::TimePointZero);
    } catch (tf2::TransformException & ex) {
      RCLCPP_DEBUG(this->get_logger(), "Could not transform turtle2 to %s: %s", 
                  current_target.c_str(), ex.what());
      return;
    }

    double dx = transform.transform.translation.x;
    double dy = transform.transform.translation.y;
    double distance = std::sqrt(dx * dx + dy * dy);
    
    auto now = this->get_clock()->now();
    auto time_since_switch = (now - last_switch_time_).seconds();
    
    if (distance < switch_threshold_ && time_since_switch > 3.0) {
      RCLCPP_INFO(this->get_logger(), "Target %s reached (distance: %.2f), switching to next target", 
                  current_target.c_str(), distance);
      switch_to_next_target();
      return;
    }

    double angle_to_target = std::atan2(dy, dx);
    
    geometry_msgs::msg::Twist msg;
    
    msg.angular.z = 4.0 * angle_to_target;
    
    double base_speed = 1.5;
    if (distance > 2.0) {
      msg.linear.x = base_speed;
    } else if (distance > 0.5) {
      msg.linear.x = base_speed * (distance / 2.0);
    } else {
      msg.linear.x = 0.1;
    }
    
    msg.linear.x = std::min(msg.linear.x, 2.0);
    msg.angular.z = std::max(std::min(msg.angular.z, 2.0), -2.0);
    
    publisher_->publish(msg);
    
    auto target_msg = ex0402b::msg::CurrentTarget();
    target_msg.target_name = current_target;
    
    try {
      auto transform_target = tf_buffer_.lookupTransform(
        "world", current_target, tf2::TimePointZero);
      target_msg.target_x = transform_target.transform.translation.x;
      target_msg.target_y = transform_target.transform.translation.y;
    } catch (tf2::TransformException & ex) {
      RCLCPP_DEBUG(this->get_logger(), "Could not transform world to %s: %s", 
                  current_target.c_str(), ex.what());
      target_msg.target_x = 0.0;
      target_msg.target_y = 0.0;
    }
    
    target_msg.distance_to_target = distance;
    target_pub_->publish(target_msg);
    
    /*
    static int log_counter = 0;
    if (log_counter++ % 50 == 0) {
      RCLCPP_INFO(this->get_logger(), "Current target: %s, distance: %.2f, linear: %.2f, angular: %.2f",
                  current_target.c_str(), distance, msg.linear.x, msg.angular.z);
    }
    */
  }

  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
  rclcpp::Publisher<ex0402b::msg::CurrentTarget>::SharedPtr target_pub_;
  rclcpp::Service<std_srvs::srv::Empty>::SharedPtr switch_service_;
  rclcpp::TimerBase::SharedPtr timer_;
  
  std::vector<std::string> targets_;
  size_t current_target_index_;
  double switch_threshold_;
  rclcpp::Time last_switch_time_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<TurtleController>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
