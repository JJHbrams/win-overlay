"""Audit the two actual contributions of frozen E, without changing its shape.

The decomposition replays E's exact affine width transform and exact linear
biharmonic extension separately on its core and tissue terms. Inherited
baseline breast shape in (1-f)*baseline is explicitly retained in actual-core,
not silently replaced with an idealized new diagnostic rib cage.
"""
import bpy,numpy as np,json,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;OUT=P/'mass-audit-E';OUT.mkdir(exist_ok=True)
S=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/face-rebuild-10/selected-v27/native/e9c865412130-Mia_Foundation_v27.blend')
E=P/'Mia_ConnectedThorax_v28_E.blend';CORE=OUT/'Mia_E_ActualCoreContribution.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def c2(t):t=np.clip(t,0,1);return t*t*t*(t*(t*6-15)+10)
d=json.loads((P/'sculpt-D-report.json').read_text());patch=np.load(P/'thorax-E-delta.npz');inspection=np.load(P/'inspection.npz');w=inspection['world'];mat=inspection['matrix'];core_pre=w.copy();pure_pre=w.copy();tissue_pre=np.zeros_like(w);factors=np.zeros(len(w));gates=np.zeros(len(w))
for row in d['records']:
 i=row['index'];f=row['blend']
 if f<1e-8:continue
 support=np.array(row['rib_support']);target=(np.array(row['world_after'])-w[i])/f+w[i];tissue=target-support
 core_pre[i]=w[i]+(support-w[i])*f;pure_pre[i]=support;tissue_pre[i]=tissue*.74*f
 height=float(c2((w[i,2]-1.17)/.055)*c2((1.335-w[i,2])/.055));g=1-.16*height
 for a in [core_pre,pure_pre]:a[i,0]=-.0004777+(a[i,0]+.0004777)*g
 tissue_pre[i,0]*=g;factors[i]=f;gates[i]=g
pre_error=float(abs(core_pre+tissue_pre-w-patch['pre_extension_delta']).max());assert pre_error<1e-12
free=patch['extension_free_indices'];lookup={int(i):j for j,i in enumerate(free)};neighbors={i:{} for i in range(3957)}
for a,b in inspection['edges']:
 a,b=int(a),int(b)
 if a>=3957 or b>=3957:continue
 value=1/max(np.linalg.norm(w[a]-w[b]),1e-5);neighbors[a][b]=value;neighbors[b][a]=value
nodes=sorted(set(free.tolist())|{j for i in free for j in neighbors[int(i)]});A=np.zeros((len(nodes),len(free)));coefficients=[]
for r,i in enumerate(nodes):
 coeff={i:1.};total=sum(neighbors[i].values())
 if total:
  for j,value in neighbors[i].items():coeff[j]=coeff.get(j,0)-value/total
 for j,value in coeff.items():
  if j in lookup:A[r,lookup[j]]+=value
 coefficients.append(coeff)
def extend(delta):
 rhs=np.zeros((len(nodes),3))
 for r,coeff in enumerate(coefficients):
  for j,value in coeff.items():
   if j not in lookup:rhs[r]-=value*delta[j]
 out=delta.copy();out[free]=np.linalg.lstsq(A,rhs,rcond=1e-9)[0];return out
core_delta=extend(core_pre-w);tissue=extend(tissue_pre);pure_delta=extend(pure_pre-w);inherited=core_delta-pure_delta
expected=np.zeros_like(w);expected[patch['indices']]=patch['world_delta'];sum_error=float(abs(core_delta+tissue-expected).max());assert sum_error<1e-12
# The actual core native uses exactly this derived field on all42 keys. This
# is diagnostic only: it is not a new proposal or a replacement of frozen E.
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);o=bpy.data.objects['MIA_V27_SharedHeadBody'];m=o.data;keys=m.shape_keys.key_blocks
local=core_delta@np.linalg.inv(mat[:3,:3]).T;idx=np.flatnonzero(np.linalg.norm(local,axis=1)>1e-9)
for key in keys:
 for i in idx:key.data[int(i)].co+=Vector(local[i])
