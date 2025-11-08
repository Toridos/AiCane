import math, numpy as np

def mission_to_polyline(mission, step=0.05):
    x=y=yaw=0.0
    pts=[(x,y)]
    for seg in mission:
        t = seg['type'].upper()
        if t=='STRAIGHT':
            D = float(seg['dist_m']); n=max(1,int(D/step))
            dx=math.cos(yaw)*D/n; dy=math.sin(yaw)*D/n
            for _ in range(n): x+=dx; y+=dy; pts.append((x,y))
        elif t=='TURN':
            yaw += math.radians(float(seg['angle_deg']))
            pts.append((x,y))
    return pts

def nearest_point_on_polyline(pt, line):
    x0,y0 = pt
    arr = np.array(line)
    d2 = (arr[:,0]-x0)**2 + (arr[:,1]-y0)**2
    idx = int(np.argmin(d2))
    return line[idx], idx
