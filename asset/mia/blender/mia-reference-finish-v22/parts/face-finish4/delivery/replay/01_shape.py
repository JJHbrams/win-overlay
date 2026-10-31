"""v22 connected nasal/philtrum/chin profile on actual Basis; source preserved."""
import bpy,sys,ast,json,hashlib,math,argparse,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));import review_setup as r
ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(r.SOURCE));ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source);OUT=Path(a.output_dir);OUT.mkdir(parents=True,exist_ok=True)
recipe=Path(__file__);beforehash=r.sha(SOURCE)
# Reuse the exact data snapshot definition, without executing old build code.
old=r.ROOT/'asset/mia/blender/mia-face-correction-v20/candidate-orbital-v21/main/exact-recipe.py';tree=ast.parse(old.read_text());ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest();exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply','interp']],type_ignores=[]),str(old),'exec'))
(OUT/'source-view-definitions.json').write_text(json.dumps([{**v,'reference_sha256':r.sha(v['reference'])} for v in r.VIEWS],indent=2))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));skin=bpy.data.objects['MIA_V14_SculptedSkin'];assert not skin.get('v22_profile_guide');before=snapshots();packed={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}
for i in bpy.data.images:
 if i.packed_file:i.use_fake_user=True
coords=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);deltas=[]
zs=[1.460,1.465,1.475,1.485,1.493,1.500,1.507,1.5135,1.519,1.527,1.537,1.550,1.565]
ys=[0,.0012,.0015,.0005,-.0010,-.0022,-.0010,.0035,.0032,.0010,-.0005,-.0002,0]
APEX_LIFT=.0022
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def eye_field(p):
 x,y,z=map(float,p);cx=math.copysign(.0345,x);w=math.exp(-((abs(x)-.0345)/.025)**6-((z-1.540)/.014)**4)*smooth((y-.024)/.026)
 return Vector(((x-cx)*.08*w,(y-.057)*.08*w,.0005*math.exp(-((z-1.533)/.0045)**2)*w))
def jaw_field(p):
 x,y,z=map(float,p);w=smooth((z-1.460)/.008)*math.exp(-((z-1.475)/.015)**4)*math.exp(-(x/.045)**4)*smooth(y/.020)*smooth((.066-y)/.035)
 return Vector((0,0,.0045*w))
for x,y,z in coords:
 radius=float(np.interp(z,[1.46,1.48,1.50,1.515,1.53,1.55],[.034,.030,.020,.013,.012,.014]));front=smooth((y-.035)/.020);w=math.exp(-(abs(x)/radius)**4)*front
 dy=interp(z,zs,ys,True)*w
 dz=APEX_LIFT*math.exp(-((z-1.5145)/.0060)**2)*math.exp(-(x/.0115)**4)*front
 dx=-x*.055*math.exp(-((z-1.534)/.012)**4)*math.exp(-(x/.016)**4)*front
 deltas.append(Vector((dx,dy,dz))+eye_field((x,y,z))+jaw_field((x,y,z)))
work=coords+np.asarray([list(d) for d in deltas]);start=work.copy();adj=[set() for p in work]
for e in skin.data.edges:
 i,j=e.vertices;adj[i].add(j);adj[j].add(i)
fair_weights=np.array([math.exp(-(x/.016)**4)*smooth((z-1.506)/.008)*(1-smooth((z-1.546)/.012))*smooth((y-.04)/.025) for x,y,z in coords])
for iteration in range(6):
 normals=np.zeros_like(work)
 for p in skin.data.polygons:
  ids=list(p.vertices);nn=np.cross(work[ids[1]]-work[ids[0]],work[ids[2]]-work[ids[0]])
  for i in ids:normals[i]+=nn
 normals/=np.maximum(np.linalg.norm(normals,axis=1),1e-12)[:,None];step=np.zeros_like(work)
 for i,nei in enumerate(adj):
  if not nei or fair_weights[i]<1e-4:continue
  ni=list(nei);weights=1/np.maximum(np.linalg.norm(work[ni]-work[i],axis=1),.0005);lap=np.average(work[ni],axis=0,weights=weights)-work[i];step[i]=normals[i]*np.clip(np.dot(lap,normals[i]),-.0005,.0005)*.35*fair_weights[i]
 work+=step
fair=work-start;length=np.linalg.norm(fair,axis=1);fair*=np.minimum(1,.0012/np.maximum(length,1e-12))[:,None]
deltas=[d+Vector(f) for d,f in zip(deltas,fair)]
errors={'MIA_V14_SculptedSkin':apply(skin,deltas)};skin['v22_profile_guide']='Basis connected nasal profile, local nasal fairing, coordinated orbital width/curvature, rising underchin; no global scale.';changed={'MIA_V14_SculptedSkin'};all_deltas={'MIA_V14_SculptedSkin':deltas}
body=bpy.data.objects['MIA_V06_BODY_SKIN'];toskin=skin.matrix_world.inverted()@body.matrix_world;back=toskin.inverted().to_3x3();bd=[];body_mask=[]
for i,v in enumerate(body.data.shape_keys.key_blocks[0].data if body.data.shape_keys else body.data.vertices):
 world=body.matrix_world@v.co;d=back@jaw_field(toskin@v.co) if world.z>=1.460 else Vector();bd.append(d)
 if d.length>1e-10:body_mask.append({'vertex':i,'source_basis_world_z':world.z,'delta_local_m':list(d)})
