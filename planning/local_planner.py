# Static route follower (optional) – kept for compatibility with old JSON routes
import json, math, time

class LocalPlanner:
    def __init__(self, json_path='tests/route_data.json', speed=0.30):
        self.speed = speed
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.path = data.get('path', [])
        except Exception:
            self.path = []

    def next_direction(self, start, end):
        dx = end['lng'] - start['lng']
        dy = end['lat'] - start['lat']
        if abs(dx) < 1e-6 and dy > 0: return 'N'
        if abs(dx) < 1e-6 and dy < 0: return 'S'
        if dx > 0 and abs(dy) < 1e-6: return 'E'
        if dx < 0 and abs(dy) < 1e-6: return 'W'
        if dx > 0 and dy > 0: return 'NE'
        if dx < 0 and dy > 0: return 'NW'
        if dx > 0 and dy < 0: return 'SE'
        if dx < 0 and dy < 0: return 'SW'
        return '?'

    # For compatibility, return simple (v, steer) for each segment
    def follow_once(self, idx):
        if idx >= len(self.path)-1:
            return 0.0, 0.0
        start = self.path[idx]; end = self.path[idx+1]
        d = self.next_direction(start, end)
        steer = 0.0
        if d in ('E','NE','SE'): steer = +20.0
        if d in ('W','NW','SW'): steer = -20.0
        v = self.speed
        if d in ('S','SE','SW'): v = -self.speed
        return v, steer
