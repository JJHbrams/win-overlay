import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;SRC=OUT/'Mia_BodyCorrection_v20.blend';DIAG=OUT.parent/'mia-lookdev-audit-v19/Mia_LookdevReview_v19.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();frozen=sha(SRC)
bpy.ops.wm.open_mainfile(filepath=str(SRC));candidate=[v.co.copy() for v in bpy.data.objects['MIA_V06_BODY_SKIN'].data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(DIAG));s=bpy.context.scene;body=bpy.data.objects['MIA_V06_BODY_SKIN'];original=[v.co.copy() for v in body.data.vertices];layer=s.view_layers['V19_DiffuseClay_SkinOnly'];bpy.context.window.view_layer=layer
for vl in s.view_layers:vl.use=vl==layer
s.render.resolution_x=s.render.resolution_y=1024;s.render.resolution_percentage=100;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;cam=s.camera;cam.data.type='ORTHO'
light_base={'V19_Key':((-1.8,-3,2.5),200,2.0),'V19_Fill':((2,-2,1.7),70,2.0),'V19_Edge':((0,2,2.3),30,1.8)}
records=[]
for state,coords in [('before',original),('after',candidate)]:
 for v,q in zip(body.data.vertices,coords):v.co=q
 body.data.update()
 cases=[('close_profile',90,.66,1.20),('close_three_quarter',45,.66,1.20)]
 if state=='after':cases+=[('front',0,1.889420911300281,.8397017427958733),('profile',90,1.889420911300281,.8397017427958733),('back',180,1.889420911300281,.8397017427958733),('three_quarter',45,1.889420911300281,.8397017427958733)]
 for name,deg,scale,target in cases:
  t=math.radians(deg);cam.data.ortho_scale=scale;cam.location=(3*math.sin(t),-3*math.cos(t),target);cam.rotation_euler=(Vector((0,0,target))-cam.location).to_track_quat('-Z','Y').to_euler()
  for ln,(loc,power,size) in light_base.items():
   o=bpy.data.objects[ln];x,y,z=loc;o.location=(x*math.cos(t)-y*math.sin(t),x*math.sin(t)+y*math.cos(t),z);o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=power;o.data.size=size
  s.render.filepath=str(OUT/(state+'_'+name+'.png'));bpy.ops.render.render(write_still=True,layer=layer.name);records.append({'state':state,'view':name,'azimuth':deg,'scale':scale,'target_z':target})
assert sha(SRC)==frozen
(OUT/'render-evidence.json').write_text(json.dumps({'candidate_sha256':frozen,'diagnostic_sha256':sha(DIAG),'method':'Fresh-open candidate coordinates transferred verbatim to identical source body in frozen v19 diagnostic rig; same modifiers/pose; no saves','cameras':records,'lighting':light_base},indent=2))
