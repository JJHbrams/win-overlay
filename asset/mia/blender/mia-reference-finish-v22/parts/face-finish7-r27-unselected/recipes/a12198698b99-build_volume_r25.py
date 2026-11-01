"""Direct semantic malar/anterior-buccal volume restoration on R23.

No fit, fairness, smoothing, radial scale or global inflation. Explicit
section rows move forward in local+Y, preserving all X/Z coordinates.
"""
import bpy,ast,json,hashlib
import numpy as np
from pathlib import Path
from collections import Counter
from mathutils import Vector
OUT=Path(__file__).resolve().parent;H=OUT.parent;SOURCE=H/'candidate-r23/Mia_FaceFinish7_BlinkR23_v22.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest()
tree=ast.parse((H.parent/'finish-6/dependencies/legacy_snapshot_apply_interp.py').read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),'frozen-guards','exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));source_sha=sha(SOURCE);skin=bpy.data.objects['MIA_V14_SculptedSkin'];P=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);before=snapshots();faces=np.array([list(p.vertices[:3]) for p in skin.data.polygons]);delta=np.zeros_like(P)
# Existing high section heights are retained. Forward projection is restored
# across a broad malar section; upper support blends into the unchanged lid,
# and the lower section loses fullness before the unchanged jaw/chin.
regions={
 'superior_malar_transition':{232:.3,242:2.8,248:.5,250:2.,251:1.6,253:1.4,323:.7,325:.4,328:.4,329:.3,333:.2},
 'high_malar_apex':{233:6.5,234:3.8,236:6.,249:6.5,252:4.2,324:1.5},
 'short_anterior_buccal_fullness':{254:5.8,255:5.3,256:4.5,257:3.,258:4.,295:1.2,296:1.5,294:3.,292:3.6},
 'inferior_buccal_fade':{290:2.6,291:2.,293:1.9,297:1.4,302:.4,278:.5,259:.5}}
mapping={};semantic={};used=set()
for region,values in regions.items():
 for i,forward_mm in values.items():
  assert P[i,0]>0 and i not in used;used.add(i);reflected=P[i]*np.array([-1,1,1]);negative=np.where(P[:,0]<0)[0];j=int(negative[np.argmin(np.linalg.norm(P[negative]-reflected,axis=1))]);assert j not in used and np.linalg.norm(P[j]-reflected)<.002;used.add(j);mapping[i]=j
  for vertex in [i,j]:delta[vertex,1]=forward_mm/1000;semantic[vertex]=region
boundary_counts=Counter(tuple(sorted((int(f[i]),int(f[(i+1)%3])))) for f in faces for i in range(3));boundary={i for edge,count in boundary_counts.items() if count==1 for i in edge};assert np.max(np.linalg.norm(delta[list(boundary)],axis=1))==0
assert np.max(abs(delta[:,[0,2]]))==0 and np.max(abs(delta[588:]))==0
def normals(points):
 n=np.cross(points[faces[:,1]]-points[faces[:,0]],points[faces[:,2]]-points[faces[:,0]]);return n/np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-20)
dots=np.sum(normals(P)*normals(P+delta),axis=1);assert dots.min()>.35,('Normal reversal risk',float(dots.min()))
# The actual subdivided eye boundary is a hard contact guard, not just a
# low-resolution cage invariant.
def evaluated_boundary():
 bpy.context.view_layer.update();obj=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=obj.to_mesh();p=np.array([tuple(v.co) for v in mesh.vertices]);f=[list(q.vertices) for q in mesh.polygons];ec=Counter(tuple(sorted((v[k],v[(k+1)%len(v)]))) for v in f for k in range(len(v)));ids=sorted({i for edge,n in ec.items() if n==1 for i in edge if .01<abs(p[i,0])<.061 and p[i,1]>.035 and 1.525<p[i,2]<1.558});obj.to_mesh_clear();return ids,p[ids]
eye_ids,eye_before=evaluated_boundary();errors=apply(skin,delta);ids,eye_after=evaluated_boundary();assert ids==eye_ids and np.array_equal(eye_before,eye_after),'Evaluated eye contact moved'
after=snapshots()
for name in before:
 if name!=skin.name:assert before[name]==after[name],name
 else:
  for field in ['uv','topology','weights','materials','matrix','modifiers']:assert before[name][field]==after[name][field],field
assert max(errors.values())<2e-7
native=OUT/'Mia_FaceFinish7_MalarVolumeR25_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));native_sha=sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after and sha(SOURCE)==source_sha
rows=[{'owner':'MIA_V14_SculptedSkin','id':i,'region':semantic[i],'before':P[i].tolist(),'after':(P[i]+delta[i]).tolist(),'delta':delta[i].tolist()} for i in sorted(semantic)]
report={'source':{'path':str(SOURCE),'sha256':source_sha},'native':{'path':str(native),'sha256':native_sha},'recipe':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},'anatomical_sections_forward_mm':regions,'actual_mirror_mapping':mapping,'changed_skin_vertices':len(rows),'maximum_forward_m':float(delta[:,1].max()),'minimum_old_new_normal_dot':float(dots.min()),'all_x_z_exact':True,'all_unrelated_owners_exact':True,'actual_evaluated_eye_boundary_exact':True,'evaluated_eye_boundary_vertex_count':len(eye_ids),'body_hair_carrier_lashes_ears_chin_jaw_unchanged':True,'relative_key_errors':errors,'limits':['One bounded form proposal responding to user rejection of R19/R23 flattened cheek; no whole-art PASS.','Fixed-X section differences diagnose recession but are not homologous volume or a numeric shape target.','Actual multiangle and source review required; no new smoothing or makeup.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'vertex-deltas.json').write_text(json.dumps(rows,indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(report,indent=2))
