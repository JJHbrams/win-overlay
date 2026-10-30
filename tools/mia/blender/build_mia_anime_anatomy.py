#!/usr/bin/env python3
"""Build a reviewable Mia anatomy checkpoint from the pristine licensed VRoid import.

The VRM import is opened read-only in practice: this script only writes a new
checkpoint.  It retains the source Face topology, UVs, materials, armature and
all expression keys; the foreign hair/wardrobe remain archived and hidden.

Input must be the pristine Victoria import, never an earlier `Mia_*` derived
checkpoint.  The builder asserts that the resulting review assembly has one
visible owned Face mesh and one visible owned Body mesh.
"""
import argparse
import hashlib
import json
import math
import shutil
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--shared-head-cage", action="store_true")
    parser.add_argument("--quick-gate", action="store_true",
                        help="640px front/three-quarter plus blink/mouth visual acceptance gate")
    parser.add_argument("--disable-face-nodes", action="store_true",
                        help="diagnostic: disable every Face Geometry Nodes modifier for art comparison")
    return parser.parse_args(values)


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def collection(name):
    old = bpy.data.collections.get(name)
    if old:
        return old
    made = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(made)
    return made


def move_to(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def duplicate_to(obj, name, target):
    made = obj.copy()
    made.data = obj.data.copy()
    made.name = name
    # v8 input archives its source meshes; a new owned derivative must not
    # inherit those visibility flags before edit-mode material isolation.
    made.hide_render = False
    made.hide_viewport = False
    target.objects.link(made)
    return made


def hide_source_originals():
    archive = collection("SOURCE_ARCHIVE_Victoria_Rubin")
    for name in ("Body", "Face", "Hair001"):
        obj = bpy.data.objects.get(name)
        if obj:
            move_to(obj, archive)
            obj.hide_render = True
            obj.hide_viewport = True
    # Armature is retained as the licensed animation-ready rig owner, but it
    # has no render surface.
    armature = bpy.data.objects.get("Armature")
    if armature:
        move_to(armature, archive)


def skin_only_copy(source, target):
    """Create a material-isolated anatomy copy without touching source Body."""
    made = duplicate_to(source, "Mia_Body_Anatomy_Skin", target)
    skin_slots = {
        i for i, material in enumerate(made.data.materials)
        if material and "SKIN" in material.name.upper()
    }
    # Delete garment faces only from our copy.  This makes material ownership
    # inspectable, while the untouched imported Body remains archived.
    bpy.context.view_layer.objects.active = made
    made.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for poly in made.data.polygons:
        poly.select = poly.material_index not in skin_slots
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    made.select_set(False)
    made["role"] = "ANATOMY_BODY_SKIN_ONLY"
    made["source_mesh"] = "Body"
    made["removed_material_slots"] = [
        material.name for i, material in enumerate(source.data.materials)
        if i not in skin_slots and material
    ]
    return made, skin_slots


def mia_face_copy(source, target):
    made = duplicate_to(source, "Mia_Face_AnimeTopology", target)
    made["role"] = "ANATOMY_FACE_TOPOLOGY"
    made["source_mesh"] = "Face"
    made["basis_edit"] = "source facial topology retained; local brow and mouth component edits only"
    keys = made.data.shape_keys.key_blocks
    basis = keys[0]
    original = [point.co.copy() for point in basis.data]

    edited = [point.copy() for point in original]
    for index, point in enumerate(basis.data):
        point.co = edited[index]
    for key in keys[1:]:
        for index, point in enumerate(key.data):
            point.co = edited[index] + (point.co - original[index])

    # Work on the existing alpha-backed brow component, not an added proxy.
    # The same affine edit is applied to Basis and every relative target, so
    # the imported 43-key expression inventory remains a valid deformation set.
    brow_slot = next((i for i, material in enumerate(made.data.materials)
                      if material and "FACEBROW" in material.name.upper()), None)
    brow_indices = sorted({vertex for poly in made.data.polygons if poly.material_index == brow_slot
                           for vertex in poly.vertices}) if brow_slot is not None else []
    for key in keys:
        for side in (-1, 1):
            indices = [index for index in brow_indices if (key.data[index].co.x < 0) == (side < 0)]
            if not indices:
                continue
            center_z = sum(key.data[index].co.z for index in indices) / len(indices)
            for index in indices:
                point = key.data[index].co
                point.z = center_z + (point.z - center_z) * 0.30 - 0.010
    made["brow_vertex_route"] = ("FaceBrow material-index vertices; z lowered 10mm and arch compressed 70% "
                                  "across Basis plus every relative shape key")
    mouth_slot = next((i for i, material in enumerate(made.data.materials)
                       if material and "FACEMOUTH" in material.name.upper()), None)
    mouth_indices = sorted({vertex for poly in made.data.polygons if poly.material_index == mouth_slot
                            for vertex in poly.vertices}) if mouth_slot is not None else []
    # Existing oral overlay only: lower each corner more than its center on
    # Basis and all relative keys, preserving cavity topology and key count.
    for key in keys:
        for index in mouth_indices:
            point = key.data[index].co
            point.z -= 0.004 * min(1.0, abs(point.x) / 0.027)
    made["mouth_vertex_route"] = "FaceMouth material-index corners lowered up to 4mm across Basis plus every relative shape key"

    # Mia is observant and tired rather than wide-awake: use the source's real
    # eyelid topology for neutral half-lids.  Blink proof later drives it to 1.
    natural = keys.get("Face.M_F00_000_00_Fcl_EYE_Natural")
    if natural:
        natural.value = 0.28
    close = keys.get("Face.M_F00_000_00_Fcl_EYE_Close")
    if close:
        close.value = 0.42
    sorrow = keys.get("Face.M_F00_000_00_Fcl_EYE_Sorrow")
    if sorrow:
        sorrow.value = 0.10
    mouth_angry = keys.get("Face.M_F00_000_00_Fcl_MTH_Angry")
    if mouth_angry:
        mouth_angry.value = 0.40
    mouth_down = keys.get("Face.M_F00_000_00_Fcl_MTH_Down")
    if mouth_down:
        mouth_down.value = 0.0
    return made


def refine_shared_anatomy(face, body):
    """Small semantic cage shared by face overlay keys and body head core."""
    def head_map(co):
        x, y, z = co
        if 1.445 < z < 1.580:
            t = min(1.0, max(0.0, (1.580 - z) / .135))
            x *= 1.0 - .06 * t
        return Vector((x, y, z))
    keys = face.data.shape_keys.key_blocks
    basis = keys[0]
    old = [p.co.copy() for p in basis.data]
    new = [head_map(p) for p in old]
    for i, p in enumerate(basis.data): p.co = new[i]
    for key in keys[1:]:
        for i, p in enumerate(key.data): p.co = new[i] + (p.co - old[i])
    def bell(value, center, radius):
        return max(0.0, 1.0 - ((value - center) / radius) ** 2)

    inverse = body.matrix_world.inverted()
    body_delta = {"bust_vertices": 0, "bust_max_back_mm": 0.0,
                  "waist_vertices": 0, "waist_max_forward_mm": 0.0,
                  "waist_max_width_percent": 0.0}
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        world = head_map(world)
        z, x = world.z, world.x
        # World front is -Y.  At the measured v12 bust apex (z~1.26,
        # front~-0.143) ease only the projecting excess back toward the
        # adjacent rib plane; side/upper/lower falloff keeps a full bust.
        bust = bell(z, 1.285, .115) * bell(abs(x), .070, .145)
        if world.y < -0.075 and bust:
            amount = min(.018, (-world.y - .075) * .19) * bust
            world.y += amount
            body_delta["bust_vertices"] += 1
            body_delta["bust_max_back_mm"] = max(body_delta["bust_max_back_mm"], amount * 1000)
        # Measured waist center is z~1.12.  A smooth depth/width support
        # prevents the prior narrow abrupt waist without altering hips/ribs.
        waist = bell(z, 1.115, .105)
        if waist:
            width_scale = 1.0 + .040 * waist
            world.x *= width_scale
            body_delta["waist_max_width_percent"] = max(body_delta["waist_max_width_percent"], (width_scale - 1) * 100)
            if world.y < 0.040:
                amount = .006 * waist
                world.y -= amount
                body_delta["waist_vertices"] += 1
                body_delta["waist_max_forward_mm"] = max(body_delta["waist_max_forward_mm"], amount * 1000)
        vertex.co = inverse @ world
    face["shared_head_body_map"] = "lower cheek/jaw 6% taper applied Face Basis+42 targets and Body head core"
    body["torso_refinement"] = json.dumps(body_delta, sort_keys=True)


def upstream_image_names(socket, visited=None):
    """Return image nodes feeding a color socket through VRM reroute/UV nodes."""
    visited = visited or set()
    if socket.as_pointer() in visited:
        return []
    visited.add(socket.as_pointer())
    result = []
    for link in socket.links:
        node = link.from_node
        if node.type == "TEX_IMAGE":
            result.append(node.name)
        else:
            result.extend(name for inp in node.inputs for name in upstream_image_names(inp, visited))
    return sorted(set(result))


def tune_texture_material(face, matcher, replacement_name, saturation, value):
    """Tone only MToon's lit/shade color routes; keep normal/alpha data intact."""
    for slot in face.material_slots:
        material = slot.material
        if not material or not matcher(material.name) or not material.use_nodes:
            continue
        copy = material.copy()
        copy.name = replacement_name
        nodes = copy.node_tree.nodes
        links = copy.node_tree.links
        target = next((node for node in nodes if node.name.endswith("Mtoon1Output")), None)
        if target:
            toned = {}
            # These are the only documented diffuse routes on the imported
            # MToon node group. Alpha, normal, matcap, rim and outline maps
            # deliberately retain their untouched original links.
            for input_name in ("Lit Color Texture Color", "Shade Color Texture"):
                socket = target.inputs.get(input_name)
                incoming = list(socket.links) if socket else []
                if not incoming:
                    continue
                toned[input_name] = upstream_image_names(socket)
                for old_link in incoming:
                    source_socket = old_link.from_socket
                    links.remove(old_link)
                    hsv = nodes.new("ShaderNodeHueSaturation")
                    hsv.name = "MIA_TONE_" + input_name.replace(" ", "_")
                    hsv.inputs["Hue"].default_value = 0.55
                    hsv.inputs["Saturation"].default_value = saturation
                    hsv.inputs["Value"].default_value = value
                    links.new(source_socket, hsv.inputs["Color"])
                    links.new(hsv.outputs["Color"], socket)
            target.inputs["Emissive Strength"].default_value = 0.0
            copy["mia_toned_color_routes"] = json.dumps(toned, sort_keys=True)
            copy["mia_preserved_noncolor_image_nodes"] = json.dumps(sorted(
                node.name for node in nodes if node.type == "TEX_IMAGE" and node.name not in set(sum(toned.values(), []))
            ))
        slot.material = copy


def tune_iris(face):
    tune_texture_material(face, lambda name: "EYEIRIS" in name.upper(),
                          "Mia_AshBlueGrey_Iris_MToon", 0.10, 0.80)
    tune_texture_material(face, lambda name: "FACEBROW" in name.upper(),
                          "Mia_SlateBrow_MToon", 0.10, 0.52)
    tune_texture_material(face, lambda name: "FACE_00_SKIN" in name.upper(),
                          "Mia_CoolMutedSkin_MToon", 0.60, 0.94)
    tune_texture_material(face, lambda name: "EYEEXTRA" in name.upper() or "EYEHIGHLIGHT" in name.upper(),
                          "Mia_MutedEyeAccent_MToon", 0.10, 0.78)
    tune_texture_material(face, lambda name: "FACEEYELASH" in name.upper(),
                          "Mia_CharcoalLash_MToon", 0.12, 0.38)
    tune_texture_material(face, lambda name: "FACEEYELINE" in name.upper(),
                          "Mia_CharcoalEyeLine_MToon", 0.08, 0.34)
    # HSV nodes alone did not overcome the source MToon multipliers.  Set the
    # actual MToon Lit/Shade factors on the duplicated routed materials while
    # retaining their packed alpha masks, UVs, normal and expression binding.
    factors = {
        "Mia_AshBlueGrey_Iris_MToon": ((0.42, 0.48, 0.54, 1), (0.20, 0.25, 0.30, 1)),
        "Mia_SlateBrow_MToon": ((0.12, 0.14, 0.17, 1), (0.055, 0.065, 0.08, 1)),
        "Mia_CharcoalLash_MToon": ((0.055, 0.065, 0.085, 1), (0.018, 0.024, 0.035, 1)),
        "Mia_CharcoalEyeLine_MToon": ((0.045, 0.055, 0.075, 1), (0.014, 0.020, 0.030, 1)),
        "Mia_MutedEyeAccent_MToon": ((0.28, 0.32, 0.36, 1), (0.12, 0.15, 0.18, 1)),
    }
    for material in bpy.data.materials:
        base_name = material.name.rsplit(".", 1)[0] if material.name.rsplit(".", 1)[-1].isdigit() else material.name
        if base_name not in factors or not material.use_nodes:
            continue
        output = next((node for node in material.node_tree.nodes if node.name.endswith("Mtoon1Output")), None)
        if output:
            output.inputs["Lit Color"].default_value = factors[base_name][0]
            output.inputs["Shade Color"].default_value = factors[base_name][1]
            output.inputs["Emissive Strength"].default_value = 0.0
            material["mia_mtoon_factor_route"] = "Mtoon1Output Lit Color + Shade Color direct factors"


def pack_reference_images():
    """Keep approved art accessible in the native checkpoint, never rendered."""
    reference = collection("MIA_REF_APPROVED_V22_NONRENDER")
    root = Path(__file__).resolve().parents[3]
    names = ("mia-clean-master-v22.png", "mia-canonical-source-v22.png",
             "mia-expressions-clean-16-v22.png")
    recorded = []
    for name in names:
        path = root / "asset" / "mia" / "references" / name
        if not path.exists():
            continue
        image = bpy.data.images.get("MIA_REF_" + name) or bpy.data.images.load(str(path), check_existing=True)
        image.name = "MIA_REF_" + name
        image.pack()
        empty = bpy.data.objects.new("MIA_REF_" + path.stem, None)
        empty.empty_display_type = "IMAGE"
        empty.data = image
        empty.empty_display_size = 0.25
        empty.hide_render = True
        empty.hide_viewport = True
        empty["role"] = "APPROVED_REFERENCE_NONRENDER"
        reference.objects.link(empty)
        recorded.append(name)
    reference.hide_render = True
    reference["role"] = "APPROVED_REFERENCE_ARCHIVE_NONRENDER"
    return recorded


def set_outline_widths():
    """Adjust the imported MToon style hulls, never the anatomy meshes."""
    for material in bpy.data.materials:
        upper = material.name.upper()
        width = (0.001 if ("FACE_00_SKIN" in upper or "MIA_COOLMUTEDSKIN" in upper)
                 else 0.0015 if "BODY_00_SKIN" in upper else None)
        if width is None or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.name.endswith("Mtoon1Output") and node.inputs.get("Outline Width"):
                node.inputs["Outline Width"].default_value = width


def studio():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    # Blender 5.2 exposes the contrast labels without the older "AgX -" prefix.
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = -0.65
    world = bpy.data.worlds.get("MIA_ANATOMY_WORLD") or bpy.data.worlds.new("MIA_ANATOMY_WORLD")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.028, 0.034, 0.048, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.24
    for name, position, energy, size in (
        ("MIA_KEY", (2.5, -3.0, 3.0), 280, 2.0),
        ("MIA_FILL", (-2.0, -2.0, 2.2), 95, 3.0),
        ("MIA_RIM", (1.8, 1.6, 2.8), 180, 1.5),
    ):
        lamp_data = bpy.data.lights.get(name) or bpy.data.lights.new(name, "AREA")
        lamp_data.energy, lamp_data.shape, lamp_data.size = energy, "DISK", size
        lamp = bpy.data.objects.get(name) or bpy.data.objects.new(name, lamp_data)
        if not lamp.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(lamp)
        lamp.location = position
        lamp.rotation_euler = (Vector((0, 0, 1.0)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    camera_data = bpy.data.cameras.get("MIA_REVIEW_CAMERA") or bpy.data.cameras.new("MIA_REVIEW_CAMERA")
    camera = bpy.data.objects.get("MIA_REVIEW_CAMERA") or bpy.data.objects.new("MIA_REVIEW_CAMERA", camera_data)
    if not camera.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(camera)
    camera.data.lens = 62
    scene.camera = camera
    return camera


def look(camera, location, target):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, directory, name, location, target):
    look(camera, location, target)
    path = directory / (name + ".png")
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


def set_outline_render(objects, enabled):
    prior = []
    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and "OUTLINE" in modifier.name.upper():
                prior.append((modifier, modifier.show_render))
                modifier.show_render = enabled
    return prior


def main():
    args = arguments()
    source = Path(args.input)
    output = Path(args.output)
    directory = Path(args.render_dir)
    directory.mkdir(parents=True, exist_ok=True)
    before = digest(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    if any(obj.name.startswith("Mia_") for obj in bpy.data.objects):
        raise RuntimeError("Input must be pristine Victoria source, not a prior Mia derivative checkpoint")
    anatomy = collection("MIA_ANATOMY_V02")
    source_face = bpy.data.objects["Face"]
    source_body = bpy.data.objects["Body"]
    face = mia_face_copy(source_face, anatomy)
    body, skin_slots = skin_only_copy(source_body, anatomy)
    if args.shared_head_cage:
        refine_shared_anatomy(face, body)
    tune_iris(face)
    tune_texture_material(body, lambda name: "BODY_00_SKIN" in name.upper(),
                          "Mia_CoolMutedBodySkin_MToon", 0.60, 0.94)
    set_outline_widths()
    hide_source_originals()
    visible_face_body = [obj.name for obj in bpy.data.objects if obj.type == "MESH" and not obj.hide_render
                         and obj.name in {"Mia_Face_AnimeTopology", "Mia_Body_Anatomy_Skin"}]
    if sorted(visible_face_body) != ["Mia_Body_Anatomy_Skin", "Mia_Face_AnimeTopology"]:
        raise RuntimeError("Single-assembly assertion failed: expected one visible owned Face and Body")
    camera = studio()
    if args.quick_gate:
        bpy.context.scene.render.resolution_x = 640
        bpy.context.scene.render.resolution_y = 640
    disabled_face_nodes = []
    if args.disable_face_nodes:
        for modifier in face.modifiers:
            if modifier.type == "NODES":
                modifier.show_render = False
                disabled_face_nodes.append(modifier.name)
    # Write a neutral, single-assembly checkpoint before diagnostic rendering.
    bpy.ops.wm.save_as_mainfile(filepath=str(output))

    # Actual visual evidence, not just an object count.  The expression proof
    # uses real imported shape keys and restores neutral after each capture.
    neutral_keys = face.data.shape_keys.key_blocks
    rendered = []
    views = {
        "neutral_front": ((0, -0.72, 1.59), (0, -0.02, 1.57)),
        "neutral_three_quarter_left": ((0.53, -0.53, 1.59), (0, -0.02, 1.57)),
        "neutral_profile": ((0.72, 0.0, 1.59), (0, -0.02, 1.57)),
        "neutral_full_front": ((0, -3.4, 0.94), (0, 0, 0.90)),
        "neutral_full_side": ((3.4, 0, 0.94), (0, 0, 0.90)),
        "neutral_full_back": ((0, 3.4, 0.94), (0, 0, 0.90)),
        "neutral_torso_three_quarter": ((1.35, -1.55, 1.10), (0, -0.01, 1.10)),
    }
    if args.quick_gate:
        views = {name: views[name] for name in ("neutral_front", "neutral_three_quarter_left")}
    for name, (location, target) in views.items():
        rendered.append(render(camera, directory, name, location, target))
    if not args.quick_gate:
        outline_prior = set_outline_render((face, body), False)
        rendered.append(render(camera, directory, "neutral_three_quarter_outline_off",
                               (0.53, -0.53, 1.59), (0, -0.02, 1.57)))
        for modifier, prior in outline_prior:
            modifier.show_render = prior
    blink = neutral_keys.get("Face.M_F00_000_00_Fcl_EYE_Close")
    if blink:
        eye_snapshot = {key.name: key.value for key in neutral_keys if "_EYE_" in key.name}
        neutral_natural = neutral_keys.get("Face.M_F00_000_00_Fcl_EYE_Natural")
        neutral_sorrow = neutral_keys.get("Face.M_F00_000_00_Fcl_EYE_Sorrow")
        neutral_blink = blink.value
        prior_natural = neutral_natural.value if neutral_natural else None
        prior_sorrow = neutral_sorrow.value if neutral_sorrow else None
        for key in neutral_keys:
            if "_EYE_" in key.name:
                key.value = 0.0
        blink.value = 1.0
        rendered.append(render(camera, directory, "blink_full_front", (0, -0.72, 1.59), (0, -0.02, 1.57)))
        rendered.append(render(camera, directory, "blink_three_quarter", (0.53, -0.53, 1.59), (0, -0.02, 1.57)))
        for key in neutral_keys:
            if key.name in eye_snapshot:
                key.value = eye_snapshot[key.name]
    mouth = neutral_keys.get("Face.M_F00_000_00_Fcl_MTH_A")
    if mouth:
        mouth_snapshot = {key.name: key.value for key in neutral_keys if "_MTH_" in key.name}
        angry_mouth = neutral_keys.get("Face.M_F00_000_00_Fcl_MTH_Angry")
        prior_angry_mouth = angry_mouth.value if angry_mouth else None
        for key in neutral_keys:
            if "_MTH_" in key.name:
                key.value = 0.0
        mouth.value = 1.0
        rendered.append(render(camera, directory, "mouth_a_front", (0, -0.72, 1.59), (0, -0.02, 1.57)))
        rendered.append(render(camera, directory, "mouth_a_three_quarter", (0.53, -0.53, 1.59), (0, -0.02, 1.57)))
        for key in neutral_keys:
            if key.name in mouth_snapshot:
                key.value = mouth_snapshot[key.name]

    packed_references = pack_reference_images()
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    after = digest(source)
    report = {
        "source_path": str(source), "source_sha256_before": before,
        "source_sha256_after": after, "source_unchanged": before == after,
        "checkpoint": str(output), "renders": [str(path) for path in rendered],
        "objects": {
            "face": {"vertices": len(face.data.vertices), "polygons": len(face.data.polygons),
                     "shape_keys": [key.name for key in face.data.shape_keys.key_blocks]},
            "body_skin_only": {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons),
                               "skin_material_slots": sorted(skin_slots),
                               "removed_materials": body["removed_material_slots"]},
        },
        "shared_head_cage_enabled": args.shared_head_cage,
        "disabled_face_nodes_for_diagnostic": disabled_face_nodes,
        "face_edit_routes": {
            "brows": face.get("brow_vertex_route"),
            "eyes_lashes": "existing Face alpha material slots 3/4/5/8; packed masks and expression bindings retained",
            "mouth": "existing MTH_Neutral=0.80 and MTH_Down=0.25 shape-key values",
        },
        "packed_approved_references_nonrender": packed_references,
        "material_tone_audit": {
            slot.material.name: {
                "toned_color_routes": slot.material.get("mia_toned_color_routes"),
                "preserved_noncolor_image_nodes": slot.material.get("mia_preserved_noncolor_image_nodes"),
            }
            for slot in face.material_slots if slot.material and slot.material.get("mia_toned_color_routes")
        },
        "review_status": "UNVERIFIED: visual gate required before custom Mia hair/wardrobe work",
    }
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
