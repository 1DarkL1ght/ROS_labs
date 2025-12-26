from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ex01'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'urdf'),
            glob(os.path.join('urdf', '*.xacro'))),
        (os.path.join('share', package_name, 'rviz'),
            glob(os.path.join('rviz', '*.rviz'))),
    ],
    entry_points={
        'console_scripts': [
        ],
    },
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='georg',
    maintainer_email='e.maksimov3@g.nsu.ru',
    description='Lidar',
    license='Apache-2.0',
)
