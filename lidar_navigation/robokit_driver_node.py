"""
Robokit Hardware Driver
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray
import time

# ⭐ 단순하게 import
from RobokitRS import RobokitRS
from config import HardwareConfig, NavigationConfig


class RobokitDriverNode(Node):
    def __init__(self):
        super().__init__('robokit_driver')
        
        # 하드웨어 초기화
        self.robot = RobokitRS()
        self._init_hardware()
        
        # ROS 통신
        self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.ultra_pub = self.create_publisher(Float32MultiArray, '/ultra', 10)
        
        self.last_cmd_time = time.time()
        
        # 타이머
        self.create_timer(1.0 / NavigationConfig.SENSOR_HZ, self.read_sensors)
        self.create_timer(0.1, self.safety_check)
        
        self.get_logger().info("✅ Robokit Driver Started")

    def _init_hardware(self):
        try:
            self.robot.port_open(HardwareConfig.ROBOKIT_PORT)
            self.get_logger().info(f"🔌 Connected: {HardwareConfig.ROBOKIT_PORT}")
            
            self.robot.sonar_begin(HardwareConfig.ULTRASONIC_FRONT)
            self.robot.sonar_begin(HardwareConfig.ULTRASONIC_LEFT)
            self.robot.sonar_begin(HardwareConfig.ULTRASONIC_RIGHT)
            
        except Exception as e:
            self.get_logger().error(f"❌ Hardware init failed: {e}")
            raise

    def cmd_callback(self, msg):
        self.last_cmd_time = time.time()
        
        vx, vy, wz = msg.linear.x, msg.linear.y, msg.angular.z
        
        try:
            if abs(wz) > 0.05:
                if wz > 0:
                    self.robot.set_mecanumwheels_rotate_left(HardwareConfig.ROTATE_SPEED)
                else:
                    self.robot.set_mecanumwheels_rotate_right(HardwareConfig.ROTATE_SPEED)
            elif abs(vy) > 0.05:
                if vy > 0:
                    self.robot.set_mecanumwheels_drive_right(HardwareConfig.BASE_SPEED)
                else:
                    self.robot.set_mecanumwheels_drive_left(HardwareConfig.BASE_SPEED)
            elif abs(vx) > 0.05:
                if vx > 0:
                    self.robot.set_mecanumwheels_drive_front(HardwareConfig.BASE_SPEED)
                else:
                    self.robot.set_mecanumwheels_drive_back(HardwareConfig.BASE_SPEED)
            else:
                self.robot.set_mecanumwheels_drive_stop()
        except Exception as e:
            self.get_logger().error(f"Motor error: {e}")
            self.robot.set_mecanumwheels_drive_stop()

    def read_sensors(self):
        try:
            sensors = []
            for pin in [HardwareConfig.ULTRASONIC_LEFT, 
                       HardwareConfig.ULTRASONIC_FRONT,
                       HardwareConfig.ULTRASONIC_RIGHT]:
                val = self.robot.sonar_read(pin)
                sensors.append(float(val) if val and val > 0 else 999.0)
            
            msg = Float32MultiArray()
            msg.data = sensors
            self.ultra_pub.publish(msg)
            
        except Exception as e:
            self.get_logger().warn(f"Sensor error: {e}")

    def safety_check(self):
        if time.time() - self.last_cmd_time > 0.5:
            try:
                self.robot.set_mecanumwheels_drive_stop()
            except:
                pass

    def cleanup(self):
        try:
            self.robot.set_mecanumwheels_drive_stop()
        except:
            pass


def main(args=None):
    rclpy.init(args=args)
    node = RobokitDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

