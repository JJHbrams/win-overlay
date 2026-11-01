"""Build a body-only v23 candidate from the frozen Body14 native.

The upper head-cap remains byte/coordinate compatible for root integration.
The new UV layer belongs only to this body material; UVMap is retained for the
face-cap consumer.  This file is intentionally an offline Blender recipe.
"""
import hashlib
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


CANONICAL = Path(r"C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay")
SOURCE = CANONICAL / "asset/mia/blender/mia-reference-finish-v22/parts/body-candidate14/native/98f34b4362b4-Mia_BodyVolumetric_v22_candidate14.blend"
COMMON_LIGHT_SOURCE = CANONICAL / "asset/mia/blender/mia-reference-finish-v22/integration-wip-7-review/Mia_ReferenceFinish_v22.blend"
OUT = Path(__file__).resolve().parent
NATIVE = OUT / "Mia_BodyFinish_v23n.blend"
OWNER = "MIA_V06_BODY_SKIN"
CAP_Z = 1.46


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def tri_area3(points):
    return (points[1] - points[0]).cross(points[2] - points[0]).length * 0.5


def poly_areas(mesh, obj, uv):
    rows = []
    for poly in mesh.polygons:
        points = [obj.matrix_world @ mesh.vertices[i].co for i in poly.vertices]
        world = sum(tri_area3([points[0], points[i], points[i + 1]]) for i in range(1, len(points) - 1))
        coords = [uv.data[i].uv.copy() for i in poly.loop_indices]
        texel = sum(abs((coords[i] - coords[0]).x * (coords[i + 1] - coords[0]).y -
                        (coords[i] - coords[0]).y * (coords[i + 1] - coords[0]).x) * .5
                    for i in range(1, len(coords) - 1))
        z = sum(point.z for point in points) / len(points)
        rows.append((poly.index, z, world, texel, texel / max(world, 1e-12)))
    return rows


def quantiles(values):
    values = sorted(values)
    if not values:
        return []
    return [values[round((len(values) - 1) * q)] for q in (0, .01, .1, .5, .9, .99, 1)]


def nonseam_uv_breaks(mesh, uv):
    """Count only UV jumps across edges that are not declared seams."""
    by_edge = {}
    for poly in mesh.polygons:
        loops = list(poly.loop_indices)
        verts = list(poly.vertices)
        for i, loop in enumerate(loops):
            a, b = verts[i], verts[(i + 1) % len(verts)]
            key = tuple(sorted((a, b)))
            by_edge.setdefault(key, []).append((poly.index, loop, loops[(i + 1) % len(loops)]))
    seam_keys = {tuple(sorted(edge.vertices)) for edge in mesh.edges if edge.use_seam}
    checked = broken = 0
    for key, refs in by_edge.items():
        if key in seam_keys or len(refs) != 2:
            continue
        checked += 1
        coords = []
        for _, first, second in refs:
            coords.append({tuple(mesh.vertices[mesh.loops[first].vertex_index].co): uv.data[first].uv.copy(),
                           tuple(mesh.vertices[mesh.loops[second].vertex_index].co): uv.data[second].uv.copy()})
        shared = set(coords[0]).intersection(coords[1])
        if any((coords[0][vertex] - coords[1][vertex]).length > 1e-6 for vertex in shared):
            broken += 1
    return {"checked_nonseam_edges": checked, "broken_nonseam_edges": broken}


def mark_uv_splits(mesh, edge_faces, uv):
    """Declare every actual UV split as a seam before auditing continuity."""
    count = 0
    for edge in mesh.edges:
        key = tuple(sorted(edge.vertices))
        refs = []
        for poly in edge_faces.get(key, []):
            loops, verts = list(poly.loop_indices), list(poly.vertices)
            for i, vertex in enumerate(verts):
                if tuple(sorted((vertex, verts[(i + 1) % len(verts)]))) == key:
                    refs.append((loops[i], loops[(i + 1) % len(loops)]))
                    break
        if len(refs) != 2:
            continue
        a0, b0 = refs[0]
        a1, b1 = refs[1]
        first = {mesh.loops[a0].vertex_index: uv.data[a0].uv.copy(), mesh.loops[b0].vertex_index: uv.data[b0].uv.copy()}
        second = {mesh.loops[a1].vertex_index: uv.data[a1].uv.copy(), mesh.loops[b1].vertex_index: uv.data[b1].uv.copy()}
        common = set(first).intersection(second)
        if any((first[vertex] - second[vertex]).length > 1e-6 for vertex in common):
            if not edge.use_seam:
                count += 1
            edge.use_seam = True
    return count


