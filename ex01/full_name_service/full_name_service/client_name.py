import sys

from full_name_message.srv import FullNameSumService
import rclpy
from rclpy.node import Node


class FullNameClient(Node):

    def __init__(self):
        super().__init__('client_name')
        self.cli = self.create_client(FullNameSumService, 'SummFullName')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')

    def send_request(self, name, first_name, last_name):
        request = FullNameSumService.Request()
        request.name = name
        request.first_name = first_name
        request.last_name = last_name
        return self.cli.call_async(request)


def main():
    rclpy.init()

    client = FullNameClient()
    future = client.send_request(sys.argv[1], sys.argv[2], sys.argv[3])
    rclpy.spin_until_future_complete(client, future)
    response = future.result()
    client.get_logger().info(
        f'Result: {response.full_name}')

    client.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
