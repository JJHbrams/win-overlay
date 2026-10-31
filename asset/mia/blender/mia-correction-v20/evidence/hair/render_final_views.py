import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent;files={'before':OUT.parent/'mia-body-correction-v20/Mia_BodyCorrection_v20.blend','after':OUT/'Mia_HairCorrection_v20.blend'};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={k:sha(v) for k,v in files.items()};records=[]
for state,src in files.items():
 bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;cam=s.camera;s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;cam.data.type='ORTHO';cam.data.ortho_scale=.52;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
 for name,deg in [('front',0),('profile',90),('back',180),('three_quarter_l',45),('three_quarter_r',-45)]:
  t=math.radians(deg);cam.location=(2*math.sin(t),-2*math.cos(t),1.475);cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/(state+'_'+name+'.png'));bpy.ops.render.render(write_still=True);records.append({'file':state+'_'+name+'.png','native_sha256':hashes[state],'azimuth':deg,'ortho_scale':.52,'target_z':1.475})
assert hashes=={k:sha(v) for k,v in files.items()};(OUT/'final-five-view-evidence.json').write_text(json.dumps({'source_hashes_unchanged':hashes,'views':records,'color':'Standard/None exposure0 gamma1; existing emission toon unchanged; beauty is not physical diffuse','save_performed':False},indent=2))