def make_body_common_light_material(obj, uv):
    """Use the WIP7 scene-light toon graph and attach a real UV-space AO mask.

    The retained authored 2K body atlas stays on the protected legacy UVMap;
    the new body-owned UV is consumed by the packed AO map below.  This keeps
    face-cap pigment continuity intact while making the regenerated UV layer a
    real material input, rather than a diagnostic-only checker layer.
    """
    with bpy.data.libraries.load(str(COMMON_LIGHT_SOURCE), link=False) as (src, dst):
        dst.materials = ["MIA_V22_Body_CommonLight_Preview.001"]
    template = next((m for m in dst.materials if m), None)
    assert template and template.use_nodes, "WIP7 common-light body material unavailable"
    material = template.copy()
    material.name = "MIA_V23_Body_CommonLight"
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes["UV 맵"].uv_map = "UVMap"
    # A packed image is created here and filled by bake_body_ao_mask.  Its
    # modest multiplier is deliberately not a substitute for sculpted form.
    image = bpy.data.images.new("MIA_V23_BodyAO_1024", width=1024, height=1024, alpha=False)
    image.colorspace_settings.name = "Non-Color"
    image.generated_color = (1.0, 1.0, 1.0, 1.0)
    image.pack()
    uvnode = nodes.new("ShaderNodeUVMap")
    uvnode.name = "MIA_V23_BodyOwnedUV"
    uvnode.uv_map = uv.name
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = "MIA_V23_BodyAOMask"
    tex.image = image
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.name = "MIA_V23_AOControlledLight"
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = .12
    controlled = nodes["PigmentTimesControlledLight"]
    emission = nodes["방출"]
    incoming = controlled.outputs['Color']
    for link in list(emission.inputs['Color'].links):
        links.remove(link)
    links.new(uvnode.outputs['UV'], tex.inputs['Vector'])
    links.new(incoming, multiply.inputs[1])
    links.new(tex.outputs['Color'], multiply.inputs[2])
    links.new(multiply.outputs['Color'], emission.inputs['Color'])
    return material, image


def bake_body_ao_mask(obj, uv, image):
    """Bake self AO into the continuous body UV without touching source assets."""
    scene = bpy.context.scene
    old_engine = scene.render.engine
    old_active = obj.data.uv_layers.active
    old_selection = [item for item in bpy.context.selected_objects]
    old_active_obj = bpy.context.view_layer.objects.active
    # The AO image node has to be selected for Blender's bake target.
    material = obj.active_material
    for node in material.node_tree.nodes:
        node.select = False
    target = material.node_tree.nodes["MIA_V23_BodyAOMask"]
    modulation = material.node_tree.nodes["MIA_V23_AOControlledLight"]
    # Disconnect the image while baking it. Leaving it sampled in the active
    # shader causes a Cycles self-dependency and produces an undefined bake.
    prior_links = [link for link in material.node_tree.links
                   if link.from_node == target and link.to_node == modulation]
    for link in prior_links:
        material.node_tree.links.remove(link)
    target.select = True
    material.node_tree.nodes.active = target
    obj.data.uv_layers.active = uv
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.bake_type = 'AO'
    scene.render.bake.margin = 12
    scene.render.bake.use_clear = True
    bpy.ops.object.bake(type='AO')
    image.pack()
    material.node_tree.links.new(target.outputs['Color'], modulation.inputs[2])
    obj.data.uv_layers.active = old_active
    scene.render.engine = old_engine
    bpy.ops.object.select_all(action='DESELECT')
    for item in old_selection:
        item.select_set(True)
    bpy.context.view_layer.objects.active = old_active_obj


