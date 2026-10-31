"""Replace only the owned hair collection; preserve the already painted face and anatomy."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path
import bpy
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--face-native', required=True)
p.add_argument('--face-sha')
p.add_argument('--hair-native', required=True)
p.add_argument('--hair-sha', required=True)
p.add_argument('--output-dir', required=True)
p.add_argument('--main-object-only', action='store_true')
p.add_argument('--native-name')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
face, hair, out = Path(a.face_native).resolve(), Path(a.hair_native).resolve(), Path(a.output_dir).resolve()
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
source_hashes = {str(f): sha(f) for f in [face, hair]}
assert source_hashes[str(hair)] == a.hair_sha.lower(), 'Hair candidate changed'
assert not a.face_sha or source_hashes[str(face)] == a.face_sha.lower(), 'Face candidate changed'
out.mkdir(parents=True, exist_ok=True)
native_name = a.native_name or ('Mia_HeadHair_v17d.blend' if a.main_object_only else 'Mia_HeadHair_v17c.blend')
assert Path(native_name).name == native_name and native_name.endswith('.blend'), 'Output must be a native filename'
native = out / native_name
assert not native.exists(), 'Refusing to overwrite existing native'
bpy.ops.wm.open_mainfile(filepath=str(face))
name = 'MIA_V17_PIXAL_HAIR'
old = bpy.data.collections[name]
old_objects = {bpy.data.objects['MIA_V17_PIXAL_DetailedHair']} if a.main_object_only else set(old.all_objects)

def mesh_hash(o):
    h = hashlib.sha256()
    for v in o.data.vertices:
        h.update(struct.pack('<3f', *v.co))
        for g in v.groups:
            h.update(struct.pack('<IIf', v.index, g.group, g.weight))
    for po in o.data.polygons:
        h.update(struct.pack('<I', len(po.vertices)))
        for v in po.vertices:
            h.update(struct.pack('<I', v))
    for uv in o.data.uv_layers:
        h.update(uv.name.encode())
        for v in uv.data:
            h.update(struct.pack('<2f', *v.uv))
    if o.data.shape_keys:
        for k in o.data.shape_keys.key_blocks:
            h.update(k.name.encode())
            h.update(struct.pack('<f', k.value))
            for v in k.data:
                h.update(struct.pack('<3f', *v.co))
    for slot in o.material_slots:
        h.update((slot.material.name if slot.material else '').encode())
    return h.hexdigest()

protected = {o.name: mesh_hash(o) for o in bpy.context.scene.objects
             if o.type == 'MESH' and o not in old_objects}
removed = sorted(o.name for o in old_objects)
assert all(set(o.users_collection) <= {old} for o in old_objects), 'Hair object has another owner'
for o in old_objects:
    bpy.data.objects.remove(o, do_unlink=True)
if a.main_object_only:
    with bpy.data.libraries.load(str(hair), link=False) as (available, requested):
        requested.objects = ['MIA_V17_PIXAL_DetailedHair']
    old.objects.link(requested.objects[0])
    new = old
else:
    bpy.data.collections.remove(old)
    with bpy.data.libraries.load(str(hair), link=False) as (available, requested):
        assert name in available.collections
        requested.collections = [name]
    new = requested.collections[0]
    bpy.context.scene.collection.children.link(new)
new.hide_render = False
new.hide_viewport = False
for o in new.all_objects:
    o.hide_render = False
    o.hide_viewport = False
    o.hide_set(False)
after = {n: mesh_hash(bpy.data.objects[n]) for n in protected}
assert protected == after, 'Protected face/body/UV/key/weight/material ownership changed'
scene = bpy.context.scene
cam = scene.camera
cam.location = (0, -2, 1.555)
cam.rotation_euler = (Vector((0, 0, 1.555)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
cam.data.ortho_scale = .48
scene['mia_v17_status'] = 'Reference refinement candidate; independent art review required. No final hair physics or motion approval.'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(native), relative_remap=False)
assert all(sha(Path(f)) == digest for f, digest in source_hashes.items())
report = {'native': str(native), 'native_sha256': sha(native), 'source_hashes': source_hashes,
          'recipe_sha256': sha(Path(__file__)), 'protected_meshes': protected,
          'protected_meshes_unchanged': protected == after, 'removed_hair_owners': removed,
          'new_hair_owners': sorted(o.name for o in new.all_objects),
          'scope': ('Only the main Pixal hair object replaced with the new UV/material candidate. All other hair/face/body objects preserved.'
                    if a.main_object_only else 'Only the hair collection replaced. No face/body/key/weight/UV edits; camera framing set for inspection.')}
(out / 'integration-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('INTEGRATED_HAIR_ONLY', report['native_sha256'])
