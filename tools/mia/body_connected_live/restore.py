"""Remove only this private design copy and restore borrowed visibility."""
import hashlib,json
import bpy,numpy as np
ns=bpy.app.driver_namespace
ob=bpy.data.objects['MIA_ConnectedBody_Design']
if ob.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
me=ob.data;bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me)
gray=bpy.data.materials.get(ns.get('MIA_Connected_Gray',''))
if gray and gray.users==0:bpy.data.materials.remove(gray)
for name,state in ns['MIA_Connected_Scope_State'].items():
    old=bpy.data.objects[name];old.hide_render=state['hide_render'];old.hide_viewport=state['hide_viewport'];old.hide_set(state['hidden'])
for overlay,visible in ns['MIA_Connected_Overlays']:overlay.show_overlays=visible
context=ns['MIA_Connected_Context']
for old in list(bpy.context.selected_objects):old.select_set(False)
for name in context['selected']:
    if name in bpy.context.view_layer.objects:bpy.data.objects[name].select_set(True)
if context['active'] in bpy.context.view_layer.objects:bpy.context.view_layer.objects.active=bpy.data.objects[context['active']]
bpy.context.tool_settings.mesh_select_mode=context['mesh_select_mode']
if 'MIA_Connected_Camera' in ns:
    c=ns['MIA_Connected_Camera'];scene=bpy.context.scene;cam=scene.camera;cam.matrix_world=c['matrix']
    for key in ['type','ortho_scale','lens','clip_start','clip_end']:setattr(cam.data,key,c[key])
    for key in ['resolution_x','resolution_y','resolution_percentage','pixel_aspect_x','pixel_aspect_y']:setattr(scene.render,key,c[key])
    for space,state in ns['MIA_Connected_Viewport']:
        space.region_3d.view_location=state['location'];space.region_3d.view_rotation=state['rotation'];space.region_3d.view_distance=state['distance'];space.region_3d.view_perspective=state['perspective']
        space.clip_start=state['clip_start'];space.clip_end=state['clip_end'];space.shading.type=state['shading_type'];space.shading.color_type=state['color_type'];space.shading.single_color=state['single_color']
source=bpy.data.objects['MIA_V27_SharedHeadBody']
assert np.array_equal(np.array([p.co[:]for p in source.data.vertices],np.float32),ns['MIA_Connected_Source_Raw'])
for k in source.data.shape_keys.key_blocks:
    assert hashlib.sha256(np.array([p.co[:]for p in k.data],np.float32).tobytes()).hexdigest()==ns['MIA_Connected_Source_Key_SHA'][k.name]
print(json.dumps(dict(status='CONNECTED_PRIVATE_DESIGN_REMOVED_ORIGINAL_RESTORED',original47_exact=True,native_saved=False)))
