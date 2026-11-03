"""Isolate backing versus outer-lock intersection without editing either mesh."""
import json
import bpy
show=globals().get('MIA_EDIT_PHASE','select')=='apply'
state=bpy.app.driver_namespace['MIA_CurvedRear03Base']
names=[]
for ob in state['objects']:
    if ob.name.endswith('_RemainingMain'):continue
    ob.hide_set(not show);ob.hide_render=not show;names.append(ob.name)
bpy.context.view_layer.update()
print(json.dumps(dict(outer_parts_visible=show,count=len(names),geometry_modified=False)))
