"""Create a bounded, mesh-anchored face-look study from the hair-stage candidate."""

import hashlib
import json
import os
import shutil
import sys
import math
import argparse
from mathutils import Vector

import bpy


INPUT = None
OUTDIR = None
OUTBLEND = None
NEUTRAL_CHECKPOINT = None
FACE_NAME = "Mia_Face_AnimeTopology"
SKIN_SLOT = 7
MASK_NAME = "Mia_FaceLook_UnderEyeMask_v04"
SKIN_NAME = "Mia_CoolMutedSkin_FaceLook_v04"
MASK_IMAGE_NAME = "Mia_FaceLook_UnderEyeUVMask_v04"


def parse_cli():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Apply the frozen Mia v04 under-eye look prototype.")
    parser.add_argument("--input", required=True, help="Existing candidate .blend; never overwritten")
    parser.add_argument("--output", required=True, help="New .blend output path")
    parser.add_argument("--render-dir", required=True, help="Directory for proof PNGs and UV mask")
    parser.add_argument("--report", required=True, help="JSON report output path")
    parser.add_argument("--eye-preset", choices=("preserve", "tired"), default="preserve")
    return parser.parse_args(raw)


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def mesh_fingerprint(obj):
    mesh = obj.data
    h = hashlib.sha256()
    for vert in mesh.vertices:
        h.update(bytes(vert.co))
    uv = mesh.uv_layers.active
    if uv:
        for item in uv.data:
            h.update(bytes(item.uv))
    keys = obj.data.shape_keys.key_blocks if obj.data.shape_keys else []
    for key in keys:
        h.update(key.name.encode("utf-8"))
        for point in key.data:
            h.update(bytes(point.co))
    return h.hexdigest(), len(keys), len(mesh.vertices), len(uv.data) if uv else 0


def vec_bounds(points):
    return [[min(p[i] for p in points), max(p[i] for p in points)] for i in range(3)]


def find_material_vertices(obj, material_index):
    return sorted({index for poly in obj.data.polygons if poly.material_index == material_index for index in poly.vertices})


def eye_clusters(obj):
    # Actual EyeWhite and charcoal-eyeline surface vertices drive each side.
    indices = set(find_material_vertices(obj, 1)) | set(find_material_vertices(obj, 2))
    world = {i: obj.matrix_world @ obj.data.vertices[i].co for i in indices}
    left = [point for point in world.values() if point.x < 0.0]
    right = [point for point in world.values() if point.x >= 0.0]
    result = []
    for points in (left, right):
        if not points:
            raise RuntimeError("Could not derive both eye regions from EyeWhite/Eyeline materials")
        bounds = vec_bounds(points)
        result.append({
            "center": Vector([(bounds[i][0] + bounds[i][1]) * 0.5 for i in range(3)]),
            "width": max(bounds[0][1] - bounds[0][0], 0.001),
            "height": max(bounds[2][1] - bounds[2][0], 0.001),
            "bounds": bounds,
        })
    return result


def eye_white_lower_contours(obj):
    """Lower eyelid contours from EyeWhite only; Eyeline tails must not drive fatigue."""
    indices = find_material_vertices(obj, 1)
    points = [obj.matrix_world @ obj.data.vertices[i].co for i in indices]
    contours = []
    for side in (-1, 1):
        side_points = [point for point in points if point.x * side > 0]
        bounds = vec_bounds(side_points)
        center_x = (bounds[0][0] + bounds[0][1]) * 0.5
        width = bounds[0][1] - bounds[0][0]
        samples = []
        for step in range(17):
            x = bounds[0][0] + width * step / 16.0
            nearby = [point.z for point in side_points if abs(point.x - x) <= width * 0.075]
            if not nearby:
                nearby = [point.z for point in side_points]
            samples.append((x, min(nearby)))
        contours.append({"bounds": bounds, "center_x": center_x, "width": width, "samples": samples})
    return contours


def contour_lower_z(contour, x):
    samples = contour["samples"]
    if x <= samples[0][0]:
        return samples[0][1]
    if x >= samples[-1][0]:
        return samples[-1][1]
    for index in range(1, len(samples)):
        x1, z1 = samples[index]
        x0, z0 = samples[index - 1]
        if x <= x1:
            factor = (x - x0) / max(x1 - x0, 1e-8)
            return z0 * (1.0 - factor) + z1 * factor
    return samples[-1][1]


