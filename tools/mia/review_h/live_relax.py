"""Small NumPy mesh-adjacency helper used only inside live MCP operations."""
import heapq
import numpy as np


def mask(world,faces,eligible,fade=.012):
    edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
    lengths=np.linalg.norm(world[edges[:,0]].astype(float)-world[edges[:,1]],axis=1)
    boundary=edges[eligible[edges].any(1)&~eligible[edges].all(1)]
    starts=np.unique(boundary[eligible[boundary]])
    graph=[[] for _ in range(len(world))]
    for (a,b),length in zip(edges[eligible[edges].all(1)],lengths[eligible[edges].all(1)]):
        graph[a].append((int(b),float(length)));graph[b].append((int(a),float(length)))
    distance=np.full(len(world),np.inf);distance[starts]=0.
    queue=[(0.,int(i)) for i in starts];heapq.heapify(queue)
    while queue:
        d,a=heapq.heappop(queue)
        if d!=distance[a] or d>=fade:continue
        for b,length in graph[a]:
            value=d+length
            if value<distance[b]:distance[b]=value;heapq.heappush(queue,(value,b))
    t=np.minimum(distance/fade,1.);weight=np.zeros(len(world))
    weight[eligible]=(t*t*t*(10-15*t+6*t*t))[eligible]
    return weight,edges


def relax(world,edges,weight,iterations):
    e=edges[(weight[edges]>0).any(1)]
    lengths=np.linalg.norm(world[e[:,0]].astype(float)-world[e[:,1]],axis=1)
    influence=np.tile(1./np.maximum(lengths,.00025)**2,2)
    a=np.r_[e[:,0],e[:,1]];b=np.r_[e[:,1],e[:,0]]
    denominator=np.bincount(a,weights=influence,minlength=len(world))
    q=world.astype(float)
    for _ in range(iterations):
        average=np.column_stack([np.bincount(a,weights=influence*q[b,k],minlength=len(q)) for k in range(3)])
        delta=np.divide(average,denominator[:,None],out=q.copy(),where=denominator[:,None]>0)-q
        q+=.5*weight[:,None]*delta
    return q.astype(np.float32)
