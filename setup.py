from setuptools import setup, find_packages

setup(
    name='aicane_navigation',
    version='0.1.0',
    description='Indoor autonomous navigation system for AiCane robot',
    author='AiCane Team',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20.0',
        'pyyaml>=5.4.0',
        'pyserial>=3.5',
    ],
    extras_require={
        'lidar': [
            'rplidar>=1.0.0',
        ],
        'dev': [
            'pytest>=7.0.0',
            'black>=22.0.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'aicane-navigate=scripts.navigate:main',
            'aicane-calibrate=scripts.calibrate:main',
            'aicane-test-sensors=scripts.test_sensors:main',
        ],
    },
    python_requires='>=3.8',
)
