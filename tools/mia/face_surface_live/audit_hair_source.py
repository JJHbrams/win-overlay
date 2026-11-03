"""Read-only R3b hair/head inventory for a later bounded live-MCP operation.

Run in factory-startup background Blender. No render, native save or live use.
Raw coordinates are an analysis cache, not a new adopted model.
"""
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np

sys.dont_write_bytecode = True
ROOT = Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT = ROOT/'.mia-cache/face-live/source-audit'
SOURCE_SHA = '4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1'


def ah(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def main():
    source = Path(bpy.data.filepath)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA
    assert not OUT.exists(), 'Never overwrite an audit'
    OUT.mkdir(parents=True)
    deps = bpy.context.evaluated_depsgraph_get()
    arrays = {}
    records = []
    for ob in bpy.data.objects:
        if not (ob.name in ('MIA_V17_PIXAL_DetailedHair', 'MIA_V27_SharedHeadBody',
                           'MIA_V27_Foundation_Face', 'Armature') or
                any(token in ob.name for token in ('V31_SourceBrow', 'Gather', 'Crown', 'HalfUp', 'BrowInk'))):
            continue
        record = dict(name=ob.name, type=ob.type, parent=ob.parent.name if ob.parent else None,
                      hidden=ob.hide_get(), hide_render=ob.hide_render,
                      matrix_world=list(map(list, ob.matrix_world)),
                      custom_properties={k: str(ob[k]) for k in ob.keys()},
                      modifiers=[dict(name=m.name, type=m.type,
                                      visible=m.show_viewport, render=m.show_render,
                                      group=getattr(getattr(m, 'node_group', None), 'name', None))
                                 for m in ob.modifiers])
        if ob.type == 'MESH':
            record['raw_vertices'] = len(ob.data.vertices)
            record['raw_faces'] = len(ob.data.polygons)
            record['keys'] = [dict(name=k.name, value=k.value, mute=k.mute)
                              for k in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else []
            record['attributes'] = [dict(name=a.name, domain=a.domain, type=a.data_type)
                                    for a in ob.data.attributes]
            record['UV'] = [a.name for a in ob.data.uv_layers]
            record['materials'] = [ma.name if ma else None for ma in ob.data.materials]
            ev = ob.evaluated_get(deps)
            me = ev.to_mesh(preserve_all_data_layers=True, depsgraph=deps)
            world = np.array([ev.matrix_world @ v.co for v in me.vertices], dtype=np.float32)
            record['world_bounds'] = [world.min(0).tolist(), world.max(0).tolist()]
            record['evaluated_vertices'] = len(world)
            if ob.name == 'MIA_V17_PIXAL_DetailedHair':
                assert all(len(p.vertices) == 3 for p in me.polygons)
                arrays['main_world'] = world
                arrays['main_local'] = np.array([v.co[:] for v in me.vertices], np.float32)
                arrays['main_raw'] = np.array([v.co[:] for v in ob.data.vertices], np.float32)
                arrays['main_triangles'] = np.array([p.vertices[:] for p in me.polygons], np.int32)
                arrays['main_material_index'] = np.array([p.material_index for p in me.polygons], np.int32)
                record['raw_co_sha256'] = ah(arrays['main_raw'])
                record['triangles_sha256'] = ah(arrays['main_triangles'])
                record['groups'] = [dict(name=g.name, index=g.index) for g in ob.vertex_groups]
                for group in ob.vertex_groups:
                    if any(x in group.name.lower() for x in ('fringe', 'root', 'head')):
                        weights = np.zeros(len(ob.data.vertices), np.float32)
                        for v in ob.data.vertices:
                            for g in v.groups:
                                if g.group == group.index:
                                    weights[v.index] = g.weight
                        arrays['main_weight_'+group.name] = weights
            elif 'V31_SourceBrow' in ob.name:
                arrays[ob.name+'_world'] = world
            ev.to_mesh_clear()
        records.append(record)
    np.savez_compressed(OUT/'analysis.npz', **arrays)
    assert (OUT/'analysis.npz').stat().st_size < 20*1024**2
    report = dict(source=str(source), source_sha256=SOURCE_SHA, objects=records,
                  scene=bpy.context.scene.name, frame=bpy.context.scene.frame_current,
                  arrays_sha256=hashlib.sha256((OUT/'analysis.npz').read_bytes()).hexdigest(),
                  written_bytes=(OUT/'analysis.npz').stat().st_size,
                  original_data_modified=False, native_saved=False, GPU_used=False, ART=False)
    (OUT/'inventory.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(status='READONLY_SOURCE_AUDIT', objects=len(records),
                          bytes=report['written_bytes'], output=str(OUT))), flush=True)


if __name__ == '__main__':
    main()
