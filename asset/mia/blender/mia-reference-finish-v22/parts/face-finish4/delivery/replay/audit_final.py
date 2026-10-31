"""Read-only c02 to finish-3 preservation and evaluated join audit; never saves native."""
import bpy,ast,json,hashlib,sys,argparse,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));import review_setup as r
ap=argparse.ArgumentParser();ap.add_argument('--candidate',default=str(HERE/'finish-3/Mia_FaceFinish_v22.blend'));args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);FINAL=Path(args.candidate)
old=r.ROOT/'asset/mia/blender/mia-face-correction-v20/candidate-orbital-v21/main/exact-recipe.py'
ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse(old.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='snapshots'],type_ignores=[]),str(old),'exec'))
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1)
 for o in bpy.context.scene.objects:
  if o.type=='MESH' and o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks[1:]:k.value=0
 bpy.context.view_layer.update();snap=snapshots();keys={};base={};evs={};counts={}
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;basis=np.array([tuple(v.co) for v in m.shape_keys.key_blocks[0].data if True]) if m.shape_keys else np.array([tuple(v.co) for v in m.vertices]);base[o.name]=basis
  keys[o.name]={k.name:np.array([tuple(v.co) for v in k.data])-np.array([tuple(v.co) for v in k.relative_key.data]) for k in m.shape_keys.key_blocks} if m.shape_keys else {}
  assert np.isfinite(basis).all()
  for uv in m.uv_layers:assert np.isfinite([tuple(d.uv) for d in uv.data]).all()
  counts[o.name]={'vertices':len(m.vertices),'polygons':len(m.polygons),'keys':len(keys[o.name])}
  if o.name in ['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN']:
   ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();evs[o.name]={'coords':np.array([tuple(o.matrix_world@v.co) for v in me.vertices]),'faces':[list(p.vertices) for p in me.polygons]};ev.to_mesh_clear()
 body=bpy.data.objects['MIA_V06_BODY_SKIN'];body_world=np.array([tuple(body.matrix_world@Vector(v)) for v in base[body.name]])
 skin=evs['MIA_V14_SculptedSkin'];uses={}
 for p in skin['faces']:
  for a,b in zip(p,p[1:]+p[:1]):e=tuple(sorted((a,b)));uses[e]=uses.get(e,0)+1
 adj={}
 for (a,b),n in uses.items():
  if n==1:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 seen=set();outer=[]
 for start in adj:
  if start in seen:continue
  stack=[start];seen.add(start);ids=[]
  while stack:
   i=stack.pop();ids.append(i)
   for j in adj[i]:
    if j not in seen:seen.add(j);stack.append(j)
  pts=skin['coords'][ids]
  if pts[:,2].min()<1.48 and pts[:,2].max()>1.58:outer.extend(ids)
 bd=evs['MIA_V06_BODY_SKIN'];bvh=BVHTree.FromPolygons([Vector(v) for v in bd['coords']],bd['faces']);dist=np.array([bvh.find_nearest(Vector(skin['coords'][i]))[3] for i in outer]);join={'sample_count':len(dist),'max_m':float(dist.max()),'p95_m':float(np.percentile(dist,95)),'median_m':float(np.median(dist))}
 packed={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}
 return snap,keys,base,evs,body_world,join,packed,counts,all(i.use_fake_user for i in bpy.data.images if i.packed_file)
source_hash=r.sha(r.SOURCE);final_hash=r.sha(FINAL);a=read(r.SOURCE);b=read(FINAL)
changed=[n for n in a[0] if a[0][n]!=b[0][n]];allowed={'MIA_V14_SculptedSkin','MIA_V14_EyeSurface','MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1','MIA_V06_BODY_SKIN'}
assert set(changed)<=allowed;assert set(a[0])==set(b[0]);errors={}
for n in a[0]:
 for k in ['uv','topology','weights','matrix','modifiers']:assert a[0][n][k]==b[0][n][k],(n,k)
 assert set(a[1][n])==set(b[1][n]);errors[n]=max([float(np.abs(a[1][n][k]-b[1][n][k]).max()) for k in a[1][n]] or [0])
assert max(errors.values())<2e-7
body='MIA_V06_BODY_SKIN';mask=a[4][:,2]<1.46;base_diff=np.linalg.norm(b[2][body]-a[2][body],axis=1);assert not base_diff[mask].any()
aa=a[3][body]['coords'];bb=b[3][body]['coords'];assert aa.shape==bb.shape;mask_ev=aa[:,2]<1.46;evdiff=np.linalg.norm(bb-aa,axis=1)
for n,h in a[6].items():assert b[6][n]==h,n
assert b[8];assert source_hash==r.sha(r.SOURCE);assert final_hash==r.sha(FINAL)
out={'source':r.artifact(r.SOURCE),'candidate':r.artifact(FINAL),'changed_mesh_owners':changed,'all_other_mesh_snapshots_exact':True,'all_uv_topology_weights_matrices_modifiers_exact':True,'relative_key_max_error_m':max(errors.values()),'relative_key_errors':{k:v for k,v in errors.items() if k in allowed},'source_packed_count':len(a[6]),'candidate_packed_count':len(b[6]),'source_packed_exact':True,'all_candidate_packed_fake_user':b[8],'source_packed_hashes':a[6],'body_basis_below1p46_count':int(mask.sum()),'body_basis_below1p46_max_delta_m':float(base_diff[mask].max()),'body_evaluated_below1p46_max_delta_m':float(evdiff[mask_ev].max()),'body_evaluated_below1p46_changed_count_gt1um':int((evdiff[mask_ev]>1e-6).sum()),'body_evaluated_below1p46_nonzero_z_range':[float(aa[mask_ev & (evdiff>1e-9),2].min()),float(aa[mask_ev & (evdiff>1e-9),2].max())] if (mask_ev & (evdiff>1e-9)).any() else None,'evaluated_face_cap_join_before':a[5],'evaluated_face_cap_join_after':b[5],'counts':{k:b[7][k] for k in allowed},'finite_coordinates_uv':True,'read_only_native_hashes_preserved':True,'limitations':['Relative key preservation is not expression validation. Close0.5 visually closes almost fully and lash ribbon is thick; inherited rig remains unfinished.','Evaluated join nearest distances measure positional contact only, not tangent/shading smoothness.']}
(FINAL.parent/'preservation-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ['source_packed_hashes','relative_key_errors','counts']},indent=2))
