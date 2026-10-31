"""One bounded lower-lateral-cheek taper on actual Basis, all relative key deltas retained."""
import bpy,sys,ast,argparse,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent;ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(H.parent/'finish-5/Mia_FaceFinish5_v22.blend'));ap.add_argument('--output-dir',default=str(H/'continuous-candidate'));ap.add_argument('--verify-existing',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);src=Path(a.source).resolve();out=Path(a.output_dir).resolve();out.mkdir(exist_ok=True,parents=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();art=lambda p:{'path':str(Path(p)),'sha256':sha(p)};ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest();helper=H.parent/'finish-4/replay/legacy_snapshot_apply_interp.py';tree=ast.parse(helper.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),str(helper),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(src));sourcehash=sha(src);o=bpy.data.objects['MIA_V14_SculptedSkin'];assert not o.get('v22_finish6_lower_cheek');before=snapshots();packed={i.name:[hashlib.sha256(i.packed_file.data).hexdigest(),i.use_fake_user] for i in bpy.data.images if i.packed_file};p=np.array([tuple(v.co) for v in o.data.shape_keys.key_blocks[0].data]);cache=np.array([tuple(v.co) for v in o.data.vertices]);assert not any(abs(k.value)>1e-8 for k in o.data.shape_keys.key_blocks[1:]);uses={};adj=[set() for v in p]
for e in o.data.edges:i,j=e.vertices;adj[i].add(j);adj[j].add(i)
for poly in o.data.polygons:
 ids=list(poly.vertices)
 for i,j in zip(ids,ids[1:]+ids[:1]):e=tuple(sorted((i,j)));uses[e]=uses.get(e,0)+1
# Protect only actual ocular/oral boundaries; matching outer face/cap join moves continuously.
protected={i for e,n in uses.items() if n==1 for i in e if (1.53<p[i,2]<1.55 and p[i,1]>.03) or (1.48<p[i,2]<1.50 and abs(p[i,0])<.020 and p[i,1]>.05)}
for _ in range(2):protected|={j for i in list(protected) for j in adj[i]}
def evaluated():
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();q=np.array([tuple(v.co) for v in me.vertices]);ev.to_mesh_clear();return q
evbefore=evaluated()
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
delta=np.zeros_like(p)
for i,(x,y,z) in enumerate(p):
 if i in protected:continue
 # Compact broad support below orbital rim, above jaw/cap boundary; no global X scaling.
 vertical=smooth((z-1.480)/.012)*(1-smooth((z-1.509)/.018))
 lateral=smooth((abs(x)-.023)/.020)*(1-smooth((abs(x)-.070)/.014))
 front=smooth((y+.040)/.032)
 delta[i,0]=-np.sign(x)*.0024*vertical*lateral*front
errors=apply(o,delta);o['v22_finish6_lower_cheek']='Continuous lower lateral cheek plus matching headcap X taper,2.4mm maximum; eye/oral boundaries protected2rings; all key relative deltas retained.'
body=bpy.data.objects['MIA_V06_BODY_SKIN'];toskin=o.matrix_world.inverted()@body.matrix_world;back=toskin.inverted().to_3x3();bdata=body.data.shape_keys.key_blocks[0].data if body.data.shape_keys else body.data.vertices;bp=np.array([tuple(v.co) for v in bdata]);bd=[];worldz=[]
def bodyeval():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();q=np.array([tuple(ev.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return q
be=bodyeval()
for i,pb in enumerate(bp):
 world=body.matrix_world@Vector(pb);worldz.append(world.z);x,y,z=toskin@Vector(pb)
 vertical=smooth((z-1.480)/.012)*(1-smooth((z-1.509)/.018));lateral=smooth((abs(x)-.023)/.020)*(1-smooth((abs(x)-.070)/.014));front=smooth((y+.040)/.032)
 d=Vector((-np.sign(x)*.0024*vertical*lateral*front,0,0)) if world.z>=1.46 else Vector();bd.append(back@d)
body_errors=apply(body,bd);bae=bodyeval();bed=bae-be
after=snapshots();evafter=evaluated();evdelta=evafter-evbefore

for name in before:
 if name not in [o.name,body.name]:assert before[name]==after[name],name
 else:
  for k in ['uv','topology','weights','materials','matrix','modifiers']:assert before[name][k]==after[name][k],k
assert max(errors.values())<2e-7;assert max(body_errors.values(),default=0)<2e-7;assert all(Vector(d).length<1e-10 for z,d in zip(worldz,bd) if z<1.46);assert len(evbefore)==len(evafter);assert np.max(abs(evdelta[:,1:]))<2e-6
native=out/'Mia_FaceFinish6_v22.blend';assert a.verify_existing==native.exists();
if not a.verify_existing:bpy.ops.wm.save_as_mainfile(filepath=str(native))
bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after;assert {i.name:[hashlib.sha256(i.packed_file.data).hexdigest(),i.use_fake_user] for i in bpy.data.images if i.packed_file}==packed;assert sha(src)==sourcehash
report={'source':art(src),'native':art(native),'recipe':art(__file__),'helper':art(helper),'coordinate_definition':'Field on source actual Basis; same pervertex delta applied to all47 keys and independent vertex cache. Neutral depsgraph evaluated before/after measured.','changed_owners':['MIA_V14_SculptedSkin','MIA_V06_BODY_SKIN >=1.46 headcap only'],'body_basis_below1p46_exact':all(Vector(d).length<1e-10 for z,d in zip(worldz,bd) if z<1.46),'body_evaluated_below1p46_max_delta_m':float(np.linalg.norm(bed[be[:,2]<1.46],axis=1).max()),'body_evaluated_max_delta_m':float(np.linalg.norm(bed,axis=1).max()),'eyes_lashes_hair_materials_unchanged':True,'relative_key_errors':{'MIA_V14_SculptedSkin':errors,'MIA_V06_BODY_SKIN':body_errors},'all_original_uv_topology_weights_unchanged':True,'packed_exact_count':len(packed),'max_basis_delta_m':float(np.linalg.norm(delta,axis=1).max()),'max_evaluated_delta_m':float(np.linalg.norm(evdelta,axis=1).max()),'max_evaluated_yz_change_m':float(np.max(abs(evdelta[:,1:]))),'changed_basis_z_range':[float(p[np.linalg.norm(delta,axis=1)>1e-9,2].min()),float(p[np.linalg.norm(delta,axis=1)>1e-9,2].max())],'protected_control_vertices':sorted(protected),'before':before,'after':after,'status':'UNSELECTED_LOCAL_GEOMETRY_TRIAL','limits':['Fixed registration does not establish true hidden cheek/skull width.','No nose pigment/shape correction; nose side graphic persists in albedo-only and is a separate mapping issue.','No aperture enlargement or iris change.','Existing bodycap/jaw underchin and inherited deformation limitations remain.']}
(out/'manifest.json').write_text(json.dumps(report,indent=2));(out/'vertex-deltas.json').write_text(json.dumps([{'vertex':i,'source_basis':p[i].tolist(),'delta_local':d.tolist()} for i,d in enumerate(delta) if np.linalg.norm(d)>1e-9],indent=2));(out/'body-headcap-deltas.json').write_text(json.dumps([{'vertex':i,'source_basis_world_z':worldz[i],'source_basis_local':bp[i].tolist(),'delta_local':list(d)} for i,d in enumerate(bd) if Vector(d).length>1e-9],indent=2));(out/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());print(json.dumps({k:report[k] for k in ['native','max_basis_delta_m','max_evaluated_delta_m','max_evaluated_yz_change_m','changed_basis_z_range']},indent=2))
