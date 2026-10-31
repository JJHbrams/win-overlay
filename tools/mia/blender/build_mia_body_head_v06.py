"""Build and audit the Mia v06 body/head foundation from the immutable source.

Run with Blender: --background --python this.py -- --phase build|audit ...
The script intentionally copies only body/face ownership into the delivered
scene; hair and clothing remain source-side, independent assets.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from refine_mia_head_v06 import refine_head, set_mia_neutral as set_head_neutral


BODY = "Mia_Body_Anatomy_Skin"
FACE = "Mia_Face_AnimeTopology"
FACE_ART_DERIVED = "asset/mia/blender/mia-production-stage2-face/v05/Mia_ReusedFace_ArtStudy.blend"


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("baseline", "build", "audit"), required=True)
    p.add_argument("--source")
    p.add_argument("--output-dir", required=True)
    p.add_argument("--blend")
    return p.parse_args(sys.argv[sys.argv.index("--") + 1:])


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        if c.name != "Collection":
            bpy.data.collections.remove(c)


def material(name, color, roughness=.62):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes = m.node_tree.nodes
    for n in list(nodes):
        nodes.remove(n)
    out = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    m.node_tree.links.new(shader.outputs["BSDF"], out.inputs["Surface"])
    return m


def col(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def link_copy(source, name, target):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    target.objects.link(obj)
    return obj


def reparent_keep_world(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj.matrix_world = world


def transform_record(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices] if obj.type == "MESH" else []
    record={"name":obj.name,"parent":obj.parent.name if obj.parent else None,
            "matrix_world":[[round(v,6) for v in row] for row in obj.matrix_world]}
    if pts:
        record["world_bounds"]=[[round(min(p[i] for p in pts),6) for i in range(3)],
                                [round(max(p[i] for p in pts),6) for i in range(3)]]
    return record


def bounds(obj):
    pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
    return [[round(min(p[i] for p in pts), 6) for i in range(3)],
            [round(max(p[i] for p in pts), 6) for i in range(3)]]


def mesh_info(obj):
    mesh = obj.data
    return {
        "name": obj.name, "vertices": len(mesh.vertices), "polygons": len(mesh.polygons),
        "uv_layers": [x.name for x in mesh.uv_layers],
        "key_names": [x.name for x in mesh.shape_keys.key_blocks] if mesh.shape_keys else [],
        "armature_modifiers": [{"name": x.name, "target": x.object.name if x.object else None}
                              for x in obj.modifiers if x.type == "ARMATURE"],
        "world_bounds": bounds(obj),
    }


def mesh_semantic_inventory(obj):
    mesh = obj.data
    unused = set(range(len(mesh.vertices))); adjacency = {i: set() for i in unused}
    for poly in mesh.polygons:
        ids = list(poly.vertices)
        for a, b in zip(ids, ids[1:] + ids[:1]): adjacency[a].add(b); adjacency[b].add(a)
    components = []
    while unused:
        stack = [unused.pop()]; found = set(stack)
        while stack:
            index = stack.pop()
            for other in adjacency[index] & unused:
                unused.remove(other); found.add(other); stack.append(other)
        components.append(len(found))
    return {"materials": [{"index":i,"name":m.name if m else None,
                            "polygons":sum(p.material_index == i for p in mesh.polygons)}
                           for i,m in enumerate(mesh.materials)],
            "connected_component_vertex_counts": sorted(components, reverse=True)[:16]}


def silhouette_metrics(obj, bands):
    result = {}
    for label, low, high in bands:
        pts = [v.co for v in obj.data.vertices if low <= v.co.z <= high]
        if pts:
            result[label] = {"width_x": round(max(p.x for p in pts) - min(p.x for p in pts), 6),
                             "depth_y": round(max(p.y for p in pts) - min(p.y for p in pts), 6),
                             "vertices": len(pts)}
    return result


def body_semantic_metrics(obj):
    """ROI measures that reject head/arm/hand influences from the combined mesh."""
    names = {g.index:g.name for g in obj.vertex_groups}
    excluded = ("Head", "Neck", "Shoulder", "UpperArm", "LowerArm", "Hand", "Index", "Middle", "Ring", "Little", "Thumb")
    regions = {"waist":(1.10,1.18), "pelvis":(.90,1.06), "thigh":(.56,.84), "calf":(.24,.50)}
    report = {}
    for label, (low, high) in regions.items():
        pts=[]
        for vertex in obj.data.vertices:
            used=[names[x.group] for x in vertex.groups if x.weight > .22 and x.group in names]
            if any(term in name for term in excluded for name in used): continue
            point = obj.matrix_world @ vertex.co
            if low <= point.z <= high: pts.append(point)
        report[label] = {"vertex_count":len(pts),
                         "width_x":round(max(p.x for p in pts)-min(p.x for p in pts),6) if pts else None,
                         "depth_y":round(max(p.y for p in pts)-min(p.y for p in pts),6) if pts else None,
                         "method":"world-space weighted body ROI; excludes head/neck/arms/hands"}
        if label in ("thigh", "calf"):
            for side, sign in (("left", 1), ("right", -1)):
                local = [p for p in pts if p.x * sign > 0]
                report[label][side] = {"width_x":round(max(p.x for p in local)-min(p.x for p in local),6) if local else None,
                                       "center_x":round(sum(p.x for p in local)/len(local),6) if local else None,
                                       "vertices":len(local)}
    return report


def affine_all_keys(obj, func):
    """Apply a position-only art fit to all corresponding vertex key blocks."""
    blocks = list(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else []
    if not blocks:
        blocks = [None]
    for block in blocks:
        points = block.data if block else obj.data.vertices
        for p in points:
            p.co = func(p.co.copy())


def fit_body(body):
    groups = {g.index: g.name for g in body.vertex_groups}
    arm_head = ("Head", "Neck", "Shoulder", "UpperArm", "LowerArm", "Hand", "Index", "Middle", "Ring", "Little", "Thumb")
    leg = ("UpperLeg", "LowerLeg", "Foot", "ToeBase")
    torso = ("Hips", "Spine", "Chest", "UpperChest", "Bust")
    armature = next((m.object for m in body.modifiers if m.type == "ARMATURE" and m.object), None)
    body_world = body.matrix_world.copy(); body_inverse = body_world.inverted()
    bones = armature.data.bones if armature else {}
    def nearest_center(side, lower, z):
        name = "J_Bip_%s_%s" % (side, "LowerLeg" if lower else "UpperLeg")
        bone = bones.get(name)
        if not bone: return Vector()
        head, tail = armature.matrix_world @ bone.head_local, armature.matrix_world @ bone.tail_local
        t = max(0.0, min(1.0, (z-head.z)/(tail.z-head.z))) if abs(tail.z-head.z) > 1e-6 else .5
        return head.lerp(tail, t)
    def smoothstep(t):
        t=max(0.0,min(1.0,t)); return t*t*(3.0-2.0*t)
    def profile(z, knots):
        if z <= knots[0][0]: return knots[0][1]
        for (a, va), (b, vb) in zip(knots, knots[1:]):
            if z <= b:
                return va + (vb-va)*smoothstep((z-a)/(b-a))
        return knots[-1][1]
    for i, vertex in enumerate(body.data.vertices):
        p = body_world @ vertex.co; influences = [groups[g.group] for g in vertex.groups if g.weight > .22 and g.group in groups]
        if any(term in name for term in arm_head for name in influences):
            continue  # Back-head and limbs are never mistaken for torso contour samples.
        z = p.z
        if any(term in name for term in leg for name in influences):
            side = "L" if any("_L_" in name for name in influences) else "R"
            lower = any("LowerLeg" in name for name in influences)
            center = nearest_center(side, lower, z)
            # Radius fit occurs around each rest-bone centerline, never world
            # origin: joint centers, stance and bone alignment are preserved.
            if lower:
                scale = profile(z, [(0.14,.93),(.24,.93),(.34,1.13),(.43,1.13),(.61,1.03)])
            else:
                scale = 1.01
            p.x = center.x + (p.x-center.x)*scale
            # Match the local depth radius to the continuous lateral profile;
            # knees/calf/ankle stay centered on their actual bone line.
            depth_scale = .97 + .55*(scale-1.0)
            p.y = center.y + (p.y-center.y)*depth_scale
        elif any(term in name for term in torso for name in influences):
            # Bone anchors: hips .97–1.01, spine 1.06–1.18, chest 1.18–1.31,
            # upper chest 1.31–1.42.  The waist is therefore around 1.14m.
            sx = profile(z, [(0.90,1.02),(1.07,1.02),(1.10,.89),(1.14,.80),
                             (1.18,.80),(1.22,.84),(1.31,.91),(1.43,.96)])
            p.x *= sx
            # Front chest is supported from lower ribcage with a smooth,
            # shallow projection; no independent spherical graft is added.
            # Canonical rest-world frame: camera/front is negative world Y.
            if 1.25 < z < 1.50 and p.y < .02:
                p.y -= .010 * math.sin((z - 1.25) / .25 * math.pi)
            # Author a slim front torso envelope from lower rib through pelvis:
            # ease the lower belly back into the torso without erasing the
            # natural pubis transition or changing the leg/hip joint center.
            if .93 < z < 1.15 and p.y < -.006:
                p.y += .012 * math.sin((z-.93)/.22*math.pi)
            # Spread chest mass into the existing thorax connection instead of
            # adding a new volume: flatten lower/outer projection while a small
            # upper-rib support remains continuous with the sternum.
            if 1.19 < z < 1.34 and p.y < -.006:
                outer = min(1.0, abs(p.x)/.14)
                p.y += .008 * math.sin((z-1.19)/.15*math.pi) * (.45+.55*outer)
            if 1.34 <= z < 1.43 and p.y < -.006:
                p.y -= .003 * math.sin((z-1.34)/.09*math.pi)
        vertex.co = body_inverse @ p


def fair_bust_attachment(body):
    """Small authored positional fairing at the weighted bust-to-rib boundary."""
    groups={g.index:g.name for g in body.vertex_groups}; mesh=body.data; world=body.matrix_world
    bust=set()
    for vertex in mesh.vertices:
        if any('Bust' in groups.get(x.group,'') and x.weight>.20 for x in vertex.groups): bust.add(vertex.index)
    adjacency={i:set() for i in range(len(mesh.vertices))}
    for edge in mesh.edges:
        a,b=edge.vertices; adjacency[a].add(b);adjacency[b].add(a)
    boundary={a for a in bust if any(n not in bust for n in adjacency[a])}
    outer_ring={n for index in boundary for n in adjacency[index] if n not in bust}
    outer_ring_2={n for index in outer_ring for n in adjacency[index]
                  if n not in bust and n not in outer_ring}
    # The breast peak is not part of this set: fair only the Bust boundary and
    # its two adjacent thorax rings.  This relaxes the connected transition
    # without turning the authored volume into a uniformly shrunken sphere.
    ring=set(boundary) | outer_ring | outer_ring_2
    eligible=[]
    for index in ring:
        p=world @ mesh.vertices[index].co
        if not (1.20 < p.z < 1.38) or abs(p.x) > .205: continue
        eligible.append(index)
    before=[world @ mesh.vertices[i].co for i in eligible]
    targets={}
    for index in eligible:
        ns=list(adjacency[index])
        targets[index]=sum((mesh.vertices[n].co for n in ns),Vector())/len(ns)
    for index in eligible:
        old=mesh.vertices[index].co; delta=(targets[index]-old)*.28
        if delta.length>.003: delta.normalize();delta*=.003
        mesh.vertices[index].co=old+delta
    after=[world @ mesh.vertices[i].co for i in eligible]
    def box(points): return [[round(min(p[k] for p in points),6) for k in range(3)],[round(max(p[k] for p in points),6) for k in range(3)]] if points else None
    return {"method":"Bust-boundary plus two thorax-ring positional fairing; no UV/index/normal edit","bust_vertices":len(bust),"boundary_vertices":len(boundary),"outer_ring_vertices":len(outer_ring),"outer_ring_2_vertices":len(outer_ring_2),"eligible_vertices":len(eligible),"before_bounds":box(before),"after_bounds":box(after),"max_displacement_m":round(max(((a-b).length for a,b in zip(after,before)),default=0),6)}


def fit_face(face):
    # Preserve key correspondence by transforming every existing key.  Material
    # islands identify eye/iris cards without replacing their authored topology.
    owners = {i:set() for i in range(len(face.data.vertices))}
    for poly in face.data.polygons:
        for index in poly.vertices: owners[index].add(poly.material_index)
    basis = face.data.shape_keys.key_blocks[0]
    centers = {}
    for side in (-1, 1):
        points = [basis.data[i].co for i in owners if 1 in owners[i] and basis.data[i].co.x * side > 0]
        centers[side] = Vector((sum(p.x for p in points) / len(points), 0,
                                sum(p.z for p in points) / len(points)))
    def f(p):
        q = p.copy()
        # Slightly compress the bare cranial cap vertically; the final hair
        # asset supplies silhouette, but this core must stand on its own.
        q.z = 1.465 + (q.z - 1.465) * .94
        center_z = 1.585
        if q.z < 1.570:
            # A slightly tapered mature lower face; no replacement topology.
            amount = min(1.0, max(0.0, (1.570 - q.z) / .10))
            q.x *= 1.0 - .065 * amount
            q.y -= .003 * amount
        return q
    blocks = list(face.data.shape_keys.key_blocks)
    for block in blocks:
        for i, point in enumerate(block.data):
            q = f(point.co.copy())
            # Tired, narrow horizontal aperture: eye whites/rims/lashes/irises
            # are transported with the same face key index, not altered only in
            # Basis.  Iris is slightly smaller and lower, retaining gaze space.
            if owners[i] & {1, 2, 3, 4, 5, 6, 8}:
                side = -1 if q.x < 0 else 1; c = centers[side]
                if owners[i] & {5, 6, 8}:
                    q.x = c.x + (q.x - c.x) * .82
                    q.z = c.z + (q.z - c.z) * .82 - .003
                else:
                    q.x = c.x + (q.x - c.x) * .96
                    q.z = c.z + (q.z - c.z) * .76 - .002
            point.co = q


def set_mia_neutral(face):
    """A restrained, tired neutral built from the preserved expression keys."""
    values = {"Fcl_EYE_Close": .23, "Fcl_EYE_Sorrow": .11,
              "Fcl_BRW_Angry": .10, "Fcl_MTH_Angry": .10,
              "Fcl_MTH_Neutral": .18}
    applied = {}
    for suffix, value in values.items():
        match = next((x for x in face.data.shape_keys.key_blocks if x.name.endswith(suffix)), None)
        if match: match.value = value; applied[match.name] = value
    return applied


def display_underwear(scene, body):
    """Separate, removable charcoal display proxy; it is never merged to skin."""
    c = bpy.data.collections.new("MIA_V06_DISPLAY_UNDERWEAR")
    scene.collection.children.link(c)
    dark = material("MIA_V06_CharcoalUnderwear", (.035, .05, .075, 1), .78)
    # Extract a pelvis-only shell from the copied skin topology so the display
    # layer follows the real silhouette without becoming part of body skin.
    brief = body.copy(); brief.data = body.data.copy(); brief.name = "MIA_V06_DISPLAY_BRIEF_PROXY"
    c.objects.link(brief)
    keep = []
    for polygon in brief.data.polygons:
        z = sum(brief.data.vertices[i].co.z for i in polygon.vertices) / len(polygon.vertices)
        polygon.select = not (.73 <= z <= .94)
        if not polygon.select: keep.append(polygon.index)
    bpy.context.view_layer.objects.active = brief; brief.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
    brief.select_set(False); brief.data.materials.clear(); brief.data.materials.append(dark)
    shell = brief.modifiers.new("MIA_V06_DISPLAY_BRIEF_SOLIDITY", "SOLIDIFY"); shell.thickness = .0018
    # Replace derived body slot display only. UVs and geometry remain untouched.
    skin = material("MIA_V06_DISPLAY_SKIN", (.28, .13, .11, 1), .82)
    originals = []
    for slot in body.material_slots:
        originals.append(slot.material.name if slot.material else None)
        slot.material = skin
    return {"collection": c.name, "objects": [brief.name], "kept_shell_polygons": len(keep), "replaced_body_slots": originals}


def unify_skin_display(face):
    """Match only the derived face's skin islands to the body display response."""
    skin = material("MIA_V06_FACE_SKIN_DISPLAY", (.28, .13, .11, 1), .82)
    changed = []
    for index in (0, 7):
        if index < len(face.material_slots):
            changed.append({"slot": index, "old": face.material_slots[index].material.name if face.material_slots[index].material else None})
            face.material_slots[index].material = skin
    return changed


