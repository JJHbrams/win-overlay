"""Save WIP with actual source light/cameras and stable orthographic navigation."""
import bpy, sys, json, hashlib, argparse
from pathlib import Path
from mathutils import Matrix, Vector
P=Path(__file__).resolve().parent
sys.path.insert(0,'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-eye-lash-v29')
from audit_mesh_helpers import snapshot
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
src=Path(a.input).resolve();dest=Path(a.output).resolve()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(src)==a.sha256
assert not dest.exists()
bo,_,bm,bi=snapshot(src)
s=bpy.context.scene;s.frame_set(1)
pkg=json.loads((P.parent/'mia-orbit-thorax-review-v28/reviews/G2L-face/reference-review.json').read_text())
spec=pkg['views'][0]['candidate_camera']
for ob in s.objects:
 if ob.type=='LIGHT':ob.hide_render=True;ob.hide_set(True)
for i,l in enumerate(spec['lighting']['areas']):
 data=bpy.data.lights.new('MIA_SourceReview_'+l['role'],'AREA');data.energy=l['watts'];data.shape=l['shape'];data.size=l['size'];data.color=l['color']
 ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.matrix_world=Matrix(l['matrix'])
w=bpy.data.worlds.new('MIA_SourceReview_World');w.use_nodes=True;n=w.node_tree.nodes;n.clear();bg=n.new('ShaderNodeBackground');bg.inputs['Color'].default_value=(*spec['lighting']['world_linear'],1);bg.inputs['Strength'].default_value=spec['lighting']['world_strength'];out=n.new('ShaderNodeOutputWorld');out.is_active_output=True;w.node_tree.links.new(bg.outputs[0],out.inputs['Surface']);s.world=w
cameras=[]
for row in pkg['views']:
 v=row['candidate_camera'];ob=bpy.data.objects.new('MIA_Review_'+row['id'],bpy.data.cameras.new('MIA_Review_'+row['id']));s.collection.objects.link(ob);ob.data.type='ORTHO';ob.matrix_world=Matrix(v['matrix']);ob.data.ortho_scale=v['ortho_scale'];ob.data.shift_x,ob.data.shift_y=v['lens_shift'];ob.data.clip_start=.1;ob.data.clip_end=10;cameras.append(ob)
body=bpy.data.objects.new('MIA_Review_FullBody',bpy.data.cameras.new('MIA_Review_FullBody'));s.collection.objects.link(body);body.data.type='ORTHO';body.data.ortho_scale=1.92;body.location=(0,-4,.87);body.rotation_euler=(Vector((0,0,.87))-body.location).to_track_quat('-Z','Y').to_euler();body.data.clip_start=.1;body.data.clip_end=10
s.camera=cameras[0]
s.render.engine='BLENDER_EEVEE';s.render.use_freestyle=False;s.render.film_transparent=False;s.render.resolution_x=s.render.resolution_y=768;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1.;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
for field in ['view_transform','look','exposure','gamma']:setattr(s.view_settings,field,spec['color_management'][field])
s['MIA_REVIEW_STATUS']='WIP. Source brows and posterior outer-eye seam component; full face/body/hair/pose style remain unaccepted.'
for ob in bpy.context.view_layer.objects:ob.select_set(False)
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   v=area.spaces.active;v.clip_start=.001;v.clip_end=10.;v.region_3d.view_location=(0,0,1.55);v.region_3d.view_distance=.45;v.region_3d.view_perspective='ORTHO';v.region_3d.view_rotation=s.camera.rotation_euler.to_quaternion();v.shading.type='MATERIAL';v.shading.use_scene_lights=True;v.shading.use_scene_world=True;v.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(dest))
ao,_,am,ai=snapshot(dest)
checks={'all_input_mesh_geometry_keys_UV_weights_drivers_modifiers_materials_matrices_exact':bo==ao,'all_input_material_graphs_exact':bm==am,'all_input_images_exact':bi==ai,'input_native_unchanged':sha(src)==a.sha256}
assert all(checks.values()),checks
report={'input':str(src),'input_sha256':sha(src),'output':str(dest),'sha256':sha(dest),'checks':checks,'scope':'Only saved review cameras/source areas/world/render/display/navigation; previous lights hidden reversibly. No mesh origin move or model edits.','default_camera':'MIA_Review_front','other_cameras':['MIA_Review_'+r['id'] for r in pkg['views'][1:]]+['MIA_Review_FullBody'],'head_pivot':[0,0,1.55],'navigation':'ORTHO','ART':'UNAPPROVED'}
dest.with_suffix('.review-scene.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('SAVED_REVIEW_SCENE',report['sha256'],checks)
