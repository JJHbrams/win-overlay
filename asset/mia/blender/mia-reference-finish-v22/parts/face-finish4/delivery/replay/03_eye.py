"""Actual tapered upper-lash ribbon and visible-range iris art; no skin/body/hair edits."""
import bpy,sys,json,math,hashlib,ast,argparse,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent));import review_setup as r
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
ah=lambda p:hashlib.sha256(np.asarray(p).tobytes()).hexdigest();old=r.ROOT/'asset/mia/blender/mia-face-correction-v20/candidate-orbital-v21/main/exact-recipe.py';tree=ast.parse(old.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['snapshots','apply']],type_ignores=[]),str(old),'exec'))
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;before=snapshots();packed={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file};skin=bpy.data.objects['MIA_V14_SculptedSkin'];ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();b=BVHTree.FromPolygons([skin.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear();changes={};errors={}
ink=bpy.data.materials.new('MIA_V22_TaperedLash_DeepInk');ink.use_nodes=True;n=ink.node_tree.nodes;n.clear();em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.008,.006,.010,1);out=n.new('ShaderNodeOutputMaterial');ink.node_tree.links.new(em.outputs[0],out.inputs[0])
for o in s.objects:
 if o.name not in ['MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1']:continue
 co=[v.co.copy() for v in o.data.shape_keys.key_blocks[0].data];count=len(co)//2;ds=[]
 for i,p in enumerate(co):
  t=(i//2)/max(count-1,1);w=max(0,math.sin(math.pi*t))**.65;d=Vector((0,0,(.0011 if i%2 else -.00025)*w));q=o.matrix_world@(p+d);hit=b.ray_cast(Vector((q.x,-.3,q.z)),Vector((0,1,0)))[0]
  if hit:q.y=min(q.y,hit.y-.00055)
  d=o.matrix_world.inverted()@q-p;ds.append(d)
 errors[o.name]=apply(o,ds);changes[o.name]=[{'vertex':i,'delta_local_m':list(d)} for i,d in enumerate(ds) if d.length>1e-9];o.material_slots[0].material=ink
eyes=bpy.data.objects['MIA_V14_EyeSurface'];m=eyes.material_slots[5].material.copy();m.name='MIA_V22_Iris_VisibleUpperAndLowerTone';n=m.node_tree.nodes;l=m.node_tree.links;grad=next(x for x in n if x.type=='VALTORGB' and len(x.color_ramp.elements)==3)
stops=[(.26,(.27,.34,.36,1)),(.32,(.54,.62,.62,1)),(.37,(.31,.39,.41,1)),(.435,(.075,.11,.13,1)),(.50,(.025,.038,.05,1))];els=grad.color_ramp.elements
while len(els)>1:els.remove(els[-1])
for i,(pos,col) in enumerate(stops):e=els[0] if i==0 else els.new(pos);e.position=pos;e.color=col
grad.color_ramp.interpolation='EASE';grad.name='MIA_V22_VisibleIrisToneRange'
py=next(x for x in n if x.type=='MATH' and x.operation=='ADD' and abs(x.inputs[1].default_value-.29)<1e-5);dest=[link.to_socket for link in list(l) if link.from_node==py];stretch=n.new('ShaderNodeMath');stretch.operation='DIVIDE';stretch.inputs[1].default_value=1.25;l.new(py.outputs[0],stretch.inputs[0])
for socket in dest:l.new(stretch.outputs[0],socket)
eyes.material_slots[5].material=m;after=snapshots();allowed=set(changes)|{eyes.name}
for name in before:
 if name not in allowed:assert before[name]==after[name],name
 else:
  for key in ['uv','topology','weights','matrix','modifiers']:assert before[name][key]==after[name][key],(name,key)
assert before[eyes.name]['co']==after[eyes.name]['co'];assert max(x for d in errors.values() for x in d.values())<2e-7
for i in bpy.data.images:
 if i.packed_file:i.use_fake_user=True
native=OUT/'Mia_FaceFinish_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));nh=r.sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert snapshots()==after
for name,digest in packed.items():assert hashlib.sha256(bpy.data.images[name].packed_file.data).hexdigest()==digest,name
parent=json.loads((SOURCE.parent/'manifest.json').read_text());report={**parent,'native':r.artifact(native),'eye_finish_source':r.artifact(SOURCE),'eye_finish_recipe_sha256':r.sha(__file__),'eye_finish_changes':changes,'eye_finish_key_errors':errors,'eye_finish_before':before,'eye_finish_after':after,'eye_finish_iris_geometry_unchanged':True,'iris_visible_uv_range':[.28,.45],'iris_new_stops':stops,'lash_reason':'Old paint supplied much of the thick band. Actual visible tapered ribbon expanded1.35mm at middle and reseated; same offsets applied to both lash keys.','eye_finish_limit':'Small neutral/Close check required; existing Close follower is not a complete expression rig.'}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'exact-eye-recipe.py').write_bytes(Path(__file__).read_bytes());shutil.copyfile(SOURCE.parent/'source-view-definitions.json',OUT/'source-view-definitions.json');print('EYE_FINISH_DONE',nh)
