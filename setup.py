import os
from glob import glob
from setuptools import setup, find_packages

package_name = 'aicane_navigation'

setup(
    name=package_name,
    version='0.1.0',
    description='Indoor autonomous navigation system for AiCane robot',
    author='AiCane Team',
    packages=find_packages(),
    # ⭐ 여기가 핵심 수정 사항입니다! (파일들을 ROS가 찾는 위치로 복사)
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch 파일 설치
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Config 파일 설치
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        # Map 파일 설치
        (os.path.join('share', package_name, 'maps'), glob('maps/*.json')),
    ],
    install_requires=[
        'setuptools',  # ROS2 필수
        'numpy>=1.20.0',
        'pyyaml>=5.4.0',
        'pyserial>=3.5',
    ],
    extras_require={
        'lidar': ['rplidar>=1.0.0'],
        'dev': ['pytest>=7.0.0', 'black>=22.0.0'],
    },
    entry_points={
        'console_scripts': [
            'aicane-navigate=scripts.navigate:main',
            'aicane-calibrate=scripts.calibrate:main',
            'aicane-test-sensors=scripts.test_sensors:main',
        ],
    },
    python_requires='>=3.8',
    zip_safe=True,
)