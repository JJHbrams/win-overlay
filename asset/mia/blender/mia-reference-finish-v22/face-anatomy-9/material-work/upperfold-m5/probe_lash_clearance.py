import json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;V22=ROOT.parents[2]
sys.path.insert(0,str(ROOT));from apply_upperfold_m5 import measured_lid_uv
bpy.ops.wm.open_mainfile(filepath=str(V22/'integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend'),use_scripts=False)
skin=bpy.data.objects['MIA_V14_SculptedSkin'];m=skin.data;uv=m.uv_layers['UVMap'];P=np.array([v.co[:] for v in m.shape_keys.key_blocks[0].data])
tris=[];ids=[]
for f in m.polygons:
 if f.material_index!=7:continue
 lis=list(f.loop_indices)
 for a,b,c in [(lis[0],lis[j],lis[j+1]) for j in range(1,len(lis)-1)]:
  tris.append([uv.data[i].uv[:] for i in (a,b,c)]);ids.append([m.loops[i].vertex_index for i in (a,b,c)])
T=np.array(tris);I=np.array(ids);A=T[:,1]-T[:,0];B=T[:,2]-T[:,0];den=A[:,0]*B[:,1]-A[:,1]*B[:,0]
def pos(q):
 Q=np.array(q)-T[:,0];a=(Q[:,0]*B[:,1]-Q[:,1]*B[:,0])/np.where(abs(den)>1e-12,den,1e10);b=(A[:,0]*Q[:,1]-A[:,1]*Q[:,0])/np.where(abs(den)>1e-12,den,1e10)
 valid=np.where((a>=-1e-6)&(b>=-1e-6)&(a+b<=1+1e-6)&(abs(den)>1e-12))[0]
 if len(valid)==0:return None
 i=valid[0];return P[I[i,0]]*(1-a[i]-b[i])+P[I[i,1]]*a[i]+P[I[i,2]]*b[i]
row=next(r for r in measured_lid_uv(skin) if r['side']==1);samples=np.array(row['upper'])
o=bpy.data.objects['MIA_V14_UpperLash_1'];mat=skin.matrix_world.inverted()@o.matrix_world;L=np.array([(mat@Vector(v.co)).to_tuple() for v in o.data.shape_keys.key_blocks[0].data])
result=[]
for t in [.25,.5,.75]:
 u=row['inner_uv'][0]+t*(row['outer_uv'][0]-row['inner_uv'][0]);v=np.interp(u,samples[:,0],samples[:,1]);p=pos([u,v+.0005]);same=L[np.abs(L[:,0]-p[0])<.0015];zz=float(same[:,2].max())
 entry={'t':t,'uv':[u,v],'rim_probe':p.tolist(),'lash_upper_z':zz,'probes':[]}
 for off in [.013-.004*t,.020,.026,.032]:
  pt=pos([u,v+off]);entry['probes'].append({'offset_uv':off,'p':pt.tolist() if pt is not None else None,'above_lash_mm':float((pt[2]-zz)*1000) if pt is not None else None})
 result.append(entry)
(ROOT/'lash-clearance-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
