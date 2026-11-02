"""Register vector crease to actual upper lid and evaluated surface UV."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parent;C=P.parents[1];V=C/'mia-refinement-v002'
N=V/'integrated/Mia_v0.0.2_Review_R3b.blend';SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
o=bpy.data.objects['MIA_V27_SharedHeadBody'];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles()
q=[e.matrix_world@v.co for v in m.vertices];tri=[list(t.vertices) for t in m.loop_triangles];uvtri=[[Vector((*m.uv_layers['UVMap'].data[i].uv,0.)) for i in t.loops] for t in m.loop_triangles];tree=BVHTree.FromPolygons(q,tri,all_triangles=True)
rim=json.loads((C/'mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text());rows=[]
def project(p):
 hit,n,face,dist=tree.ray_cast(Vector((float(p[0]),-.2,float(p[2]))),Vector((0,1,0)),.4)
 assert hit is not None,'Upper skin projection missed'
 a,b,c=[q[i] for i in tri[face]];u,v,w=uvtri[face];uv=barycentric_transform(hit,a,b,c,u,v,w)
 return np.array(uv[:2]),list(hit),int(face)
for side in [-1,1]:
 curve=np.array([q[i][:] for i in rim['evaluated_openings'][str(side)]['upper_evaluated_indices']]);axis=curve[-1]-curve[0];axis/=np.linalg.norm(axis);up=np.array([0.,0.,1.])-axis*axis[2];up/=np.linalg.norm(up);points=[]
 for t in np.linspace(.10,.93,10):
  v=t*(len(curve)-1);i=min(int(v),len(curve)-2);p=curve[i]*(1-(v-i))+curve[i+1]*(v-i)
  gap=.0013+.0005*np.sin(np.pi*t);target=p+up*gap
  uv,hit,face=project(target);uv2,_,_=project(target+up*.00017)
  width=float(np.linalg.norm(uv2-uv));points.append(dict(t=float(t),uv=uv.tolist(),half_width_uv=width,world=hit,skin_triangle=face,gap_from_rim_mm=float(gap*1000)))
 rows.append(dict(side=side,screen='right' if side==1 else 'left',points=points))
uv=o.data.uv_layers['UVMap'];raw=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',raw)
mhash=hashlib.sha256(raw.tobytes()).hexdigest();e.to_mesh_clear()
report=dict(baseline_sha256=SHA,UV='UVMap',original_face_UV_sha256=mhash,creases=rows,method='Actual evaluated upper-rim curve with1.3..1.8mm local superior offset, projected to current skin; vector UV registration and0.17mm half-width. Original UV is not remapped. Same surface UV follows morphing.',native_saved=False)
(P/'upper-crease-vector.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('UPPER_CREASE_UV_REGISTERED',[(r['side'],r['points'][0]['uv'],r['points'][-1]['uv']) for r in rows],flush=True)
