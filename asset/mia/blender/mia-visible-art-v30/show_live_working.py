"""Live MCP preview of an explicit WIP native. Runtime navigation never saves the asset."""
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Matrix,Vector

P=Path(__file__).resolve().parent
native=Path(REVIEW_NATIVE).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native)==REVIEW_SHA
old=P.parent/'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json'
spec=json.loads(old.read_text())['views'][0]['candidate_camera']
bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False)
s=bpy.context.scene
for o in s.objects:
 if o.type=='LIGHT':o.hide_render=True
for i,l in enumerate(spec['lighting']['areas']):
 data=bpy.data.lights.new('V30_LIVE_'+str(i),'AREA');data.energy=l['watts'];data.shape=l['shape'];data.size=l['size'];data.color=l['color'];o=bpy.data.objects.new(data.name,data);s.collection.objects.link(o);o.matrix_world=Matrix(l['matrix'])
w=bpy.data.worlds.new('V30_LIVE_SourceWorld');w.use_nodes=True;n=w.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(*spec['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=spec['lighting']['world_strength'];wo=n.new('ShaderNodeOutputWorld');wo.is_active_output=True;w.node_tree.links.new(bg.outputs[0],wo.inputs['Surface']);s.world=w
cam=bpy.data.objects.new('V30_LIVE_Head',bpy.data.cameras.new('V30_LIVE_Head'));s.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=spec['ortho_scale'];cam.matrix_world=Matrix(spec['matrix']);s.camera=cam
body=bpy.data.objects.new('V30_LIVE_FullBody',bpy.data.cameras.new('V30_LIVE_FullBody'));s.collection.objects.link(body);body.data.type='ORTHO';body.data.ortho_scale=1.92;body.location=(0,-4,.87);body.rotation_euler=(Vector((0,0,.87))-body.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.film_transparent=False;s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
cm=spec['color_management'];s.view_settings.view_transform=cm['view_transform'];s.view_settings.look=cm['look'];s.view_settings.exposure=cm['exposure'];s.view_settings.gamma=cm['gamma']
for o in bpy.context.view_layer.objects:o.select_set(False)
for window in bpy.context.window_manager.windows:
 for area in window.screen.areas:
  if area.type=='VIEW_3D':
   sp=area.spaces.active;sp.clip_start=.001;sp.clip_end=100;sp.region_3d.view_location=(0,0,1.55);sp.region_3d.view_distance=.45;sp.region_3d.view_perspective='ORTHO';sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.shading.type='MATERIAL';sp.shading.use_scene_lights=True;sp.shading.use_scene_world=True;sp.overlay.show_overlays=False
out=P/'live'/REVIEW_TAG;out.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update();s.render.filepath=str(out/'head.png');bpy.ops.render.render(write_still=True)
assert sha(native)==REVIEW_SHA
report={'native':str(native),'native_sha256':sha(native),'runtime_only':True,'native_saved':False,
 'status':'WIP preview, source appearance not yet accepted. Continue all remaining contract criteria.',
 'image':s.render.filepath,'image_sha256':sha(Path(s.render.filepath)),
 'camera':'ORTHO source-front, no extra2Ddisplayroll','head_pivot':[0,0,1.55],'mesh_origins_changed':False}
(out/'live-review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
