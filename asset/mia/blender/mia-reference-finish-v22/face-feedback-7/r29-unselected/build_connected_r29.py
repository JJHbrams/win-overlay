"""One bounded connected medial final-position relaxation from R28.

Reuses existing positive-cotangent positional fairness, now restricted to
medial nasal/buccal supports with restored OUTER form fixed. Per-side area-
weighted anterior moment is retained as a diagnostic guard, not art proof.
"""
from pathlib import Path
base=Path(__file__).resolve().parent.parent/'candidate-r28/expanded-recipe.py';source=base.read_text()
source=source.replace("SOURCE = R25 / 'refinement-r27/Mia_FaceFinish7_OrbitalTransitionR27_v22.blend'","SOURCE = H / 'candidate-r28/Mia_FaceFinish7_MedialTransitionR28_v22.blend'")
source=source.replace("Mia_FaceFinish7_MedialTransitionR28_v22.blend'\nassert not native", "Mia_FaceFinish7_ConnectedMedialR29_v22.blend'\nassert not native")
local='''
edge_pre=Counter(tuple(sorted((int(f[i]),int(f[(i+1)%3])))) for f in faces for i in range(3))
fixed_boundary={i for edge,n in edge_pre.items() if n==1 for i in edge}
outer_fixed={249,236,233,234,242,247,248,250,251,56,44,45,46,51,54,55,57,58}
region=sorted(i for i,(x,y,z) in enumerate(P) if i<588 and .005<abs(x)<.037 and y>.04 and 1.502<z<1.542 and i not in fixed_boundary and i not in outer_fixed and not(abs(x)<.014 and z<1.510))
index={i:k for k,i in enumerate(region)};adj=[set() for _ in P];cot={};area=np.zeros(len(P))
for f in faces:
 ar=np.linalg.norm(np.cross(P[f[1]]-P[f[0]],P[f[2]]-P[f[0]]))/6
 for i in f:area[i]+=ar
 for a,b,c in [tuple(f),tuple(np.roll(f,1)),tuple(np.roll(f,2))]:
  va=P[a]-P[c];vb=P[b]-P[c];w=float(np.dot(va,vb)/max(np.linalg.norm(np.cross(va,vb)),1e-12));edge=tuple(sorted((int(a),int(b))));cot[edge]=cot.get(edge,0.)+.5*w;adj[a].add(b);adj[b].add(a)
cot={e:max(w,.025) for e,w in cot.items()};n=len(region);L=np.zeros((n,n));rhs=np.zeros((n,3));data_weights=np.ones(n)
for row,i in enumerate(region):
 ww={j:cot[tuple(sorted((i,j)))] for j in adj[i]};total=sum(ww.values());L[row,row]=1.
 for j,w in ww.items():
  if j in index:L[row,index[j]]-=w/total
  else:rhs[row]+=w/total*P[j]
 x,y,z=P[i]
 if abs(x)<.011:data_weights[row]=4.
 if z<1.512:data_weights[row]=max(data_weights[row],3.)
 if z>1.538:data_weights[row]=max(data_weights[row],2.)
fairness=7.;A=np.diag(data_weights)+fairness*L.T@L;B=data_weights[:,None]*P[region]+fairness*L.T@rhs;solved=np.linalg.solve(A,B)
C=np.zeros((2,n))
for row,sign in enumerate([-1,1]):
 ids=[k for k,i in enumerate(region) if P[i,0]*sign>0];C[row,ids]=area[np.array(region)[ids]];C[row]/=C[row].sum()
response=np.linalg.solve(A,C.T);solved[:,1]+=response@np.linalg.solve(C@response,C@(P[region,1]-solved[:,1]))
delta[region]=solved-P[region];assert np.max(abs(C@delta[region,1]))<1e-12
regions={'connected_medial_support_final_delta_mm':{i:(1000*delta[i]).tolist() for i in region}};mapping={};semantic={i:'connected_medial_nasal_buccal_support' for i in region}
assert np.max(abs(delta[list(outer_fixed)]))==0
print('R29_LOCAL_FINAL_POSITIONS',len(region),float(np.linalg.norm(delta,axis=1).max()),'anterior_moment',list(C@delta[region,1]),flush=True)
'''
start=source.index('regions = ');end=source.index('edge_counts = Counter(',start);source=source[:start]+local+'\n'+source[end:]
source=source.replace('vertex-deltas-from-r27.json','vertex-deltas-from-r28.json').replace('One manual connected medial-cheek support iteration from R27; no fitting or smoothing operation.','One connected medial final-position relaxation from R28 using existing positive-cotangent method; no global face fairness or new framework.').replace('R27 outer apex positions are exact. Compressed medial rows redistributed by maximum2.6mm; full-face/continuity acceptance is not guaranteed.','Outer restored apex fixed; per-side anterior moment retained as a diagnostic only. Actual angles/sections decide volume and source character, not this numeric guard.')
source=source.replace("'changed_vertices': len(rows)","'changed_vertices': len(rows), 'changed_vertex_ids': region, 'fairness': fairness, 'area_weighted_anterior_delta': list(C@delta[region,1])")
expanded=Path(__file__).with_name('expanded-recipe.py');expanded.write_text(source);exec(compile(source,str(expanded),'exec'))
