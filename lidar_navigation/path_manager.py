"""
Path Manager
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from std_msgs.msg import Bool
import json
import os
from config import PathConfig


class PathManager(Node):
    def __init__(self):
        super().__init__('path_manager')
        
        self.goal_pub = self.create_publisher(Point, '/goal', 10)
        self.create_subscription(Bool, '/goal_reached', self.goal_reached_callback, 10)
        
        self.path = self._load_path()
        self.idx = 0
        
        self.create_timer(1.0, self._publish_initial, one_shot=True)
        self.get_logger().info(f"✅ Path Manager: {len(self.path)} waypoints")

    def _load_path(self):
        if os.path.exists(PathConfig.PATH_FILE):
            try:
                with open(PathConfig.PATH_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return PathConfig.DEFAULT_PATH

    def _publish_initial(self):
        self._publish_current()

    def _publish_current(self):
        if self.idx >= len(self.path):
            self.get_logger().info("🏁 All waypoints done!")
            return
        
        wp = self.path[self.idx]
        msg = Point()
        msg.x, msg.y = float(wp['x']), float(wp['y'])
        self.goal_pub.publish(msg)
        self.get_logger().info(f"🎯 Goal #{self.idx+1}: ({msg.x:.2f}, {msg.y:.2f})")

    def goal_reached_callback(self, msg):
        if msg.data:
            self.idx += 1
            self.create_timer(0.5, self._publish_current, one_shot=True)


def main(args=None):
    rclpy.init(args=args)
    node = PathManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()