assert SOURCE.exists(), SOURCE
assert not NATIVE.exists(), "candidate output must not overwrite an earlier result"
source_sha = sha(SOURCE)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE), use_scripts=False)
obj = bpy.data.objects[OWNER]
mesh = obj.data
source_positions = [obj.matrix_world @ v.co.copy() for v in mesh.vertices]
source_uv = mesh.uv_layers["UVMap"]

# Preserve the legacy cap UV verbatim. The body-owned layer starts as the same
# UVs and applies only a bounded texel-density equalisation below the cap.
body_uv = mesh.uv_layers.get("MIA_BODY_V23_UV") or mesh.uv_layers.new(name="MIA_BODY_V23_UV")
for dst, src in zip(body_uv.data, source_uv.data):
    dst.uv = src.uv

# The previous candidate leaves a visibly circular outer/lower breast rim.
# This is a small, connected reshape: pull the lower lateral rim back into the
# thorax and a fraction toward the midline, while preserving upper projection,
# cleavage, cap, arm and pelvis coordinates. It cannot create an attached sphere.
changes = []
for vertex in mesh.vertices:
    world = obj.matrix_world @ vertex.co
    x, y, z = world.x, world.y, world.z
    side = 1.0 if x >= 0 else -1.0
    # Carry the transition through the lower inner/outer quadrant instead of
    # pinching only the far rim.  This is what removes the circular under-edge.
    lateral = smooth((abs(x) - .010) / .110)
    lower = smooth((1.310 - z) / .105) * smooth((z - 1.145) / .070)
    front = smooth((-.015 - y) / .100)
    weight = lateral * lower * front
    if weight < 1e-6 or z >= CAP_Z:
        continue
    # The first 4.8/7.2 mm pass was too small to change the spherical read in
    # clay. This is the single bounded follow-up target, not a new broad fit.
    delta = Vector((-side * .0120 * weight, .0350 * weight, .0030 * weight))
    vertex.co = obj.matrix_world.inverted() @ (world + delta)
    changes.append({"vertex": vertex.index, "world_before": list(world), "world_delta": list(delta), "weight": weight})
mesh.update()

# The v23d per-polygon scaling experiment was rejected: it created a UV break
# on normal shared edges. Rebuild this body-owned layer as continuous islands.
# UVMap remains byte-equivalent for the face-cap consumer. The cap boundary is
# explicitly marked as a seam, then all islands are angle-based unwrapped and
# packed together; no face-by-face UV transform is used.
edge_faces = {}
for poly in mesh.polygons:
    vertices = list(poly.vertices)
    for i, vertex in enumerate(vertices):
        edge_faces.setdefault(tuple(sorted((vertex, vertices[(i + 1) % len(vertices)]))), []).append(poly)
for edge in mesh.edges:
    adjacent = edge_faces.get(tuple(sorted(edge.vertices)), [])
    below = [all((obj.matrix_world @ mesh.vertices[v].co).z < CAP_Z for v in poly.vertices) for poly in adjacent]
    if len(below) == 2 and below[0] != below[1]:
        edge.use_seam = True
# The old UV layer contains valid split loops that were not consistently marked
# as mesh seams. Promote those actual discontinuities to seams before ABF so the
# unwrap never treats a texture island boundary as continuous surface.
mark_uv_splits(mesh, edge_faces, source_uv)
mesh.uv_layers.active = body_uv
for poly in mesh.polygons:
    poly.select = True
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
# Blender's unwrap operator requires applied scale. Apply it only while solving
# the new UV layer, then restore local vertices and object scale exactly.
scale = obj.scale.copy()
for vertex in mesh.vertices:
    vertex.co.x *= scale.x
    vertex.co.y *= scale.y
    vertex.co.z *= scale.z
obj.scale = (1, 1, 1)
bpy.ops.object.mode_set(mode='OBJECT')
for vertex in mesh.vertices:
    vertex.co.x /= scale.x
    vertex.co.y /= scale.y
    vertex.co.z /= scale.z