def uv_mask_strength(world, contours):
    for contour in contours:
        horizontal = abs(world.x - contour["center_x"]) / (contour["width"] * 0.56)
        if horizontal >= 1.0:
            continue
        # Continuous quadratic lower-lid curve from actual EyeWhite bounds, not noisy vertex minima.
        rim_z = contour["bounds"][2][0] + 0.008 * horizontal * horizontal
        below = rim_z - world.z
        if 0.0 < below < 0.010:
            vertical = below / 0.010
            return (1.0 - horizontal ** 2.0) * math.sin(math.pi * vertical) * 0.36
    return 0.0


def bake_uv_mask(obj, contours):
    """Rasterize a contour evaluated from actual world positions over actual source UV triangles."""
    width = height = 1024
    image = bpy.data.images.get(MASK_IMAGE_NAME)
    if image:
        bpy.data.images.remove(image)
    image = bpy.data.images.new(MASK_IMAGE_NAME, width, height, alpha=True, float_buffer=False)
    pixels = [0.0] * (width * height * 4)
    uv = obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        if poly.material_index != SKIN_SLOT or len(poly.loop_indices) < 3:
            continue
        loops = list(poly.loop_indices)
        for tri in range(1, len(loops) - 1):
            loop_ids = (loops[0], loops[tri], loops[tri + 1])
            coords = [uv[i].uv[:] for i in loop_ids]
            positions = [obj.matrix_world @ obj.data.vertices[obj.data.loops[i].vertex_index].co for i in loop_ids]
            min_x = max(0, int(math.floor(min(p[0] for p in coords) * width)))
            max_x = min(width - 1, int(math.ceil(max(p[0] for p in coords) * width)))
            min_y = max(0, int(math.floor(min(p[1] for p in coords) * height)))
            max_y = min(height - 1, int(math.ceil(max(p[1] for p in coords) * height)))
            ax, ay = coords[0]; bx, by = coords[1]; cx, cy = coords[2]
            denom = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(denom) < 1e-10:
                continue
            for py in range(min_y, max_y + 1):
                v = (py + 0.5) / height
                for px in range(min_x, max_x + 1):
                    u = (px + 0.5) / width
                    w0 = ((by - cy) * (u - cx) + (cx - bx) * (v - cy)) / denom
                    w1 = ((cy - ay) * (u - cx) + (ax - cx) * (v - cy)) / denom
                    w2 = 1.0 - w0 - w1
                    if w0 < 0.0 or w1 < 0.0 or w2 < 0.0:
                        continue
                    strength = uv_mask_strength(positions[0] * w0 + positions[1] * w1 + positions[2] * w2, contours)
                    if strength > 0.0:
                        offset = (py * width + px) * 4
                        pixels[offset:offset + 4] = (0.62, 0.53, 0.67, strength)
    # A small UV-space blur removes triangle stair-steps while retaining the contour-derived placement.
    alpha = [pixels[offset + 3] for offset in range(0, len(pixels), 4)]
    radius = 5
    for axis in (0, 1):
        softened = [0.0] * len(alpha)
        for outer in range(height if axis == 0 else width):
            values = [alpha[outer * width + inner] if axis == 0 else alpha[inner * width + outer] for inner in range(width if axis == 0 else height)]
            prefix = [0.0]
            for value in values:
                prefix.append(prefix[-1] + value)
            for inner in range(len(values)):
                lo, hi = max(0, inner - radius), min(len(values), inner + radius + 1)
                value = (prefix[hi] - prefix[lo]) / (hi - lo)
                softened[outer * width + inner if axis == 0 else inner * width + outer] = value
        alpha = softened
    for pixel_index, value in enumerate(alpha):
        pixels[pixel_index * 4 + 3] = value
    image.pixels.foreach_set(pixels)
    image.filepath_raw = artifact_path("_under_eye_uv_mask.png")
    image.file_format = "PNG"
    image.save()
    return image, [pixels[i + 3] for i in range(0, len(pixels), 4)]


