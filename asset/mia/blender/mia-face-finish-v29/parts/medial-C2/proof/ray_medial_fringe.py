import bpy,numpy as np,json
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;bpy.ops.wm.open_mainfile(filepath=str(O/'Mia_EyeLash_v29_A.blend'));master=bpy.data.objects['MIA_V27_Foundation_Face']
for k in master.data.shape_keys.key_blocks:k.value=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();owners=[bpy.data.objects[n] for n in ['MIA_V27_SharedHeadBody','V28G_InnerLid_1','V28G_Sclera_1','V28G_Iris_1']];bvs={}
for ob in owners:
 ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();p=np.array([ev.matrix_world@v.co for v in me.vertices]);tri=[list(t.vertices) for t in me.loop_triangles];uv=[np.array([me.uv_layers[0].data[j].uv[:] for j in t.loops]) for t in me.loop_triangles] if me.uv_layers else None;bvs[ob.name]=(BVHTree.FromPolygons([Vector(q) for q in p],tri,all_triangles=True),p,np.array(tri),uv);ev.to_mesh_clear()
rec=json.loads((O/'medial-review/macros/records.json').read_text());mat=Matrix(next(r for r in rec if r['id']=='A-front-clean')['camera_matrix']);pos=mat.translation;rot=mat.to_3x3();direction=-(rot@Vector((0,0,1)));rows=[]
for x,y in [(419,458),(423,462),(430,462),(425,463),(463,472),(422,456),(432,459)]:
 origin=pos+rot@Vector((((x+.5)/768-.5)*.045,(.5-(y+.5)/768)*.045,0));hits=[]
 for name,(bv,p,tri,uv) in bvs.items():
  h,n,idx,dist=bv.ray_cast(origin,direction)
  if h is None:continue
  d={'owner':name,'distance_m':dist,'world_mm':list(h*1000),'normal':list(n),'triangle':int(idx)}
  if uv is not None:
   a,b,c=p[tri[idx]];e=np.stack([b-a,c-a],axis=1);v=np.linalg.lstsq(e,np.array(h)-a,rcond=None)[0];bc=np.array([1-v.sum(),*v]);u=bc@uv[idx];d['uv']=u.tolist()
   if 'Iris' in name:d['iris_radial_alpha_inside']=bool(((u[0]*2%1-.5)/.29352959990501404)**2+((u[1]-.5)/.22200000286102295)**2<1)
  hits.append(d)
 hits.sort(key=lambda d:d['distance_m']);rows.append({'pixel':[x,y],'hits_nearest_first':hits})
(O/'medial-A-fringe-rays.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
