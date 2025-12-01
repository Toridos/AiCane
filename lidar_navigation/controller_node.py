"""
Navigation Controller
Pure Pursuit + Wall Following
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose2D, Twist, Point
from std_msgs.msg import Bool, Float32MultiArray
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
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
        
        # 장애물 체크
        if self.ultra[1] < NavigationConfig.OBSTACLE_THRESHOLD * 100:  # cm → m
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
            # 회전
            cmd.angular.z = NavigationConfig.KP_ANGULAR * angle_error
            cmd.angular.z = max(-1.0, min(1.0, cmd.angular.z))
        else:
            # 전진
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
