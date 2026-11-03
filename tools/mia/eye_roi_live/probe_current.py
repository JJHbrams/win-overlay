"""Read the bounded eye-ROI configuration in the current live Blender scene.

No file open/save, pose/key/property assignment, visibility, camera, material or
geometry mutation. The external standard MCP client stores stdout as evidence.
"""
from pathlib import Path
import hashlib
import json

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CORRECTIVE = 'Mia.v003.NeutralLowerLidBalance.1'
NAMES = [
    'MIA_Review12_H_LiveRepair', 'MIA_ConnectedBody_Design',
    'MIA_V27_Foundation_Face', 'MIA_V27_SharedHeadBody',
    'V28G_Sclera_-1', 'V28G_Sclera_1', 'V28G_Iris_-1', 'V28G_Iris_1',
    'V28G_InnerLid_-1', 'V28G_InnerLid_1',
    'V30_UpperLashes_-1', 'V30_UpperLashes_1',
    'V30_LowerLashes_-1', 'V30_LowerLashes_1',
    'V31_SourceBrow_-1', 'V31_SourceBrow_1',
    'MIA_V17_PIXAL_DetailedHair',
    'MiaHair_BrowInkProjection_-1', 'MiaHair_BrowInkProjection_1',
]


def sha_array(values):
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def coordinates(collection):
    data = np.empty(len(collection) * 3, np.float32)
    collection.foreach_get('co', data)
    return data.reshape(-1, 3)


def key_values():
    return {
        n: {k.name: float(k.value) for k in bpy.data.objects[n].data.shape_keys.key_blocks}
        for n in NAMES if n in bpy.data.objects and
        bpy.data.objects[n].type == 'MESH' and bpy.data.objects[n].data.shape_keys
    }


before = key_values()
scene = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
actors = {}
for name in NAMES:
    ob = bpy.data.objects.get(name)
    if ob is None:
        actors[name] = {'exists': False}
        continue
    row = dict(exists=True, type=ob.type, viewport_hidden=ob.hide_get(),
               hide_render=ob.hide_render, visible_get=ob.visible_get(),
               matrix_world=[list(r) for r in ob.matrix_world])
    if ob.type != 'MESH':
        actors[name] = row
        continue
    mesh = ob.data
    raw = coordinates(mesh.vertices)
    sk = mesh.shape_keys
    row.update(raw_vertices=len(mesh.vertices), polygons=len(mesh.polygons),
               raw_co_sha256=sha_array(raw), key_count=len(sk.key_blocks) if sk else 0,
               active_keys={k: v for k, v in before.get(name, {}).items() if abs(v) > 1e-9},
               lower_lid_corrective_present=bool(sk and CORRECTIVE in sk.key_blocks),
               material_slots=[m.name if m else None for m in mesh.materials],
               modifiers=[dict(name=m.name, type=m.type, show_viewport=m.show_viewport,
                               show_render=m.show_render,
                               target=getattr(getattr(m, 'object', None), 'name', None),
                               wrap_target=getattr(getattr(m, 'target', None), 'name', None))
                          for m in ob.modifiers])
    if sk:
        row['basis_co_sha256'] = sha_array(coordinates(sk.key_blocks[0].data))
        row['key_names_sha256'] = hashlib.sha256('\n'.join(k.name for k in sk.key_blocks).encode()).hexdigest()
        row['eye_corrective_names'] = [k.name for k in sk.key_blocks
                                       if 'v003' in k.name or 'Mia.' in k.name]
        row['eye_drivers'] = [dict(data_path=d.data_path, expression=d.driver.expression,
                                  variables=[dict(name=v.name, targets=[dict(
                                      owner=getattr(t.id, 'name', None), data_path=t.data_path)
                                      for t in v.targets]) for v in d.driver.variables])
                              for d in (sk.animation_data.drivers if sk.animation_data else [])
                              if any(s in d.data_path for s in ('EYE_', 'NeutralLowerLidBalance'))]
    row['UV'] = []
    for layer in mesh.uv_layers:
        uv = np.empty(len(layer.data) * 2, np.float32)
        layer.data.foreach_get('uv', uv)
        row['UV'].append(dict(name=layer.name, loops=len(layer.data), sha256=sha_array(uv),
                              active=layer == mesh.uv_layers.active, active_render=layer.active_render))
    ev = ob.evaluated_get(dg)
    em = ev.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
    q = coordinates(em.vertices)
    matrix = np.asarray(ev.matrix_world)
    world = q @ matrix[:3, :3].T + matrix[:3, 3]
    row['evaluated'] = dict(vertices=len(q), world_sha256=sha_array(world.astype(np.float32)),
                             bounds=[world.min(0).tolist(), world.max(0).tolist()] if len(q) else None)
    ev.to_mesh_clear()
    row['crease_material_signals'] = []
    for material in mesh.materials:
        if not material or not material.use_nodes:
            continue
        nodes = material.node_tree.nodes
        row['crease_material_signals'].append(dict(
            material=material.name,
            aligned_crease_nodes=[n.name for n in nodes if 'AlignedCrease' in n.name],
            old_fold_gain={n: float(nodes[n].outputs[0].default_value)
                           for n in ('V29_FoldGain', 'V30_FoldGain') if n in nodes},
            crease_metadata=material.get('Mia_v003_crease'),
            active_outputs=[n.name for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]))
    actors[name] = row

ctrl = bpy.data.objects.get('Mia_FacialControls_v002')
rig = bpy.data.objects.get('MIA_V06_RIG')
head = rig.pose.bones.get('J_Bip_C_Head') if rig and rig.pose else None
cam = scene.camera
frame = bpy.data.objects.get('MIA_v003_BrowInk_HeadFrame')
native = Path(bpy.data.filepath) if bpy.data.filepath else None
report = dict(
    scope='ACTUAL live read-only Stage A configuration; no source-registration or ART judgment',
    native=dict(path=str(native) if native else None,
                sha256=hashlib.sha256(native.read_bytes()).hexdigest() if native and native.is_file() else None),
    scene=scene.name, frame=scene.frame_current,
    active_object=getattr(bpy.context.view_layer.objects.active, 'name', None),
    actors=actors,
    controls={n: float(ctrl[n]) for n in ctrl.keys()
              if isinstance(ctrl[n], (int, float)) and
              (abs(float(ctrl[n])) > 1e-9 or n in ('HeadPitch','HeadYaw','HeadRoll','GazeX','GazeY'))} if ctrl else None,
    head_matrix_basis=[list(r) for r in head.matrix_basis] if head else None,
    partial_brow_strength=float(frame.get('Strength', 0)) if frame else None,
    camera=dict(name=cam.name, projection=cam.data.type, matrix=[list(r) for r in cam.matrix_world],
                ortho_scale=cam.data.ortho_scale, clip=[cam.data.clip_start, cam.data.clip_end],
                pixel_aspect=[scene.render.pixel_aspect_x, scene.render.pixel_aspect_y],
                resolution=[scene.render.resolution_x, scene.render.resolution_y],
                shift=[cam.data.shift_x, cam.data.shift_y]) if cam else None,
    key_values_unchanged=before == key_values(),
    mutation_performed=False, native_saved=False,
    limitation='Static D head has no facial deformation. Hidden original actors may evaluate keys; visibility is recorded separately.')
print(json.dumps(report, ensure_ascii=False))
