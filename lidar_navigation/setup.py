from setuptools import setup
import os
from glob import glob

package_name = 'lidar_navigation'

setup(
    name=package_name,
    version='1.0.0',
    # 📦 하위 폴더 없이 단일 패키지만
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # launch 폴더
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # path.json
        (os.path.join('share', package_name), ['path.json']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AiCane',
    maintainer_email='aicane@robot.com',
    description='LiDAR Navigation System',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # ⭐ nodes. 제거! (하위 폴더가 없으므로)
            'robokit_driver = lidar_navigation.robokit_driver_node:main',
            'localization = lidar_navigation.localization_node:main',
            'controller = lidar_navigation.controller_node:main',
            'path_manager = lidar_navigation.path_manager:main',
        ],
    },
)