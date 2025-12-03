def bfs_multifloor_fast(used_floors, GRIDS, CLEANED, start_room, goal_room):
    from collections import deque

    # Start coords
    for f in used_floors:
        if str(start_room) in CLEANED[f]:
            sx, sy = CLEANED[f][str(start_room)]
            start_f = f

    for f in used_floors:
        if str(goal_room) in CLEANED[f]:
            gx, gy = CLEANED[f][str(goal_room)]
            goal_f = f

    start = (start_f, int(sx), int(sy))
    goal  = (goal_f, int(gx), int(gy))

    Q = deque([start])
    visited = {start}
    parent = {}

    while Q:
        f,x,y = Q.popleft()
        if (f,x,y) == goal:
            # reconstruct
            path = []
            cur = goal
            while cur in parent:
                path.append(cur)
                cur = parent[cur]
            path.append(start)
            path.reverse()
            return [{"floor":a, "x":b, "y":c} for (a,b,c) in path]

        H,W = GRIDS[f].shape
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny=x+dx,y+dy
            if 0<=nx<W and 0<=ny<H:
                if GRIDS[f][ny,nx]==0:
                    nxt=(f,nx,ny)
                    if nxt not in visited:
                        visited.add(nxt)
                        parent[nxt]=(f,x,y)
                        Q.append(nxt)

    return None