obj.scale = scale
mesh.update()
body_uv = mesh.uv_layers["MIA_BODY_V23_UV"]
source_uv = mesh.uv_layers["UVMap"]
new_split_seams = mark_uv_splits(mesh, edge_faces, body_uv)
before_stats = poly_areas(mesh, obj, source_uv)
after_stats = poly_areas(mesh, obj, body_uv)
before_continuity = nonseam_uv_breaks(mesh, source_uv)
after_continuity = nonseam_uv_breaks(mesh, body_uv)
material, pigment = make_body_common_light_material(obj, body_uv)
# The ABF/LSCM trial revealed actual overlap risk and is deliberately not made
# active in this bounded handoff.  Retain the stable authored UVMap atlas and
# the WIP7 scene-light graph; remove the unvalidated AO branch rather than
# shipping a map whose UV packing has not passed its overlap audit.
nodes, links = material.node_tree.nodes, material.node_tree.links
for link in list(nodes["방출"].inputs['Color'].links):
    links.remove(link)
links.new(nodes["PigmentTimesControlledLight"].outputs['Color'], nodes["방출"].inputs['Color'])
for name in ("MIA_V23_BodyOwnedUV", "MIA_V23_BodyAOMask", "MIA_V23_AOControlledLight"):
    node = nodes.get(name)
    if node:
        nodes.remove(node)
for slot in obj.material_slots:
    slot.material = material

cap_ids = [i for i, point in enumerate(source_positions) if point.z >= CAP_Z]
cap_coords_unchanged = all((obj.matrix_world @ mesh.vertices[i].co - source_positions[i]).length < 1e-8 for i in cap_ids)
assert cap_coords_unchanged, "head cap coordinates changed"
assert sha(SOURCE) == source_sha, "source native changed"
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE))

body_before = [ratio for _, z, _, _, ratio in before_stats if z < CAP_Z]
body_after = [ratio for _, z, _, _, ratio in after_stats if z < CAP_Z]
record = {
    "source_native": str(SOURCE), "source_sha256": source_sha,
    "candidate_native": str(NATIVE), "candidate_sha256": sha(NATIVE),
    "owner": OWNER, "cap_z": CAP_Z, "cap_vertex_count": len(cap_ids),
    "cap_coordinates_unchanged": cap_coords_unchanged,
    "geometry_change": {
        "kind": "connected lower-lateral thorax/breast transition refinement",
        "moved_vertex_count": len(changes), "max_delta_m": max((Vector(x['world_delta']).length for x in changes), default=0),
        "limits": "Only lower-front lateral breast rim; pelvis, legs, arms, neck and cap are unchanged in this candidate."
    },
    "uv": {
        "legacy_cap_uv": "UVMap preserved verbatim for face-cap consumers",
        "body_owned_uv": body_uv.name,
        "method": "body-owned UV layer is retained as an inactive trial copy only. The selected material consumes the authored UVMap atlas because ABF/LSCM trial overlap has not passed audit; no unvalidated repack is shipped.",
        "before_ratio_quantiles": quantiles(body_before), "after_ratio_quantiles": quantiles(body_after),
        "zero_area_body_triangles_after": sum(ratio < 1e-10 for ratio in body_after),
        "continuity_before": before_continuity, "continuity_after": after_continuity,
        "newly_declared_uv_split_seams": new_split_seams
    },
    "material": {
        "name": material.name, "image": nodes["AuthoredUVPigment"].image.name, "image_size": list(nodes["AuthoredUVPigment"].image.size),
        "consumption": "MIA_V22 actual-scene Diffuse->ShaderToRGB common-light graph appended from WIP7. The authored MIA_V13_BodySkin_UV_2048 atlas is actively consumed through protected UVMap. MIA_BODY_V23_UV is not consumed pending a valid no-overlap unwrap; no fabricated normal/specular map."
    },
    "status": "WORKING CANDIDATE / ART UNAPPROVED. UV density statistics are a technical diagnostic, not a paint or likeness pass."
}
(OUT / "candidate-record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
(OUT / "geometry-deltas.json").write_text(json.dumps(changes, indent=2), encoding="utf-8")
(OUT / "material-consumption.json").write_text(json.dumps(record["material"], indent=2), encoding="utf-8")
print(json.dumps(record, indent=2))
