import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent/'sculpt2'
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
objects=sorted([o for o in bpy.data.objects if o.name.startswith('MIA_V24_Gather_')],key=lambda o:o.name)
projection=json.loads((P/'paint-projection.json').read_text())['views']
verts=[];faces=[]
for o in objects:
 base=len(verts);verts.extend([v.co.copy() for v in o.data.vertices]);faces.extend([tuple(base+i for i in p.vertices) for p in o.data.polygons])
tree=BVHTree.FromPolygons(verts,faces)
allrows=[]
for o in objects:
 m=o.data;m.calc_loop_triangles();uv=m.uv_layers['MIA_V20_LongitudinalUV'];co=np.array([v.co[:] for v in m.vertices]);norm=np.array([v.normal[:] for v in m.vertices]);projected={};visibility={}
 for view,entry in projection.items():
  mat=Matrix(entry['matrix_world']).inverted();direction=Vector((0,1,0)) if view=='back' else Vector((1,0,0));vis=[]
  for v in m.vertices:
   point=v.co+direction*.00015;hit,no,index,d=tree.ray_cast(point,direction,3)
   vis.append(1.0 if hit is None else 0.0)
  pc=np.array([mat@v.co for v in m.vertices]);projected[view]=.5+pc[:,:2]/entry['ortho_scale'];visibility[view]=np.array(vis)*np.clip(norm[:,1 if view=='back' else 0],0,1)**2
 tris=np.array([t.vertices[:] for t in m.loop_triangles]);uvtri=np.array([[uv.data[li].uv[:] for li in t.loops] for t in m.loop_triangles]);uvtri=(uvtri+np.array([.006,0]))/np.array([1.012,1])*.94+.03
 np.savez_compressed(P/(o.name+'.npz'),positions=co,triangles=tris,uv=uvtri,back_uv=projected['back'],profile_uv=projected['profile'],back_weight=visibility['back'],profile_weight=visibility['profile'])
 allrows.append({'owner':o.name,'npz':str(P/(o.name+'.npz'))})
(P/'paint-meshes.json').write_text(json.dumps(allrows,indent=2));print('EXPORTED',len(allrows))
