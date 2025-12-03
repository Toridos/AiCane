import heapq
def a_star(grid,start,goal):
    h,w=grid.shape
    pq=[(0,start)]; came={}; cost={start:0}
    def heur(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])
    while pq:
        _,cur=heapq.heappop(pq)
        if cur==goal:
            p=[]; c=cur
            while c in came: p.append(c); c=came[c]
            return p[::-1]
        for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            nx,ny=cur[0]+dx,cur[1]+dy
            if 0<=nx<h and 0<=ny<w and grid[nx,ny]==0:
                nc=cost[cur]+1
                if (nx,ny) not in cost or nc<cost[(nx,ny)]:
                    cost[(nx,ny)]=nc
                    heapq.heappush(pq,(nc+heur((nx,ny),goal),(nx,ny)))
                    came[(nx,ny)]=cur
    return []
