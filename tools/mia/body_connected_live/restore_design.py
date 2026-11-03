"""Remove only the owned charted design and restore the borrowed live scene."""
import bpy,numpy as np,hashlib,json
ns=bpy.app.driver_namespace;source=bpy.data.objects['MIA_V27_SharedHeadBody']
o=bpy.data.objects.get('MIA_ChartedBody_Design')
if o:
 if o.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 me=o.data;bpy.data.objects.remove(o,do_unlink=True)
 if me.users==0:bpy.data.meshes.remove(me)
gray=bpy.data.materials.get(ns.get('MIA_Charted_Gray',''))
if gray and gray.users==0:bpy.data.materials.remove(gray)
for name,state in ns['MIA_Charted_State'].items():
 o=bpy.data.objects[name];o.hide_viewport=state['hide_viewport'];o.hide_render=state['hide_render'];o.hide_set(state['hidden'])
for overlay,visible in ns.get('MIA_Charted_Overlays',[]):overlay.show_overlays=visible
for o in list(bpy.context.selected_objects):o.select_set(False)
context=ns['MIA_Charted_Context']
for name in context['selected']:
 if name in bpy.data.objects:bpy.data.objects[name].select_set(True)
if context['active']in bpy.data.objects:bpy.context.view_layer.objects.active=bpy.data.objects[context['active']]
if 'MIA_Charted_Camera'in ns:
 c=ns['MIA_Charted_Camera'];scene=bpy.context.scene;cam=scene.camera;cam.matrix_world=c['matrix']
 for key in ['type','ortho_scale','lens','clip_start','clip_end']:setattr(cam.data,key,c[key])
 for key in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y']:setattr(scene.render,key,c[key])
 for space,state in ns['MIA_Charted_Viewport']:
  space.region_3d.view_location=state['location'];space.region_3d.view_rotation=state['rotation'];space.region_3d.view_distance=state['distance'];space.region_3d.view_perspective=state['perspective']
  space.clip_start=state['clip_start'];space.clip_end=state['clip_end'];space.shading.type=state['shading_type'];space.shading.color_type=state['color_type'];space.shading.single_color=state['single_color']
assert np.array_equal(np.array([v.co[:]for v in source.data.vertices],np.float32),ns['MIA_Charted_Source_Raw'])
keys={k.name:hashlib.sha256(np.array([v.co[:]for v in k.data],np.float32).tobytes()).hexdigest()for k in source.data.shape_keys.key_blocks}
assert keys==ns['MIA_Charted_Source_Keys']
print(json.dumps(dict(status='CHARTED_PRIVATE_DESIGN_REMOVED_SOURCE_RESTORED',original_raw47_exact=True,native_saved=False)))