def add_under_eye_attribute(obj, eyes):
    mesh = obj.data
    old = mesh.color_attributes.get(MASK_NAME)
    if old:
        mesh.color_attributes.remove(old)
    attr = mesh.color_attributes.new(MASK_NAME, "BYTE_COLOR", "POINT")
    skin_indices = find_material_vertices(obj, SKIN_SLOT)
    affected = []
    for index, point in enumerate(attr.data):
        point.color = (1.0, 1.0, 1.0, 0.0)
    # The mask stays on vertex data, so it deforms with every existing shape key.
    for index in skin_indices:
        pos = obj.matrix_world @ mesh.vertices[index].co
        strength = 0.0
        for eye in eyes:
            delta = pos - eye["center"]
            horizontal = abs(delta.x) / (eye["width"] * 0.62)
            lower_eye = eye["bounds"][2][0]
            below_lower_lid = lower_eye - pos.z
            # Constrain to a narrow strip under the actual lower eye bound and eye-front surface.
            if horizontal < 1.0 and 0.002 < below_lower_lid < 0.034 and abs(delta.y) < eye["width"] * 0.30:
                vertical = (below_lower_lid - 0.002) / 0.032
                strength = max(strength, (1.0 - horizontal ** 1.8) * (1.0 - abs(vertical - 0.48) ** 1.35))
        alpha = min(0.60, strength * 0.60)
        if alpha > 0.01:
            attr.data[index].color = (0.67, 0.57, 0.69, alpha)
            affected.append(index)
    if not affected:
        raise RuntimeError("Derived eye bounds selected no skin vertices; refusing a guessed UV patch")
    points = [obj.matrix_world @ mesh.vertices[i].co for i in affected]
    return affected, vec_bounds(points)


def attach_mask_to_skin(face, mask_image):
    original = face.data.materials[SKIN_SLOT]
    clone = original.copy()
    clone.name = SKIN_NAME
    clone["LOOK_PROTOTYPE_STATUS"] = "LOOK_PROTOTYPE_UNVERIFIED"
    clone["FACELOOK_MASK"] = MASK_NAME
    tree = clone.node_tree
    nodes, links = tree.nodes, tree.links
    uv = nodes.new("ShaderNodeTexImage")
    uv.name = "MIA_FACELOOK_UVMask"
    uv.image = mask_image
    tint = nodes.new("ShaderNodeMixRGB")
    tint.name = "MIA_FACELOOK_UnderEyeTint_Multiply"
    tint.blend_type = "MULTIPLY"
    tint.inputs[2].default_value = (0.55, 0.49, 0.62, 1.0)
    tint.label = "UV contour mask: natural muted violet-grey fatigue"
    links.new(uv.outputs["Alpha"], tint.inputs[0])
    base = nodes.get("Mtoon1BaseColorTexture.Image")
    if not base:
        raise RuntimeError("Skin MToon base texture node missing")
    links.new(nodes["Mtoon1BaseColorTexture.Uv"].outputs["UV Vector"], uv.inputs["Vector"])
    links.new(base.outputs["Color"], tint.inputs[1])
    for target_name, socket_name in (("Reroute.001", "Input"), ("Mtoon1Material.CompatibleShader", "Base Color")):
        target = nodes.get(target_name)
        socket = target.inputs[socket_name]
        for link in list(socket.links):
            links.remove(link)
        links.new(tint.outputs["Color"], socket)
    # The MToon lit route receives Reroute.001 through its existing hue node; alpha/normal routes remain untouched.
    face.data.materials[SKIN_SLOT] = clone
    return original, clone, [
        (link.from_node.name, link.from_socket.name, link.to_node.name, link.to_socket.name)
        for link in tree.links if link.from_node in (uv, tint) or link.to_node in (uv, tint)
    ]


def snapshot_values(face):
    return {key.name: float(key.value) for key in face.data.shape_keys.key_blocks}


def restore_values(face, values):
    for key in face.data.shape_keys.key_blocks:
        key.value = values[key.name]


def zero_channel(face, token):
    for key in face.data.shape_keys.key_blocks:
        if token in key.name:
            key.value = 0.0


def set_key(face, fragment, value):
    matches = [key for key in face.data.shape_keys.key_blocks if key.name.endswith(fragment)]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one key for %s, got %s" % (fragment, len(matches)))
    matches[0].value = value
    return matches[0].name


