"""Show the explicit replacement region before changing a surface."""
from pathlib import Path
import json
import bpy
import numpy as np
ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
data=np.load(ROOT/'.mia-cache/face-live/rear-part01/ownership.npz')
ob=bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
if bpy.context.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.selected_objects:o.select_set(False)
ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
for v in ob.data.vertices:v.select=False
for e in ob.data.edges:e.select=False
for p in ob.data.polygons:p.select=False
for i in data['hidden_faces']:ob.data.polygons[int(i)].select=True
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.overlay.show_overlays=True
bpy.ops.object.mode_set(mode='EDIT')
print(json.dumps(dict(selected_faces=len(data['hidden_faces']),scope='Explicit replacement fin patch + previously traced U family',geometry_modified=False)))