errors[body.name]=apply(body,bd);changed.add(body.name);all_deltas[body.name]=bd
eyes=bpy.data.objects['MIA_V14_EyeSurface'];toskin=skin.matrix_world.inverted()@eyes.matrix_world;back=toskin.inverted().to_3x3();iris={i for p in eyes.data.polygons if p.material_index==5 for i in p.vertices};ed=[]
for v in eyes.data.vertices:
 q=toskin@v.co
 if v.index in iris:d=Vector(((q.x-math.copysign(.0345,q.x))*.10,(q.y-.057)*.10,0))
 else:d=eye_field(q);d.y-=.00035*smooth((abs(q.x)-.049)/.009)
 ed.append(back@d)
errors[eyes.name]=apply(eyes,ed);changed.add(eyes.name);all_deltas[eyes.name]=ed
imat=eyes.material_slots[5].material.copy();imat.name='MIA_V22_Reference_GrayIris';nodes=imat.node_tree.nodes
width=[n for n in nodes if n.type=='MATH' and n.operation=='DIVIDE' and abs(n.inputs[1].default_value-.28224)<1e-5];assert len(width)==1;width[0].inputs[1].default_value*=1.04
pup=[n for n in nodes if n.type=='MATH' and n.operation=='LESS_THAN' and abs(n.inputs[1].default_value-.285)<1e-5];assert len(pup)==1;pup[0].inputs[1].default_value=.215
for n in nodes:
 if n.type=='VALTORGB' and len(n.color_ramp.elements)==3:
  for e,col in zip(n.color_ramp.elements,[(.38,.44,.44,1),(.22,.28,.29,1),(.055,.075,.082,1)]):e.color=col
eyes.material_slots[5].material=imat;assert eyes.material_slots[1].material.use_backface_culling
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bvh=BVHTree.FromPolygons([v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render or not any(t in o.name for t in ['UpperLash','OuterWing']):continue
 toskin=skin.matrix_world.inverted()@o.matrix_world;back=toskin.inverted();dd=[]
 for v in o.data.shape_keys.key_blocks[0].data if o.data.shape_keys else o.data.vertices:
  q=toskin@v.co;q+=eye_field(q);hit=bvh.ray_cast(Vector((q.x,.3,q.z)),Vector((0,-1,0)))[0]
  if hit is not None:q.y=hit.y+.00045
  dd.append(back@q-v.co)
 errors[o.name]=apply(o,dd);changed.add(o.name);all_deltas[o.name]=dd
after=snapshots()
for n in before:
 if n not in changed:assert before[n]==after[n],n
 else:
  for k in ['uv','topology','weights','matrix','modifiers']:assert before[n][k]==after[n][k],k
  if n!='MIA_V14_EyeSurface':assert before[n]['materials']==after[n]['materials']
assert max(v for e in errors.values() for v in e.values())<2e-7
native=OUT/'Mia_FaceShape_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));nh=r.sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after;assert {i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}==packed
report={'source':r.artifact(SOURCE),'native':r.artifact(native),'recipe_sha256':r.sha(recipe),'coordinate_definition':'Field on actual Basis; identical delta applied to all 47 key coordinates and separate vertex cache. Source evaluated geometry remains distinct from cache.','profile_guide_z':zs,'profile_depth_delta':ys,'nose_apex_lift_m':APEX_LIFT,'nasal_fairing_max_m':float(np.linalg.norm(fair,axis=1).max()),'max_delta_m':max(d.length for d in deltas),'changed_owners':sorted(changed),'relative_key_errors':errors,'before':before,'after':after,'packed_image_count':len(packed),'packed_exact':True,'all_other_owners_unchanged':True,'body_headcap_vertex_deltas':body_mask,'body_below_1p46_basis_unmodified':all(x['source_basis_world_z']>=1.460 for x in body_mask),'eye_change':'Aperture X/Y8percent, lowerlid+.5mm; whole iris carrier X/Y10percent; UV gray width4percent and pupil radius .285 to .215; culling retained','limitations':['Shape trial pending source-art boards; no art acceptance','Reference SIDE is small and stylized; exact nose depth not ground truth','Source fixed skin pigment unchanged for shape comparison','Headcap underchin boundary now raised locally; integration must use explicit vertex deltas, not replace whole Body']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'exact-recipe.py').write_bytes(recipe.read_bytes());(OUT/'vertex-deltas.json').write_text(json.dumps([{'vertex':i,'delta_local_m':list(d)} for i,d in enumerate(deltas) if d.length>1e-8],indent=2))
r.renders(native,OUT/'renders');assert r.sha(SOURCE)==beforehash and r.sha(native)==nh;print('SHAPE_DONE',nh)
