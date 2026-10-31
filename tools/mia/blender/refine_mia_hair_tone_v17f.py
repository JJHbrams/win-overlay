"""Reference-calibrated warm ash-gray tone; keep actual UV texture and geometry."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import bpy
import struct
from mathutils import Vector

p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--output-dir', required=True)
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out = Path(a.source).resolve(), Path(a.output_dir).resolve()
out.mkdir(parents=True, exist_ok=True)
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
source_hash = sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source))
scene, cam = bpy.context.scene, bpy.context.scene.camera
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100

def render(name, xy):
    cam.location = (xy[0], xy[1], 1.46)
    cam.rotation_euler = (Vector((0, 0, 1.46)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = .64
    scene.render.filepath = str(out / (name + '.png'))
    bpy.ops.render.render(write_still=True)

views = [('front', (0, -2)), ('profile', (2, 0)), ('back', (0, 2))]
for name, xy in views:
    render('before_' + name, xy)
hair = bpy.data.objects['MIA_V17_PIXAL_DetailedHair']
original = hair.material_slots[0].material
# Freeze geometry/UV/key and all non-hair material assignments.
hairnames={o.name for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].all_objects}
def scope():
    result={}
    for o in bpy.data.objects:
        if o.type!='MESH':continue
        data=b''.join(struct.pack('<3f',*v.co) for v in o.data.vertices)+b''.join(struct.pack('<2f',*v.uv) for l in o.data.uv_layers for v in l.data)
        if o.data.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in o.data.shape_keys.key_blocks for v in k.data)
        result[o.name]=hashlib.sha256(data).hexdigest()
    return result
protected=scope();nonhair_slots={o.name:[s.material.name if s.material else None for s in o.material_slots] for o in bpy.data.objects if o.type=='MESH' and o.name not in hairnames};packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
material = original.copy()
material.name = 'MIA_V17_ReferenceAshGray_PaintUV'
nodes, links = material.node_tree.nodes, material.node_tree.links
bw = next(n for n in nodes if n.type == 'RGBTOBW')
mix = next(n for n in nodes if n.type == 'MIX_RGB')
tone = nodes.new('ShaderNodeValToRGB')
tone.name = 'MIA_V17_REFERENCE_ASH_TONE'
tone.color_ramp.interpolation = 'LINEAR'
stops = [(0, (.008, .007, .007, 1)),
         (.010, (.080, .065, .062, 1)),
         (.030, (.235, .193, .189, 1)),
         (.050, (.340, .280, .274, 1)),
         (.100, (.390, .330, .325, 1))]
stops=[(pos,tuple(v*.65 for v in color[:3])+(1,)) for pos,color in stops]
for i, (pos, color) in enumerate(stops):
    element = tone.color_ramp.elements[i] if i < 2 else tone.color_ramp.elements.new(pos)
    element.position, element.color = pos, color
links.new(bw.outputs[0], tone.inputs[0])
links.new(tone.outputs[0], mix.inputs[1])
hair.material_slots[0].material = material
haircol = bpy.data.collections['MIA_V17_PIXAL_HAIR']
changed_materials = {original.name: material.name}
copies = {}
for obj in haircol.all_objects:
    if obj == hair:
        continue
    for slot in obj.material_slots:
        old = slot.material
        if not old or not old.use_nodes:
            continue
        strand = old.node_tree.nodes.get('OWNED_STRAND_RAMP')
        if not strand:
            continue
        if old.name not in copies:
            new = old.copy()
            new.name = old.name + '_ReferenceAsh'
            ramp = new.node_tree.nodes['OWNED_STRAND_RAMP'].color_ramp
            ramp.elements[0].color = (.11375, .091, .08905, 1)
            ramp.elements[-1].color = (.15925, .1313, .1274, 1)
            copies[old.name] = new
            changed_materials[old.name] = new.name
        slot.material = copies[old.name]
assert scope()==protected
assert all([s.material.name if s.material else None for s in bpy.data.objects[n].material_slots]==v for n,v in nonhair_slots.items())
cam.location = (0, -2, 1.46)
cam.rotation_euler = (Vector((0, 0, 1.46)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
native = out / 'Mia_HairTone_v17f.blend'
assert not native.exists(), 'Do not overwrite an earlier candidate'
for image in bpy.data.images:
    if image.packed_file:image.use_fake_user=True
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(native), relative_remap=False)
bpy.ops.wm.open_mainfile(filepath=str(native))
scene,cam=bpy.context.scene,bpy.context.scene.camera
assert scope()==protected
assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
for name,xy in views:render('after_'+name,xy)
assert source_hash == sha(source)
(out / 'tone-manifest.json').write_text(json.dumps({
    'source': str(source), 'source_sha256': source_hash, 'native': str(native),
    'native_sha256': sha(native), 'recipe_sha256': sha(Path(__file__)),
    'unchanged_geometry_uv_key_meshes':len(protected),'unchanged_nonhair_material_owners':len(nonhair_slots),'packed_images_byte_exact':len(packed),'changed_materials': changed_materials, 'tone_stops_linear': stops,
    'scope': 'Hair material response only. No geometry/UV/rig/face/body changes. Normal multiplier retained.',
    'calibration': 'Root bright tone RGB151,137,135 was too light; this candidate scales its linear palette by.65 toward portrait122,111,110. Source dark85,85,85. Different viewpoints make this a directional color guide, not a global likeness metric.'
}, indent=2), encoding='utf-8')
print('TONE_NATIVE', sha(native))