def principled_from_color_signal(source, name):
    """Retain an authored skin color/pigment path but replace emission lighting."""
    mat = source.copy(); mat.name = name; nodes, links = mat.node_tree.nodes, mat.node_tree.links
    output = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not output: return mat, "no_output"
    signal = None
    image = nodes.get("Mtoon1BaseColorTexture.Image")
    if image and image.outputs.get("Color"):
        signal = image.outputs["Color"]
    else:
        emission = next((n for n in nodes if n.type == "EMISSION"), None)
        if emission and emission.inputs["Color"].links:
            signal = emission.inputs["Color"].links[0].from_socket
    if not signal: return mat, "no_color_signal"
    shader = nodes.new("ShaderNodeBsdfPrincipled"); shader.name = "MIA_V06_StudioSkin"
    shader.inputs["Roughness"].default_value = .78
    links.new(signal, shader.inputs["Base Color"])
    for link in list(output.inputs["Surface"].links): links.remove(link)
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    return mat, "principled_from_authored_color"


def studio_skin_lookdev(body, face):
    """Convert only skin material slots to lit authored-color copies."""
    changed = []
    body_source = body.material_slots[0].material if body.material_slots else None
    if body_source:
        body_mat, mode = principled_from_color_signal(body_source, "MIA_V06_BODY_STUDIO_SKIN")
        body.material_slots[0].material = body_mat; changed.append({"owner":"body","source":body_source.name,"mode":mode})
    for index in (0, 7):
        if index < len(face.material_slots) and face.material_slots[index].material:
            source = face.material_slots[index].material
            face_mat, mode = principled_from_color_signal(source, "MIA_V06_FACE_STUDIO_SKIN_%d" % index)
            face.material_slots[index].material = face_mat
            changed.append({"owner":"face","slot":index,"source":source.name,"mode":mode})
    return changed


