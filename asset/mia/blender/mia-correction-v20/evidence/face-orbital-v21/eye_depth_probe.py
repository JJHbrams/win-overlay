"""Read-only eye-depth causal A/B: frozen6794 skin/lid/keys, no native save."""
import bpy,sys,math,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay');sys.path.insert(0,str(ROOT/'tools/mia/blender'));import refine_mia_head_v06 as h
OUT=Path(__file__).resolve().parent/'eye-depth-diagnostic';OUT.mkdir(exist_ok=True);SOURCE=OUT.parent.parent/'frozen/Mia_FaceCorrection_v20.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;eye=bpy.data.objects['MIA_V14_EyeSurface'];skin=bpy.data.objects['MIA_V14_SculptedSkin'];base=eye.matrix_world.copy()
def meshhash(o):
 payload=[tuple(v.co) for v in o.data.vertices]
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:payload.extend(tuple(v.co) for v in k.data)
 return hashlib.sha256(np.asarray(payload).tobytes()).hexdigest()
protected={o.name:(meshhash(o),str(o.matrix_world)) for o in s.objects if o.type=='MESH' and o!=eye}
keyvalues={k.name:k.value for k in skin.data.shape_keys.key_blocks};assert all(v==0 for k,v in keyvalues.items() if k!='Basis')
members={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
for o in s.objects:
 if o.type=='MESH' and (o.name in members or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):o.hide_render=True
s.render.resolution_x=s.render.resolution_y=1400;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.camera.data.type='ORTHO';s.camera.data.ortho_scale=.29;s.camera.data.shift_x=s.camera.data.shift_y=0
slots=[]
for i,slot in enumerate(eye.material_slots):
 faces=[p for p in eye.data.polygons if p.material_index==i];ids=sorted({v for p in faces for v in p.vertices});pts=np.array([tuple(base@eye.data.vertices[v].co) for v in ids]);uses={}
 for p in faces:
  vs=list(p.vertices)
  for a,b in zip(vs,vs[1:]+vs[:1]):e=tuple(sorted((a,b)));uses[e]=uses.get(e,0)+1
 slots.append({'slot':i,'material':slot.material.name if slot.material else None,'polygons':len(faces),'vertices':len(ids),'boundary_edges':sum(v==1 for v in uses.values()),'world_min':pts.min(0).tolist() if len(pts) else None,'world_max':pts.max(0).tolist() if len(pts) else None,'backface_culling':slot.material.use_backface_culling if slot.material else None})
variants=[('retreat_1p5',.0015),('retreat_0p5',.0005),('baseline',0),('advance_0p5',-.0005),('advance_1p5',-.0015)];views=[('front',0),('left45',45),('profile90',90)];records=[]
for label,depth in variants:
 eye.matrix_world=base.copy();eye.matrix_world.translation.y+=depth;bpy.context.view_layer.update()
 for view,yaw in views:
  y=math.radians(yaw);h._aim(s.camera,(2*math.sin(y),-2*math.cos(y),1.55),(0,0,1.55));s.render.filepath=str(OUT/(label+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
  records.append({'label':label,'world_y_delta_m':depth,'positive_y':'retreat away from frontal camera','view':view,'camera_matrix':[list(r) for r in s.camera.matrix_world],'eye_matrix':[list(r) for r in eye.matrix_world]})
eye.matrix_world=base;bpy.context.view_layer.update();assert all((meshhash(bpy.data.objects[n]),str(bpy.data.objects[n].matrix_world))==p for n,p in protected.items());assert sha(SOURCE)==source_sha
report={'source':str(SOURCE),'source_sha256':source_sha,'source_sha_after':sha(SOURCE),'no_native_saved':True,'face_lids_lashes_geometry_and_keys_fixed':True,'neutral_key_values':keyvalues,'eye_structure':{'object':eye.name,'vertices':len(eye.data.vertices),'polygons':len(eye.data.polygons),'shape_keys':bool(eye.data.shape_keys),'modifiers':[(m.name,m.type) for m in eye.modifiers],'material_regions':slots},'camera':{'ortho':.29,'target':[0,0,1.55],'resolution':[1400,1400],'pixel_aspect':[1,1],'roll':0},'variants':records,'v21_difference':'Main3cd has a separate cheek depth correction plus iris vertices only retreated0.35mm in worldY; that is not equivalent to moving the whole EyeSurface as this A/B does.','limits':['Eye-only transform can alter occlusion/gaze impression but cannot change fixed skin normals or cheek wall geometry.','Native EyeSurface consists of material-separated open curved surfaces, not asserted to be a closed anatomical eyeball.','No production-depth selection is implied.']}
(OUT/'diagnostic.json').write_text(json.dumps(report,indent=2));print('EYE_DEPTH_PROBE_DONE')
