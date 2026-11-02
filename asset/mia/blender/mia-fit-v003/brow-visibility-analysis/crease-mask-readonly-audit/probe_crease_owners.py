"""Read-only ephemeral CPU ray/UV audit. No apply, render, or native save."""
from pathlib import Path
import bpy, json, hashlib, numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
P=Path(__file__).resolve().parent
C=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender')
E=C/'mia-fit-v003/eyes'
N=C/'mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend'
native_sha=hashlib.sha256(N.read_bytes()).hexdigest()
assert native_sha=='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'
cfg=json.loads((E/'upper-crease-vector.json').read_text(encoding='utf-8'))
rec=json.loads((E/'crease-B/render-records.json').read_text(encoding='utf-8'))[0]
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False)
for name in rec['hair_temporarily_hidden']:bpy.data.objects[name].hide_render=True
cam=Matrix(rec['camera']['matrix']);incoming=cam.to_3x3().col[2].normalized();forward=-incoming
bpy.context.scene.frame_set(rec['camera']['frame']);bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get()
trees=[];skin_uv=None;skin_q=None;skin_tri=None;skin_tree=None
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ev=ob.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);me.calc_loop_triangles()
 if not me.loop_triangles:ev.to_mesh_clear();continue
 q=[ev.matrix_world@v.co for v in me.vertices];tri=[list(t.vertices) for t in me.loop_triangles]
 tree=BVHTree.FromPolygons(q,tri,all_triangles=True)
 uv=me.uv_layers.get('UVMap')
 uvs=[[(float(uv.data[i].uv.x),float(uv.data[i].uv.y)) for i in t.loops] for t in me.loop_triangles] if uv else None
 trees.append((ob.name,tree,q,tri,uvs))
 if ob.name=='MIA_V27_SharedHeadBody':skin_uv=uvs;skin_q=q;skin_tri=tri;skin_tree=tree
 ev.to_mesh_clear()
def coverage(uv,row):
 best=0.
 for a,b in zip(row['points'][:-1],row['points'][1:]):
  start=np.array(a['uv']);d=np.array(b['uv'])-start
  t=np.clip(np.dot(np.array(uv)-start,d)/np.dot(d,d),0,1)
  dist=np.linalg.norm(np.array(uv)-start-t*d)
  taper=.6+.4*np.sin(np.pi*((a['t']+b['t'])/2-.10)/.83)
  w=(a['half_width_uv']+b['half_width_uv'])*.5*taper
  best=max(best,max(0.,1.-dist/w))
 return best*.65
def first(origin):
 hits=[]
 for name,tree,q,tri,uvs in trees:
  p,n,f,dist=tree.ray_cast(origin,forward,2.)
  if p is not None:hits.append((float(dist),name,list(p),int(f)))
 return sorted(hits)[:5]
rows=[]
for row in cfg['creases']:
 samples=[]
 for j,(a,b) in enumerate(zip(row['points'][:-1],row['points'][1:])):
  for t in [.0,.25,.5,.75]:
   point=Vector(np.array(a['world'])*(1-t)+np.array(b['world'])*t)
   hits=first(point+incoming*.5)
   p,n,f,dist=skin_tree.ray_cast(point+incoming*.5,forward,2.)
   u=v=None;alpha=0.
   if p is not None:
    vert=[skin_q[i] for i in skin_tri[f]];ut=[Vector((*i,0)) for i in skin_uv[f]]
    value=barycentric_transform(p,*vert,*ut);u,v=value[:2];alpha=coverage([u,v],row)
   samples.append(dict(segment=j,t=t,world=list(point),first_hits=hits,actual_skin_uv=[u,v],CPU_mask_at_skin=alpha))
 rows.append(dict(side=row['side'],samples=samples))
summary=[]
from collections import Counter
for row in rows:
 c=Counter(s['first_hits'][0][1] for s in row['samples'] if s['first_hits'])
 summary.append(dict(side=row['side'],first_hit_owner_counts=dict(c),mask_at_skin_max=max(s['CPU_mask_at_skin'] for s in row['samples']),mask_at_skin_positive=sum(s['CPU_mask_at_skin']>.01 for s in row['samples'])))
skin=bpy.data.objects['MIA_V27_SharedHeadBody'];nd=skin.material_slots[0].material.node_tree.nodes
lash_graphs=[]
def val(v):
 if v is None:return None
 try:return list(v)
 except TypeError:return v
for name in ['V30_UpperLashes_-1','V30_UpperLashes_1']:
 ob=bpy.data.objects[name]
 for mat in ob.data.materials:
  if not mat or not mat.use_nodes:continue
  out=mat.node_tree.get_output_node('EEVEE');seen=set();stack=[out]
  while stack:
   node=stack.pop()
   if node.name in seen:continue
   seen.add(node.name)
   for inp in node.inputs:stack += [l.from_node for l in inp.links]
  lash_graphs.append(dict(owner=name,material=mat.name,alpha_method=mat.surface_render_method,nodes=[dict(name=n.name,type=n.bl_idname,operation=getattr(n,'operation',None),uv_map=getattr(n,'uv_map',None),inputs=[dict(name=i.name,value=val(getattr(i,'default_value',None)),links=[(l.from_node.name,l.from_socket.name) for l in i.links]) for i in n.inputs],outputs=[dict(name=o.name,value=val(getattr(o,'default_value',None))) for o in n.outputs]) for n in mat.node_tree.nodes if n.name in seen]))
report=dict(native=str(N),native_sha256=native_sha,actual_camera=rec['camera'],summary=summary,rows=rows,lash_graphs=lash_graphs,neutral_gates={k:nd[k].outputs[0].default_value for k in ['V30_FaceRootFade','V30_FoldOpen_L','V30_FoldOpen_R']},setup='Native unchanged. Hair hide flags from actual crease-B record. Same actual front camera. Evaluated viewport mesh CPU rays, not render-DG opacity proof.',native_saved=False,render_called=False,GPU_used=False)
(P/'crease-owner-rays.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x))+'\n',encoding='utf-8')
assert hashlib.sha256(N.read_bytes()).hexdigest()==native_sha
print('CREASE_OWNER_RAYS_DONE',json.dumps(summary,default=lambda x:x.item()),flush=True)
