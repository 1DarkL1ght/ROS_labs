#include <memory>
#include <cmath>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>

class TargetSwitcher : public rclcpp::Node
{
public:
  TargetSwitcher()
  : Node("target_switcher")
  {
    this->declare_parameter<double>("radius", 2.0);
    radius_ = this->get_parameter("radius").as_double();
    
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
    
    timer_ = this->create_wall_timer(
      std::chrono::milliseconds(100),
      std::bind(&TargetSwitcher::broadcast_targets, this));
    
    start_time_ = this->get_clock()->now();
    
    RCLCPP_INFO(this->get_logger(), "Target switcher started");
  }

private:
  void broadcast_targets()
  {
    auto current_time = this->get_clock()->now();
    auto elapsed_time = (current_time - start_time_).seconds();
    
    double angle1 = elapsed_time;
    broadcast_carrot_frame("turtle1", "carrot1", angle1, current_time);
    
    double angle2 = elapsed_time * 1.5;
    broadcast_carrot_frame("turtle3", "carrot2", angle2, current_time);
    
    broadcast_static_frame(current_time);
  }

  void broadcast_carrot_frame(const std::string& parent_frame, const std::string& child_frame, 
                             double angle, rclcpp::Time current_time)
  {
    geometry_msgs::msg::TransformStamped t;
    
    t.header.stamp = current_time;
    t.header.frame_id = parent_frame;
    t.child_frame_id = child_frame;
    
    double x = radius_ * std::cos(angle);
    double y = radius_ * std::sin(angle);
    t.transform.translation.x = x;
    t.transform.translation.y = y;
    t.transform.translation.z = 0.0;
    
    t.transform.rotation.x = 0.0;
    t.transform.rotation.y = 0.0;
    t.transform.rotation.z = 0.0;
    t.transform.rotation.w = 1.0;
    
    tf_broadcaster_->sendTransform(t);
  }

  void broadcast_static_frame(rclcpp::Time current_time)
  {
    geometry_msgs::msg::TransformStamped t;
    
    t.header.stamp = current_time;
    t.header.frame_id = "world";
    t.child_frame_id = "static_target";
    
    t.transform.translation.x = 8.0;
    t.transform.translation.y = 2.0;
    t.transform.translation.z = 0.0;
    
    t.transform.rotation.x = 0.0;
    t.transform.rotation.y = 0.0;
    t.transform.rotation.z = 0.0;
    t.transform.rotation.w = 1.0;
    
    tf_broadcaster_->sendTransform(t);
  }

  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::TimerBase::SharedPtr timer_;
  rclcpp::Time start_time_;
  double radius_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<TargetSwitcher>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
