from setuptools import setup

package_name = 'cleaning_robot'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='georg',
    maintainer_email='e.maksimov3@g.nsu.ru',
    description='Cleaning robot action server and client',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cleaning_action_server = cleaning_robot.cleaning_action_server:main',
            'cleaning_action_client = cleaning_robot.cleaning_action_client:main',
        ],
    },
)
