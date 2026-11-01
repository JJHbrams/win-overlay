"""Correct lower-arc traversal: connected lower path, never mixed upper samples."""
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'author_uv_maps.py').read_text().replace("'look-a/maps'","'look-c/maps'")
start=code.index(" q=bp[(bp[:,0]*sign>")
end=code.index(" assert len(xs)>20",start)
code=code[:start]+''' from collections import defaultdict
 adjacency=defaultdict(set)
 for (a,b),count in ec.items():
  if count==1:adjacency[a].add(b);adjacency[b].add(a)
 eligible=[i for i in boundary if P[i,0]*sign>.013 and P[i,0]*sign<.059 and P[i,1]>.035 and 1.527<P[i,2]<1.557]
 inner=min(eligible,key=lambda i:abs(P[i,0]));outer=max(eligible,key=lambda i:abs(P[i,0]));paths=[]
 for neighbor in adjacency[inner]:
  path=[inner,neighbor]
  while path[-1]!=outer:
   nexts=adjacency[path[-1]]-{path[-2]};assert len(nexts)==1
   nxt=next(iter(nexts));assert nxt not in path;path.append(nxt)
  paths.append(path)
 lower=min(paths,key=lambda path:np.mean(P[path,2]));q=P[lower];order=np.argsort(abs(q[:,0]));q=q[order]
 xs=abs(q[:,0]).tolist();zs=q[:,2].tolist()
''' +code[end:]
code=code.replace("base[:,:,:3]=np.clip(base[:,:,:3],0,1.2)","""base[:,:,:3]=np.clip(base[:,:,:3],0,1.2)
filled=valid.copy()
for step in range(16):
 previous=filled.copy()
 for axis,shift in [(0,1),(0,-1),(1,1),(1,-1)]:
  take=(~filled)&np.roll(previous,shift,axis)
  if axis==0:take[0 if shift==1 else -1,:]=False
  else:take[:,0 if shift==1 else -1]=False
  for channel in [base,fat,ink,region]:channel[take]=np.roll(channel,shift,axis)[take]
  filled[take]=True
""")
(ROOT/'author_uv_maps_c_expanded.py').write_text(code);exec(compile(code,str(ROOT/'author_uv_maps_c_expanded.py'),'exec'))
