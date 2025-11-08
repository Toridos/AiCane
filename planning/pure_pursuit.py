import math

def target_point(line, idx_near, lookahead=0.5):
    d_acc=0.0
    for i in range(idx_near, len(line)-1):
        x1,y1=line[i]; x2,y2=line[i+1]
        seg=math.hypot(x2-x1, y2-y1)
        d_acc += seg
        if d_acc >= lookahead: return (x2,y2), i+1
    return line[-1], len(line)-1

def control_cmd(pose, target, base_speed=0.30, kp_steer=2.0, steer_limit_deg=30):
    x,y,yaw = pose
    tx,ty = target
    dx = tx - x; dy = ty - y
    ang = math.atan2(dy, dx)
    e_yaw = (ang - yaw + math.pi)%(2*math.pi) - math.pi
    steer_deg = max(-steer_limit_deg, min(steer_limit_deg, math.degrees(kp_steer*e_yaw)))
    v = base_speed * max(0.5, 1.0 - abs(steer_deg)/steer_limit_deg)
    return v, steer_deg