def create_reference(target, path, name, location):
    image = bpy.data.images.load(str(path), check_existing=True)
    image.pack()
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = "IMAGE"
    empty.data = image
    empty.empty_display_size = 1.0
    empty.empty_display_size = 1.0
    empty.location = location
    empty.hide_render = True
    empty["reference_path"] = str(path)
    target.objects.link(empty)
    return empty


def camera(scene):
    cam = bpy.data.cameras.new("MIA_V06_REVIEW_CAMERA")
    cam.lens = 58
    obj = bpy.data.objects.new(cam.name, cam)
    scene.collection.objects.link(obj)
    scene.camera = obj
    return obj


def aim(obj, location, target):
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lighting(scene):
    for name, loc, energy, size in (("Key", (2.5, -3.4, 3.1), 260, 2.5),
                                    ("Fill", (-2.6, -2.0, 2.0), 115, 2.1),
                                    ("Rim", (0.0, 2.5, 2.8), 160, 1.5)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size = energy, "DISK", size
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = loc
        aim(obj, loc, (0, 0, 1.05))
    scene.world.color = (.055, .065, .085)


def setup_render(scene):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"


def render_views(scene, body, face, out, stem, clay=False, wire=False):
    out.mkdir(parents=True, exist_ok=True)
    cam = scene.camera
    claymat = material("MIA_V06_CLAY", (.18, .20, .24, 1), .86)
    original_override = bpy.context.view_layer.material_override
    if clay:
        bpy.context.view_layer.material_override = claymat
    temps = []
    if wire:
        for source in (body, face):
            source.hide_render = True
            obj = source.copy(); obj.data = source.data.copy(); obj.name = "WIRE_" + source.name
            scene.collection.objects.link(obj)
            obj.hide_render = False
            obj.data.materials.clear(); obj.data.materials.append(material("MIA_V06_WIRE", (.05,.07,.1,1), .42))
            mod = obj.modifiers.new("MIA_V06_Wireframe", "WIREFRAME")
            mod.thickness = .0014
            temps.append((source, obj))
    views = {
        "front": ((0, -3.35, 1.0), (0, 0, .95)),
        "three_quarter_l": ((2.25, -2.65, 1.0), (0, 0, .95)),
        "profile_l": ((3.30, 0, 1.0), (0, 0, .95)),
        "back": ((0, 3.35, 1.0), (0, 0, .95)),
        "head_front": ((0, -1.5, 1.59), (0, .02, 1.59)),
        "head_three_quarter": ((.92, -1.17, 1.59), (0, .02, 1.59)),
    }
    made = []
    for name, (pos, target) in views.items():
        aim(cam, pos, target)
        scene.render.filepath = str(out / f"{stem}_{name}.png")
        bpy.ops.render.render(write_still=True)
        made.append(str(out / f"{stem}_{name}.png"))
    for source, obj in temps:
        bpy.data.objects.remove(obj, do_unlink=True)
        source.hide_render = False
    bpy.context.view_layer.material_override = original_override
    return made


def pose_proofs(scene, armature, face, out):
    out.mkdir(parents=True, exist_ok=True)
    cam = scene.camera
    log, rendered = [], []
    blocks = face.data.shape_keys.key_blocks
    def key(term, value):
        found = [x for x in blocks if x.name.endswith(term)]
        if found: found[0].value = value
        return found[0].name if found else None
    def clear_expression_only():
        for b in blocks:
            if "Fcl_" in b.name:
                b.value = 0
    clear_expression_only()
    cases = [("blink", [("Fcl_EYE_Close", 1.0)]), ("mouth_a", [("Fcl_MTH_A", 1.0)])]
    for name, items in cases:
        clear_expression_only()
        names = [key(t, v) for t, v in items]
        aim(cam, (0, -1.5, 1.59), (0, .02, 1.59))
        scene.render.filepath = str(out / f"facial_{name}.png")
        bpy.ops.render.render(write_still=True)
        rendered.append(str(out / f"facial_{name}.png")); log.append({"case": name, "keys": names})
    if armature:
        eye_names = ["J_Adj_L_FaceEye", "J_Adj_R_FaceEye"]
        changed = []
        for name in eye_names:
            bone = armature.pose.bones.get(name)
            if bone:
                bone.rotation_mode = "XYZ"; bone.rotation_euler = (.12, 0, 0); changed.append(name)
        bpy.context.view_layer.update(); aim(cam, (0, -1.5, 1.59), (0, .02, 1.59))
        scene.render.filepath = str(out / "facial_gaze_eye_bones.png"); bpy.ops.render.render(write_still=True)
        rendered.append(str(out / "facial_gaze_eye_bones.png")); log.append({"case":"gaze_eye_bones","bones":changed})
        for name in changed: armature.pose.bones[name].rotation_euler = (0,0,0)
        bpy.context.view_layer.update()
    clear_expression_only()
    if armature:
        motions = [("arm_raise", "J_Bip_L_UpperArm", (-.30, 0, 0)),
                   ("arm_forward", "J_Bip_R_UpperArm", (-1.08, .45, 0)),
                   ("torso_yaw", "J_Bip_C_Chest", (0, 0, .26)),
                   ("knee_bend", "J_Bip_L_LowerLeg", (.42, 0, 0))]
        for name, bone_name, rotation in motions:
            bone = armature.pose.bones.get(bone_name)
            if not bone:
                log.append({"case":name,"status":"MISSING_BONE"}); continue
            old_mode, old_rot = bone.rotation_mode, tuple(bone.rotation_euler)
            bone.rotation_mode = "XYZ"; bone.rotation_euler = rotation
            bpy.context.view_layer.update()
            aim(cam, (2.8, -3.35, 1.0), (0, 0, .95))
            scene.render.filepath = str(out / f"rig_{name}.png")
            bpy.ops.render.render(write_still=True)
            rendered.append(str(out / f"rig_{name}.png")); log.append({"case":name,"bone":bone_name,"rotation":rotation})
            bone.rotation_euler = old_rot; bone.rotation_mode = old_mode
            bpy.context.view_layer.update()
    return rendered, log


def set_reference_a_pose(armature):
    """Use the actual upper-arm controls to establish the v06 A-pose baseline."""
    if not armature:
        return []
    applied = []
    for name in ("J_Bip_L_UpperArm", "J_Bip_R_UpperArm"):
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            # Bone local Y follows the source arm; its local X drops it toward
            # the body without scaling the arm span into a false shoulder fit.
            bone.rotation_euler = (-1.08, 0, 0)
            applied.append(name)
    # Derive a modest leg abduction from rest-bone vectors (rather than a
    # guessed Euler).  This supplies a readable A-pose stance while preserving
    # source joint lengths and the local-radius body fit.
    for side, sign in (("L", 1), ("R", -1)):
        name = "J_Bip_%s_UpperLeg" % side; bone = armature.pose.bones.get(name)
        rest = armature.data.bones.get(name)
        if bone and rest:
            source = rest.tail_local - rest.head_local
            target = source + Vector((sign * .040, 0, 0))
            q_armature_delta = source.rotation_difference(target)
            q_rest = rest.matrix_local.to_quaternion()
            bone.rotation_mode = "QUATERNION"
            # Pose-bone rotation is local to its rest basis, while the desired
            # vector is in armature rest space.  Convert bases explicitly.
            bone.rotation_quaternion = q_rest.inverted() @ q_armature_delta @ q_rest
            applied.append(name + "_derived_abduction")
    bpy.context.view_layer.update()
    endpoints = {}
    for side in ("L", "R"):
        for role in ("UpperLeg", "LowerLeg", "Foot"):
            name = "J_Bip_%s_%s" % (side, role); rest = armature.data.bones.get(name); pose = armature.pose.bones.get(name)
            if rest and pose:
                endpoints[name] = {"rest_head_world": [round(x,6) for x in (armature.matrix_world @ rest.head_local)],
                                   "rest_tail_world": [round(x,6) for x in (armature.matrix_world @ rest.tail_local)],
                                   "evaluated_head_world": [round(x,6) for x in (armature.matrix_world @ pose.head)],
                                   "evaluated_tail_world": [round(x,6) for x in (armature.matrix_world @ pose.tail)]}
    return {"controls":applied, "evaluated_endpoints":endpoints}


def build(a):
    source = Path(a.source).resolve(); out = Path(a.output_dir).resolve()
    source_sha = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    source_body, source_face = bpy.data.objects[BODY], bpy.data.objects[FACE]
    source_inventory = {"body": mesh_info(source_body), "face": mesh_info(source_face),
                        "source_sha256_before": source_sha,
                        "body_semantics": mesh_semantic_inventory(source_body),
                        "face_semantics": mesh_semantic_inventory(source_face)}
    # Work in a source-loaded scene but isolate the authored checkpoint into
    # dedicated ownership collections; original objects are hidden, never edited.
    scene = bpy.context.scene
    anatomy, refs, rigcol = col("MIA_V06_ANATOMY"), col("MIA_V06_REFERENCE_GUIDES"), col("MIA_V06_RIG")
    body = link_copy(source_body, "MIA_V06_BODY_SKIN", anatomy)
    # The approved v05 face-art study retains the original Face42 prefix and
    # adds two owned corrective keys.  It is used only as a derived face layer,
    # never as a replacement for the immutable 02:40 archive.
    face_source = source_face
    v05 = Path(__file__).resolve().parents[3] / FACE_ART_DERIVED
    if v05.exists():
        with bpy.data.libraries.load(str(v05), link=False) as (data_from, data_to):
            data_to.objects = [FACE] if FACE in data_from.objects else []
        if data_to.objects and data_to.objects[0]:
            face_source = data_to.objects[0]
            scene.collection.objects.link(face_source)
            # Library append does not bring the archive Armature parent that
            # carries the face's active Rz180 placement.  Restore the verified
            # source active-face world frame before production reparenting.
            face_source.matrix_world = source_face.matrix_world.copy()
    face = link_copy(face_source, "MIA_V06_FACE_SKIN", anatomy)
    if face_source != source_face:
        bpy.data.objects.remove(face_source, do_unlink=True)
    armature = next((m.object for m in body.modifiers if m.type == "ARMATURE" and m.object), None)
    if armature:
        source_rig_world = armature.matrix_world.copy()
        armature_copy = armature.copy(); armature_copy.data = armature.data.copy(); armature_copy.name = "MIA_V06_RIG"; rigcol.objects.link(armature_copy)
        armature_copy.parent = None; armature_copy.matrix_world = source_rig_world
        for obj in (body, face):
            for m in obj.modifiers:
                if m.type == "ARMATURE": m.object = armature_copy
            reparent_keep_world(obj, armature_copy)
        armature = armature_copy
    # Hide every original source object so the presentation is not an accidental merged assembly.
    for obj in list(bpy.context.scene.objects):
        if obj not in (body, face, armature): obj.hide_render = True; obj.hide_viewport = True
    frames_before_fit={"source_body":transform_record(source_body),"source_face":transform_record(source_face),"production_body":transform_record(body),"production_face":transform_record(face),"production_rig":transform_record(armature) if armature else None}
    fit_body(body); bust_fairing=fair_bust_attachment(body); fit_face(face)
    head_refine = refine_head(face, body, armature, expected_stage="v04-mapped")
    # Kept in source-authored MToon/pigment response until a calibrated shared
    # texture-space skin pass is available; see build report limitation.
    face_skin_slots = []
    root = Path(__file__).resolve().parents[3]
    create_reference(refs, root / "asset/mia/references/body-foundation/v06/mia-body-turnaround-v06.png", "REF_V06_TURNAROUND", (0, 2, 1))
    create_reference(refs, root / "asset/mia/references/body-foundation/v06/mia-body-visibility-guide-v06.png", "REF_V06_VISIBILITY", (0, 2.2, 1))
    create_reference(refs, root / "asset/mia/references/mia-expression-style-confirmed-20261031.png", "REF_MIA_CONFIRMED_FACE", (0, 2.4, 1))
    for obj in refs.objects: obj.hide_render = True
    # The native checkpoint contains no display-underwear shell.  Final proof
    # is intentionally rendered in a second step by the isolated matrix and
    # pose tools, which exclude proxies/archive/card artefacts by design.
    a_pose_controls = set_reference_a_pose(armature)
    scene.render.fps = 30; scene.render.fps_base = 1.0
    scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.0; scene.view_settings.gamma = 1.0
    # Apply the head helper's neutral after every setup action so its two
    # identity profiles remain active in the saved reference idle/A-pose.
    neutral_keys = set_head_neutral(face)
    blend = out / "Mia_BodyHead_v06.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report = {"source": str(source), "source_sha256_before": source_sha,
              "source_sha256_after": digest(source), "source_inventory": source_inventory,
              "frame_record_before_fit": frames_before_fit,
              "frame_record_after_fit":{"production_body":transform_record(body),"production_face":transform_record(face),"production_rig":transform_record(armature) if armature else None},
              "derived": {"body": mesh_info(body), "face": mesh_info(face), "references": [x.name for x in refs.objects],
                          "face_art_source": str(v05) if v05.exists() else "02:40 Face42 only"},
              "silhouette_metrics": {"source_body": silhouette_metrics(source_body, [("calf",.20,.50),("thigh",.70,1.02),("waist",1.10,1.18),("chest",1.24,1.40)]),
                                     "derived_body": silhouette_metrics(body, [("calf",.20,.50),("thigh",.70,1.02),("waist",1.10,1.18),("chest",1.24,1.40)]),
                                     "source_face": silhouette_metrics(source_face, [("jaw",1.46,1.57),("eye",1.55,1.64),("cap",1.64,1.71)]),
                                     "derived_face": silhouette_metrics(face, [("jaw",1.46,1.57),("eye",1.55,1.64),("cap",1.64,1.71)])},
              "semantic_body_roi_metrics": {"source":body_semantic_metrics(source_body), "derived":body_semantic_metrics(body)},
              "bust_attachment_fairing": bust_fairing,
              "head_refine": head_refine,
              "final_evidence": {"legacy_render_views": "not used as final evidence",
                                 "required_external_tools": ["render_mia_body_head_v06_matrix.py", "render_mia_body_head_v06_poses.py", "audit_mia_body_head_v06_independent.py"]},
              "reference_a_pose_controls": a_pose_controls,
              "neutral_expression_keys": neutral_keys, "display_underwear": {"created": False, "reason": "anatomy validation excludes display proxies"},
              "scene_output": {"fps": scene.render.fps, "fps_base": scene.render.fps_base,
                               "view_transform": scene.view_settings.view_transform, "look": scene.view_settings.look,
                               "exposure": scene.view_settings.exposure, "gamma": scene.view_settings.gamma},
              "matched_face_skin_slots": face_skin_slots,
              "landmark_direction": {"waist":"narrower horizontal silhouette", "hips_thighs":"preserved/restored relative width", "calves":"reduced lateral scale", "chest":"restrained front/outer volume"},
              "limits": ["v06 is illustrative rather than calibrated orthographic data", "hair, clothing, accessories and secondary motion are out of scope"]}
    (out / "build-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    recipe = {"input_source": str(source), "input_source_sha256": source_sha,
              "builder_script": str(Path(__file__).resolve()), "builder_script_sha256": digest(Path(__file__).resolve()),
              "shader_dependencies": {"head_refine": {"path": str(Path(__file__).resolve().parent / "refine_mia_head_v06.py"),
                                                        "sha256": digest(Path(__file__).resolve().parent / "refine_mia_head_v06.py")},
                                      "astra_fatigue_ink": {"path": str(Path(__file__).resolve().parent / "astra_mia_fatigue_v08.py"),
                                                             "sha256": digest(Path(__file__).resolve().parent / "astra_mia_fatigue_v08.py")}},
              "output_native": str(blend), "output_native_sha256": digest(blend),
              "common_neutral": {"expression_keys": neutral_keys, "a_pose_controls": a_pose_controls},
              "coordinate_frame": "Body and Face retain source active world Rz180; MIA_V06_RIG world is identity"}
    (out / "recipe-metadata.json").write_text(json.dumps(recipe, indent=2), encoding="utf-8")