def ensure_close_camera(face):
    scene = bpy.context.scene
    cam_data = bpy.data.cameras.get("MIA_FACELOOK_CAMERA") or bpy.data.cameras.new("MIA_FACELOOK_CAMERA")
    cam = bpy.data.objects.get("MIA_FACELOOK_CAMERA") or bpy.data.objects.new("MIA_FACELOOK_CAMERA", cam_data)
    if cam.name not in scene.collection.objects:
        scene.collection.objects.link(cam)
    points = [face.matrix_world @ vert.co for vert in face.data.vertices]
    bounds = vec_bounds(points)
    target = Vector((0.0, (bounds[1][0] + bounds[1][1]) * 0.5, 1.58))
    width = bounds[0][1] - bounds[0][0]
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 0.30
    scene.camera = cam
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    def aim(location):
        cam.location = location
        cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    aim(target + Vector((0.0, -width * 3.0, 0.0)))
    return cam, target, width, aim


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def artifact_path(suffix):
    return os.path.join(OUTDIR, os.path.splitext(os.path.basename(OUTBLEND))[0] + suffix)


def render_mask_debug(face, mask_image, path):
    """Render only the actual face's vertex-mask alpha as emission, then restore materials."""
    scene = bpy.context.scene
    hidden = {obj.name: obj.hide_render for obj in scene.objects}
    for obj in scene.objects:
        obj.hide_render = obj != face
    debug = bpy.data.materials.new("MIA_FACELOOK_MASK_DEBUG_v02")
    debug.use_nodes = True
    nodes, links = debug.node_tree.nodes, debug.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new("ShaderNodeOutputMaterial")
    attr = nodes.new("ShaderNodeTexImage")
    attr.image = mask_image
    tex_uv = nodes.new("ShaderNodeUVMap")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.01
    ramp.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    ramp.color_ramp.elements[1].position = 0.60
    ramp.color_ramp.elements[1].color = (0.55, 0.12, 0.70, 1.0)
    emission = nodes.new("ShaderNodeEmission")
    links.new(tex_uv.outputs["UV"], attr.inputs["Vector"])
    links.new(attr.outputs["Alpha"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], out.inputs["Surface"])
    slots = [slot.material for slot in face.material_slots]
    for index in range(len(face.data.materials)):
        face.data.materials[index] = debug
    render(path)
    for index, material in enumerate(slots):
        face.data.materials[index] = material
    for obj in scene.objects:
        obj.hide_render = hidden[obj.name]
    bpy.data.materials.remove(debug)


