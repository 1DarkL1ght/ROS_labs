#include <memory>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <turtlesim/msg/pose.hpp>
#include "ex0402b/utilities.hpp"

class Turtle2Tf2Broadcaster : public rclcpp::Node
{
public:
  Turtle2Tf2Broadcaster()
  : Node("turtle2_tf2_broadcaster")
  {
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this);
    
    subscription_ = this->create_subscription<turtlesim::msg::Pose>(
      "/turtle2/pose", 1,
      std::bind(&Turtle2Tf2Broadcaster::handle_turtle_pose, this, std::placeholders::_1));
    
    RCLCPP_INFO(this->get_logger(), "Started turtle2_tf2_broadcaster");
  }

private:
  void handle_turtle_pose(const std::shared_ptr<turtlesim::msg::Pose> msg)
  {
    geometry_msgs::msg::TransformStamped t;
    
    t.header.stamp = this->get_clock()->now();
    t.header.frame_id = "world";
    t.child_frame_id = "turtle2";
    
    t.transform.translation.x = msg->x;
    t.transform.translation.y = msg->y;
    t.transform.translation.z = 0.0;
    
    auto q = ex0402b::quaternion_from_euler(0, 0, msg->theta);
    t.transform.rotation = q;
    
    tf_broadcaster_->sendTransform(t);
  }

  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_;
  rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr subscription_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<Turtle2Tf2Broadcaster>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
