#include <memory>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <turtlesim/msg/pose.hpp>
#include "ex0402b/utilities.hpp"

class TurtleTf2Broadcaster : public rclcpp::Node
{
public:
  TurtleTf2Broadcaster()
  : Node("turtle_tf2_broadcaster")
  {
    this->declare_parameter<std::string>("turtle_name", "turtle1");
    turtle_name_ = this->get_parameter("turtle_name").as_string();
    
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
    
    subscription_ = this->create_subscription<turtlesim::msg::Pose>(
      "/" + turtle_name_ + "/pose", 1,
      std::bind(&TurtleTf2Broadcaster::handle_turtle_pose, this, std::placeholders::_1));
    
    RCLCPP_INFO(this->get_logger(), "Started turtle_tf2_broadcaster for %s", turtle_name_.c_str());
  }

private:
  void handle_turtle_pose(const std::shared_ptr<turtlesim::msg::Pose> msg)
  {
    geometry_msgs::msg::TransformStamped t;
    
    t.header.stamp = this->get_clock()->now();
    t.header.frame_id = "world";
    t.child_frame_id = turtle_name_;
    
    t.transform.translation.x = msg->x;
    t.transform.translation.y = msg->y;
    t.transform.translation.z = 0.0;
    
    auto q = ex0402b::quaternion_from_euler(0, 0, msg->theta);
    t.transform.rotation = q;
    
    tf_broadcaster_->sendTransform(t);
  }

  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr subscription_;
  std::string turtle_name_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<TurtleTf2Broadcaster>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
