"""Read-only CPU diagnostic; baseline is supplied to Blender on its command line."""
import bpy
import json

obj = bpy.data.objects['MIA_V27_SharedHeadBody']
print('POSE_SPACE_BASELINE ' + json.dumps({
    'version': bpy.app.version_string,
    'frame': bpy.context.scene.frame_current,
    'object_count': len(bpy.data.objects),
    'owner': obj.name,
    'vertices': len(obj.data.vertices),
    'keys': len(obj.data.shape_keys.key_blocks),
    'matrix_world': [list(row) for row in obj.matrix_world],
    'modifiers': [{'name': m.name, 'type': m.type, 'viewport': m.show_viewport,
        **({k: getattr(m, k) for k in ['use_deform_preserve_volume', 'use_vertex_groups',
              'use_bone_envelopes', 'use_multi_modifier']} if m.type == 'ARMATURE' else {})}
        for m in obj.modifiers],
    'active_keys': {k.name: k.value for k in obj.data.shape_keys.key_blocks if k.value},
}, sort_keys=True))
