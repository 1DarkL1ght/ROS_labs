from full_name_message.srv import FullNameSumService

import rclpy
from rclpy.node import Node


class FullNameService(Node):

    def __init__(self):
        super().__init__('service_name')
        self.srv = self.create_service(FullNameSumService, 'SummFullName', self.full_name_callback)

    def full_name_callback(self, request, response):
        name = request.name
        first_name = request.first_name
        last_name = request.last_name

        full_name = f"{name} {first_name} {last_name}"

        response.full_name = full_name

        self.get_logger().info(f"Recieved: {name}, {first_name}, {last_name}. Sent: {full_name}")

        return response


def main():
    rclpy.init()

    full_name_service = FullNameService()

    rclpy.spin(full_name_service)

    rclpy.shutdown()


if __name__ == '__main__':
    main()
