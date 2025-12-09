#include <rclcpp/rclcpp.hpp>
#include <std_srvs/srv/empty.hpp>
#include <iostream>
#include <thread>
#include <atomic>
#include <termios.h>
#include <unistd.h>
#include <fcntl.h>

class KeyboardListener : public rclcpp::Node
{
public:
  KeyboardListener()
  : Node("keyboard_listener"), key_thread_running_(false)
  {
    switch_client_ = this->create_client<std_srvs::srv::Empty>("/switch_target");
    
    RCLCPP_INFO(this->get_logger(), "Keyboard listener started");
    RCLCPP_INFO(this->get_logger(), "Press 'n' to switch target manually");
    RCLCPP_INFO(this->get_logger(), "Or use: ros2 service call /switch_target std_srvs/srv/Empty");

    try {
      key_thread_running_ = true;
      key_thread_ = std::thread(&KeyboardListener::keyboard_thread, this);
      RCLCPP_INFO(this->get_logger(), "Keyboard input enabled");
    } catch (const std::exception& e) {
      RCLCPP_WARN(this->get_logger(), "Keyboard input not available: %s", e.what());
      RCLCPP_INFO(this->get_logger(), "You can still use service call for manual switching");
    }
  }

  ~KeyboardListener() {
    key_thread_running_ = false;
    if (key_thread_.joinable()) {
      key_thread_.join();
    }
  }

private:
  void keyboard_thread() {

    struct termios old_tio, new_tio;
    if (tcgetattr(STDIN_FILENO, &old_tio) != 0) {
      throw std::runtime_error("Cannot get terminal attributes");
    }

    new_tio = old_tio;
    new_tio.c_lflag &= ~(ICANON | ECHO);
    if (tcsetattr(STDIN_FILENO, TCSANOW, &new_tio) != 0) {
      throw std::runtime_error("Cannot set terminal attributes");
    }

    int flags = fcntl(STDIN_FILENO, F_GETFL, 0);
    fcntl(STDIN_FILENO, F_SETFL, flags | O_NONBLOCK);

    RCLCPP_INFO(this->get_logger(), "Listening for keyboard input...");

    while (rclcpp::ok() && key_thread_running_) {
      char c;
      int bytes_read = read(STDIN_FILENO, &c, 1);
      
      if (bytes_read > 0) {
        if (c == 'n' || c == 'N') {
          switch_target();
        }
      }
      
      std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    tcsetattr(STDIN_FILENO, TCSANOW, &old_tio);
    fcntl(STDIN_FILENO, F_SETFL, flags);
  }

  void switch_target()
  {
    if (!switch_client_->wait_for_service(std::chrono::seconds(1))) {
      RCLCPP_WARN(this->get_logger(), "Service /switch_target not available");
      return;
    }

    auto request = std::make_shared<std_srvs::srv::Empty::Request>();
    auto future = switch_client_->async_send_request(request);
    
    RCLCPP_INFO(this->get_logger(), "Target switch command sent via keyboard");
  }

  rclcpp::Client<std_srvs::srv::Empty>::SharedPtr switch_client_;
  std::thread key_thread_;
  std::atomic_bool key_thread_running_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<KeyboardListener>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