def baseline(a):
    source, out = Path(a.source).resolve(), Path(a.output_dir).resolve()
    before = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    body, face = bpy.data.objects[BODY], bpy.data.objects[FACE]
    for obj in scene.objects:
        if obj not in (body, face):
            obj.hide_render = True
    setup_render(scene); camera(scene); lighting(scene)
    proof = out / "baseline"
    actual = render_views(scene, body, face, proof, "source_actual")
    clay = render_views(scene, body, face, proof, "source_clay", clay=True)
    report = {"source": str(source), "source_sha256_before": before,
              "source_sha256_after": digest(source), "inventory": {"body":mesh_info(body),"face":mesh_info(face)},
              "actual": actual, "clay": clay,
              "note":"Fresh baseline render from the immutable 02:40 source before v06 derived fitting."}
    (out / "baseline-inventory.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def audit(a):
    out = Path(a.output_dir).resolve(); blend = Path(a.blend).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    body, face = bpy.data.objects.get("MIA_V06_BODY_SKIN"), bpy.data.objects.get("MIA_V06_FACE_SKIN")
    checks = {"body_exists": body is not None, "face_exists": face is not None,
              "body_vertices": len(body.data.vertices) if body else None,
              "face_vertices": len(face.data.vertices) if face else None,
              "face_keys": [x.name for x in face.data.shape_keys.key_blocks] if face and face.data.shape_keys else [],
              "reference_objects": [x.name for x in bpy.data.objects if x.name.startswith("REF_")],
              "packed_reference_images": {x.name: bool(x.data and getattr(x.data, "packed_file", None))
                                          for x in bpy.data.objects if x.name.startswith("REF_")},
              "forbidden_merged_hair": any("hair" in x.name.lower() for x in (body, face) if x),
              "fresh_reopen": True}
    scene = bpy.context.scene; setup_render(scene)
    if not scene.camera: camera(scene)
    if not any(x.type == "LIGHT" for x in scene.objects): lighting(scene)
    aim(scene.camera, (0, -1.5, 1.59), (0, .02, 1.59))
    proof = out / "fresh-reopen"; proof.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(proof / "fresh_head_front.png"); bpy.ops.render.render(write_still=True)
    checks["proof"] = str(proof / "fresh_head_front.png")
    checks["pass_structure"] = bool(checks["body_exists"] and checks["face_exists"] and len(checks["face_keys"]) >= 42 and not checks["forbidden_merged_hair"])
    (out / "fresh-reopen-audit.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")


if __name__ == "__main__":
    a = args()
    if a.phase == "baseline":
        if not a.source: raise SystemExit("--source is required for baseline")
        baseline(a)
    elif a.phase == "build":
        if not a.source: raise SystemExit("--source is required for build")
        build(a)
    else:
        if not a.blend: raise SystemExit("--blend is required for audit")
        audit(a)
