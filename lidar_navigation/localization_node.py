"""
Localization via Dead Reckoning
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose2D, Twist
import math
from config import HardwareConfig


class LocalizationNode(Node):
    def __init__(self):
        super().__init__('localization')
        
        self.pose_pub = self.create_publisher(Pose2D, '/pose', 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        
        self.vx_actual = 0.0
        self.vy_actual = 0.0
        self.wz_actual = 0.0
        
        self.last_time = self.get_clock().now()
        self.create_timer(0.01, self.update_pose)
        
        self.get_logger().info("✅ Localization Started")

    def cmd_callback(self, msg):
        vx, vy, wz = msg.linear.x, msg.linear.y, msg.angular.z
        
        if abs(wz) > 0.05:
            self.vx_actual = 0.0
            self.vy_actual = 0.0
            self.wz_actual = HardwareConfig.ACTUAL_SPEED_ROTATE * (1 if wz > 0 else -1)
        elif abs(vy) > 0.05:
            self.vx_actual = 0.0
            self.vy_actual = HardwareConfig.ACTUAL_SPEED_LATERAL * (1 if vy > 0 else -1)
            self.wz_actual = 0.0
        elif abs(vx) > 0.05:
            self.vx_actual = HardwareConfig.ACTUAL_SPEED_FORWARD * (1 if vx > 0 else -1)
            self.vy_actual = 0.0
            self.wz_actual = 0.0
        else:
            self.vx_actual = self.vy_actual = self.wz_actual = 0.0

    def update_pose(self):
        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        self.last_time = now
        
        if dt > 0.5:
            return
        
        cos_theta = math.cos(self.theta)
        sin_theta = math.sin(self.theta)
        
        vx_world = self.vx_actual * cos_theta - self.vy_actual * sin_theta
        vy_world = self.vx_actual * sin_theta + self.vy_actual * cos_theta
        
        self.x += vx_world * dt
        self.y += vy_world * dt
        self.theta += self.wz_actual * dt
        
        while self.theta > math.pi: self.theta -= 2 * math.pi
        while self.theta < -math.pi: self.theta += 2 * math.pi
        
        msg = Pose2D()
        msg.x, msg.y, msg.theta = self.x, self.y, self.theta
        self.pose_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LocalizationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()


# ========================================
# 파일 5: lidar_navigation/controller_node.py
# ========================================
"""
Navigation Controller
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose2D, Twist, Point
from std_msgs.msg import Bool, Float32MultiArray
import math
from config import NavigationConfig


class ControllerNode(Node):
    def __init__(self):
        super().__init__('controller')
        
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.reached_pub = self.create_publisher(Bool, '/goal_reached', 10)
        
        self.create_subscription(Pose2D, '/pose', self.pose_callback, 10)
        self.create_subscription(Point, '/goal', self.goal_callback, 10)
        self.create_subscription(Float32MultiArray, '/ultra', self.ultra_callback, 10)
        
        self.pose = Pose2D()
        self.goal = None
        self.ultra = [999.0, 999.0, 999.0]
        
        self.create_timer(1.0 / NavigationConfig.CONTROL_HZ, self.control_loop)
        self.get_logger().info("✅ Controller Started")

    def pose_callback(self, msg):
        self.pose = msg

    def goal_callback(self, msg):
        self.goal = msg
        self.get_logger().info(f"🎯 New goal: ({msg.x:.2f}, {msg.y:.2f})")

    def ultra_callback(self, msg):
        if len(msg.data) >= 3:
            self.ultra = list(msg.data)

    def control_loop(self):
        if not self.goal:
            self._stop()
            return
        
        # 장애물 체크 (cm → m)
        if self.ultra[1] < NavigationConfig.OBSTACLE_THRESHOLD * 100:
            self.get_logger().warn(f"⛔ Obstacle! {self.ultra[1]:.1f}cm")
            self._stop()
            return
        
        # 거리 계산
        dx = self.goal.x - self.pose.x
        dy = self.goal.y - self.pose.y
        dist = math.sqrt(dx**2 + dy**2)
        
        # 도달 체크
        if dist < NavigationConfig.GOAL_THRESHOLD:
            self.get_logger().info("✅ Goal reached!")
            self._stop()
            self.reached_pub.publish(Bool(data=True))
            self.goal = None
            return
        
        # Pure Pursuit
        target_angle = math.atan2(dy, dx)
        angle_error = self._normalize_angle(target_angle - self.pose.theta)
        
        cmd = Twist()
        
        if abs(angle_error) > NavigationConfig.ANGLE_TOLERANCE:
            cmd.angular.z = NavigationConfig.KP_ANGULAR * angle_error
            cmd.angular.z = max(-1.0, min(1.0, cmd.angular.z))
        else:
            cmd.linear.x = 0.3
            cmd.angular.z = NavigationConfig.KP_ANGULAR * angle_error
        
        self.cmd_pub.publish(cmd)

    def _stop(self):
        self.cmd_pub.publish(Twist())

    @staticmethod
    def _normalize_angle(angle):
        while angle > math.pi: angle -= 2 * math.pi
        while angle < -math.pi: angle += 2 * math.pi
        return angle


def main(args=None):
    rclpy.init(args=args)
    node = ControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
