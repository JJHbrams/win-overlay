"""Read-only projection of actual iris owners in the frozen review cameras."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--native', required=True)
p.add_argument('--owner', required=True)
p.add_argument('--output', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
native = Path(a.native)
before = hashlib.sha256(native.read_bytes()).hexdigest()
deps = Path(__file__).resolve().parents[1] / 'face-feedback-7/surface-diagnosis/dependencies'
sys.path.insert(0, str(deps))
import review_setup as review
bpy.ops.wm.open_mainfile(filepath=str(native), use_scripts=False)
s = bpy.context.scene
s.frame_set(1)
o = bpy.data.objects[a.owner]
for ob in s.objects:
    if ob.type == 'MESH' and ob.data.shape_keys:
        for k in ob.data.shape_keys.key_blocks:
            k.value = 0
o.hide_viewport = False
o.hide_set(False)
bpy.context.view_layer.update()
ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = ev.to_mesh()
ids = {i for poly in mesh.polygons if poly.material_index == 5 for i in poly.vertices}
world = [ev.matrix_world @ mesh.vertices[i].co for i in ids]
centers = []
for sign in [-1, 1]:
    pts = [v for v in world if v.x * sign > 0]
    centers.append(sum(pts, Vector()) / len(pts))
ev.to_mesh_clear()
records = []
for view in review.VIEWS:
    review.camera(s, view)
    s.render.resolution_percentage = 70
    bpy.context.view_layer.update()
    w = int(s.render.resolution_x * .7)
    h = int(s.render.resolution_y * .7)
    screen = [world_to_camera_view(s, s.camera, c) for c in centers]
    records.append({'view':view, 'size':[w,h], 'points':[[v.x*w,(1-v.y)*h] for v in screen],
                    'camera':review.record(s,view,'iris-center-projection')})
after = hashlib.sha256(native.read_bytes()).hexdigest()
assert before == after
Path(a.output).write_text(json.dumps({'native':str(native),'sha256':before,'owner':a.owner,
    'method':'Centroid of actual evaluated slot-5 iris vertices per world-X side; approximate pupil anchor, not measured iris diameter or gaze.',
    'native_unchanged':True,'world_centers':[list(c) for c in centers],'records':records},indent=2),encoding='utf-8')
print('IRIS_PROJECTION_COMPLETE')
