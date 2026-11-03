"""Show the whole original-cage selection in live Blender, not a new native."""
from pathlib import Path
import hashlib
import json
import bpy
import numpy as np

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
CACHE=ROOT/'.mia-cache/body-connected'
NAME='MIA_ConnectedBody_Design'
source=bpy.data.objects['MIA_V27_SharedHeadBody']; ns=bpy.app.driver_namespace
assert NAME not in bpy.data.objects
assert bpy.context.mode=='OBJECT','Return the previous live edit bundle before installing the design cage'
ns['MIA_Connected_Context']=dict(selected=[o.name for o in bpy.context.selected_objects],
    active=bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None,
    mesh_select_mode=tuple(bpy.context.tool_settings.mesh_select_mode))
ns['MIA_Connected_Overlays']=[(area.spaces.active.overlay,area.spaces.active.overlay.show_overlays)
    for screen in bpy.data.screens for area in screen.areas if area.type=='VIEW_3D']
d=dict(np.load(CACHE/'scope.npz'))
assert len(source.data.vertices)==4647 and bpy.context.scene.frame_current==1
state={ob.name:dict(hide_render=ob.hide_render,hide_viewport=ob.hide_viewport,hidden=ob.hide_get())
       for ob in bpy.context.scene.objects if ob.name==source.name or ob.name.startswith('MIA_Review12_')}
original=np.array([p.co[:]for p in source.data.vertices],np.float32)
keys={k.name:hashlib.sha256(np.array([p.co[:]for p in k.data],np.float32).tobytes()).hexdigest() for k in source.data.shape_keys.key_blocks}
ob=source.copy();ob.data=source.data.copy();ob.name=NAME;ob.data.name=NAME+'_PrivateMesh'
assert ob.data.shape_keys is not source.data.shape_keys
ob.shape_key_clear();ob.animation_data_clear()
arm=[m for m in ob.modifiers if m.type=='ARMATURE'];assert len(arm)==1
ob.modifiers.remove(arm[0]);ob.data.vertices.foreach_set('co',d['q0_local'].astype(np.float32).ravel());ob.data.update()
bpy.context.scene.collection.objects.link(ob)
for old in list(bpy.context.selected_objects):old.select_set(False)
for name in state:
    bpy.data.objects[name].hide_render=True;bpy.data.objects[name].hide_set(True)
ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
gray=bpy.data.materials.new(NAME+'_Gray');gray.use_nodes=True
nodes=gray.node_tree.nodes;nodes.clear();bs=nodes.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(.23,.23,.23,1);bs.inputs['Roughness'].default_value=.85
out=nodes.new('ShaderNodeOutputMaterial');gray.node_tree.links.new(bs.outputs[0],out.inputs['Surface'])
ob.material_slots[1].link='OBJECT';ob.material_slots[1].material=gray
for p in ob.data.polygons:p.select=False
for e in ob.data.edges:e.select=False
mask=np.zeros(len(ob.data.vertices),bool);mask[d['selected']]=True
for p in ob.data.vertices:p.select=bool(mask[p.index])
bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.context.tool_settings.mesh_select_mode=(True,False,False)
ns['MIA_Connected_Scope_State']=state
ns['MIA_Connected_Source_Raw']=original
ns['MIA_Connected_Source_Key_SHA']=keys
ns['MIA_Connected_Baseline_Local']=d['q0_local'].astype(np.float32).copy()
ns['MIA_Connected_Gray']=gray.name
bpy.context.view_layer.update()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=True
bpy.ops.object.mode_set(mode='EDIT')
runtime='CPU_BACKGROUND' if bpy.app.background else 'LIVE_OFFICIAL_MCP'
report=dict(operation='Broad control selection only, no target deformation applied',runtime=runtime,
    object=ob.name,selected=int(mask.sum()),original47_untouched=True,static_design_no_keys_or_armature=True,
    production_migration=False,native_saved=False,ART=False)
directory=CACHE/('cpu' if bpy.app.background else 'live');directory.mkdir(exist_ok=True)
(directory/'scope-installed.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps(report))