def main():
    global INPUT, OUTDIR, OUTBLEND, NEUTRAL_CHECKPOINT
    options = parse_cli()
    INPUT = os.path.abspath(options.input)
    OUTBLEND = os.path.abspath(options.output)
    OUTDIR = os.path.abspath(options.render_dir)
    NEUTRAL_CHECKPOINT = os.path.join(OUTDIR, os.path.splitext(os.path.basename(OUTBLEND))[0] + "_neutral_checkpoint.blend")
    if os.path.normcase(INPUT) == os.path.normcase(OUTBLEND):
        raise RuntimeError("--output must differ from --input; source candidates are never overwritten")
    if bpy.data.filepath != INPUT:
        bpy.ops.wm.open_mainfile(filepath=INPUT)
    os.makedirs(OUTDIR, exist_ok=True)
    face = bpy.data.objects.get(FACE_NAME)
    if not face:
        raise RuntimeError("Canonical face object missing")
    if len([o for o in bpy.context.scene.objects if o.visible_get() and o.name == FACE_NAME]) != 1:
        raise RuntimeError("Expected exactly one visible canonical face owner")
    bodies = [o for o in bpy.context.scene.objects if o.visible_get() and o.type == "MESH" and "body" in o.name.lower()]
    if len(bodies) != 1:
        raise RuntimeError("Expected exactly one visible canonical body owner, got %s" % len(bodies))
    skin = face.data.materials[SKIN_SLOT]
    if skin and (skin.get("LOOK_PROTOTYPE_STATUS") or (skin.use_nodes and skin.node_tree.nodes.get("MIA_FACELOOK_UVMask"))):
        raise RuntimeError("Input already has a face-look prototype; refusing to stack masks")
    input_sha = sha_file(INPUT)
    before_fp = mesh_fingerprint(face)
    initial_values = snapshot_values(face)
    if options.eye_preset == "tired":
        zero_channel(face, "Fcl_EYE_")
        set_key(face, "Fcl_EYE_Close", 0.60)
        set_key(face, "Fcl_EYE_Natural", 0.0)
        set_key(face, "Fcl_EYE_Sorrow", 0.10)
    selected_values = snapshot_values(face)
    # A neutral checkpoint is saved before any diagnostics or material changes.
    bpy.ops.wm.save_as_mainfile(filepath=NEUTRAL_CHECKPOINT)
    cam, target, width, aim = ensure_close_camera(face)
    render(artifact_path("_BEFORE_front.png"))
    aim(target + Vector((width * 0.62, -width * 2.93, width * 0.04)))
    render(artifact_path("_BEFORE_3q.png"))
    eyes = eye_clusters(face)
    contours = eye_white_lower_contours(face)
    mask_image, alphas = bake_uv_mask(face, contours)
    render_mask_debug(face, mask_image, artifact_path("_MASK_DEBUG_emission.png"))
    original, clone, links = attach_mask_to_skin(face, mask_image)
    # Neutral comparisons retain the source's actual loaded expression dictionary.
    restore_values(face, selected_values)
    aim(target + Vector((0.0, -width * 3.0, 0.0)))
    render(artifact_path("_AFTER_front.png"))
    aim(target + Vector((width * 0.62, -width * 2.93, width * 0.04)))
    render(artifact_path("_AFTER_3q.png"))
    proofs = [("neutral", []), ("blink", [("Fcl_EYE_Close", 1.0)]), ("mouth_A", [("Fcl_MTH_A", 1.0)]), ("subtle_frown", [("Fcl_MTH_Down", 0.35)])]
    expressions = {}
    for label, values in proofs:
        restore_values(face, selected_values)
        channel = "Fcl_EYE_" if label == "blink" else "Fcl_MTH_" if values else None
        if channel:
            zero_channel(face, channel)
        expressions[label] = {}
        for fragment, value in values:
            expressions[label][set_key(face, fragment, value)] = value
        aim(target + Vector((0.0, -width * 3.0, 0.0)))
        render(artifact_path("_%s_front.png" % label))
        aim(target + Vector((width * 0.62, -width * 2.93, width * 0.04)))
        render(artifact_path("_%s_3q.png" % label))
    restore_values(face, selected_values)
    if snapshot_values(face) != selected_values:
        raise RuntimeError("Shape-key values were not restored to the selected neutral dictionary")
    after_fp = mesh_fingerprint(face)
    if before_fp != after_fp:
        raise RuntimeError("Geometry, UV, or shape-key fingerprint changed; refusing output")
    bpy.ops.wm.save_as_mainfile(filepath=OUTBLEND)
    report = {
        "status": "LOOK_PROTOTYPE_UNVERIFIED",
        "input": INPUT,
        "input_native_sha256_before_after": [input_sha, sha_file(INPUT)],
        "output": OUTBLEND,
        "neutral_checkpoint_before_diagnostics": NEUTRAL_CHECKPOINT,
        "canonical_face": FACE_NAME,
        "geometry_uv_all_shape_key_fingerprint_before_after": [before_fp[0], after_fp[0]],
        "shape_key_count": before_fp[1], "vertex_count": before_fp[2], "uv_corner_count": before_fp[3],
        "skin_material": {"source_archive_unchanged": original.name, "clone_attached_slot": SKIN_SLOT, "clone": clone.name, "active_mask_links": links},
        "mask": {"image": artifact_path("_under_eye_uv_mask.png"), "derived_from": "actual Skin UV triangles + barycentric world positions + smooth quadratic from EyeWhite lower bounds", "eye_white_lower_contours": [item["samples"] for item in contours], "eye_bounds_actual_material_slots_1_2": [e["bounds"] for e in eyes], "world_vertical_band_below_rim_m": [0.0, 0.010], "alpha_max": max(alphas), "alpha_mean_pixels": sum(alphas) / len(alphas), "alpha_nonzero_over_0_1_count": sum(value > 0.1 for value in alphas), "debug_emission_preview": os.path.basename(artifact_path("_MASK_DEBUG_emission.png"))},
        "eye_preset": options.eye_preset, "original_source_expression_values": initial_values, "selected_neutral_expression_values": selected_values, "proof_expression_keys": expressions,
        "note": "The UV mask is rasterized from actual face skin triangles and therefore follows the mesh UV deformation; this study does not alter facial proportions or rig coordinates."
    }
    with open(os.path.abspath(options.report), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    shutil.copy2(os.path.join(os.path.dirname(__file__), "apply_mia_face_look.py"), os.path.join(OUTDIR, "apply_mia_face_look.py"))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