for i in idx:m.vertices[int(i)].co=keys[0].data[int(i)].co
o['MIA_MassAudit']='Actual E core contribution derived by exact affine/linear replay; inherited baseline term intentionally retained; NOT an accepted ideal ribcage'
bpy.context.view_layer.update()
if not CORE.exists():bpy.ops.wm.save_as_mainfile(filepath=str(CORE))
np.savez_compressed(OUT/'actual-E-two-mass-decomposition.npz',baseline_world=w,actual_core_world=w+core_delta,tissue_offset_world=tissue,pure_support_world=w+pure_delta,inherited_baseline_residual_world=inherited,core_pre_world=core_pre,tissue_pre_world=tissue_pre,pure_pre_world=pure_pre,factors=factors,width_gate=gates,triangles=inspection['triangles'],matrix=mat)
# Snapshot evaluated actual core and saved E with outline nodes disabled. Same
# topology is checked before corresponding surface offsets/sections are used.
evals={}
for label,path in [('actual-core',CORE),('skin',E)]:
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False);s=bpy.context.scene;s.frame_set(1);owner=bpy.data.objects['MIA_V27_SharedHeadBody']
 for k in owner.data.shape_keys.key_blocks[1:]:k.value=0
 for mod in owner.modifiers:
  if mod.type=='NODES':mod.show_viewport=False;mod.show_render=False
 bpy.context.view_layer.update();ev=owner.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();em.calc_loop_triangles();v=np.array([list(ev.matrix_world@p.co) for p in em.vertices]);f=np.array([list(t.vertices) for t in em.loop_triangles]);loops=np.array([q.vertex_index for q in em.loops]);polys=np.array([(q.loop_start,q.loop_total) for q in em.polygons]);ev.to_mesh_clear();evals[label]=(v,f,loops,polys);np.savez_compressed(OUT/('evaluated-'+label+'.npz'),vertices=v,triangles=f,loop_vertices=loops,polygon_loop_ranges=polys)
assert np.array_equal(evals['actual-core'][2],evals['skin'][2]) and np.array_equal(evals['actual-core'][3],evals['skin'][3])
np.savez_compressed(OUT/'evaluated-tissue-offset.npz',offset=evals['skin'][0]-evals['actual-core'][0])
region=(w[:,2]>1.17)&(w[:,2]<1.38)&(abs(w[:,0])<.15)
def maximum(v):return float(np.linalg.norm(v[region],axis=1).max())
report={'frozen_E':{'path':str(E),'sha256':sha(E)},'actual_core_native':{'path':str(CORE),'sha256':sha(CORE)},'algebra':'Epre = narrow[(1-f)*baseline + f*Dsupport + f*.74*Dtissue]; H is the exact linear upper/axillary biharmonic extension. ActualEcore = baseline + H(narrow[(1-f)*baseline+f*Dsupport]-baseline); actualEtissue = H(narrow-vector[f*.74*Dtissue]).','pre_extension_sum_error_m':pre_error,'full_extension_sum_error_m':sum_error,'same_evaluated_topology':True,'evaluated_vertices':len(evals['skin'][0]),'inherited_baseline_residual_max_m':maximum(inherited),'inherited_baseline_residual_count_gt1mm_in_thorax':int(np.count_nonzero(region&(np.linalg.norm(inherited,axis=1)>.001))),'actual_tissue_offset_max_m':maximum(tissue),'corefit_provenance':'Dsupport front/back/width tables were native-section-informed estimates and include sternum/front-center values inherited from e9 in breast-height range. This audit does not assert that those center-front values exclude prior breast mass. Upper extension also retains baseline contributions by construction.','interpretation_status':'UNREVIEWED core-only anatomy. E is not adopted; surface continuity review alone did not verify two anatomical masses.','unchanged_sources':sha(S)=='e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4'}
(OUT/'actual-two-mass-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('ACTUAL_TWO_MASS_DECOMPOSED',json.dumps(report),flush=True)
