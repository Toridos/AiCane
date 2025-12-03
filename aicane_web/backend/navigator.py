import heapq
import numpy as np

def a_star(grid, start, goal):
    h, w = grid.shape
    pq = [(0, start)]
    came = {}
    cost = {start: 0}

    def heur(a,b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    while pq:
        _, cur = heapq.heappop(pq)
        if cur == goal:
            path = []
            while cur in came:
                path.append(cur)
                cur = came[cur]
            return path[::-1]

        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx, ny = cur[0]+dx, cur[1]+dy
            if 0 <= nx < h and 0 <= ny < w:
                if grid[nx,ny] == 0:
                    new_cost = cost[cur] + 1
                    if (nx,ny) not in cost or new_cost < cost[(nx,ny)]:
                        cost[(nx,ny)] = new_cost
                        pr = new_cost + heur((nx,ny), goal)
                        heapq.heappush(pq, (pr, (nx,ny)))
                        came[(nx,ny)] = cur

    return []
