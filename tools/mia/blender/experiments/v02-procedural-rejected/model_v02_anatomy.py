#!/usr/bin/env python3
"""Build the face/body-only checkpoint for the Mia v02 authoring master.

The script opens the clean foundation, creates an independent checkpoint, and
uses a retained shape-key basis for the actual body/head sculpt.  It does not
read v45 and deliberately leaves Hair, Garments, Bag, and Hardware empty.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--inventory", required=True)
    return parser.parse_args(values)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def material(name, color, roughness=0.6):
    item = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    item.use_nodes = True
    bsdf = item.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = roughness
    return item


def set_material(obj, item):
    obj.data.materials.clear()
    obj.data.materials.append(item)


def assign_eye_surface_materials(eye, sclera, iris, pupil):
    """Assign sclera/iris/pupil zones on the retained eye mesh itself."""
    eye.data.materials.clear()
    for item in (sclera, iris, pupil):
        eye.data.materials.append(item)
    center = eye.matrix_world.translation
    for polygon in eye.data.polygons:
        point = eye.matrix_world @ polygon.center
        radius = ((point.x - center.x) ** 2 + (point.z - center.z) ** 2) ** 0.5
        front_facing = point.y < center.y - 0.018
        if front_facing and radius < 0.007:
            polygon.material_index = 2
        elif front_facing and radius < 0.016:
            polygon.material_index = 1
        else:
            polygon.material_index = 0


def world_vertex(obj, co):
    return obj.matrix_world @ co


def deform_world(point):
    """Shared smooth field for skin and the already seated eye meshes."""
    x, y, z = point
    ax = abs(x)
    result = Vector(point)
    if 1.30 < z < 1.69:
        # Keep the original broad upper-cheek/skull width. Mia's likeness
        # comes from a shorter tapered lower third, not a globally narrowed
        # head that turns the base into an elongated silhouette.
        result.z = 1.47 + (result.z - 1.47) * 0.93
        face = max(0.0, 1.0 - abs(z - 1.49) / 0.20)
        jaw = math.exp(-((z - 1.435) / 0.060) ** 2)
        result.x *= (1.0 - 0.025 * face - 0.26 * jaw)
        # Landmark-controlled lower-third compression: bring the retained
        # mouth/chin region upward toward the eye line instead of globally
        # shrinking the skull or cutting a face ROI.
        lower_face = math.exp(-((z - 1.425) / 0.060) ** 2) * math.exp(-((y + 0.055) / 0.11) ** 2)
        result.z += 0.032 * lower_face
        nose = math.exp(-((x / 0.045) ** 2 + ((z - 1.49) / 0.045) ** 2 + ((y + 0.105) / 0.035) ** 2))
        lips = math.exp(-((x / 0.060) ** 2 + ((z - 1.435) / 0.030) ** 2 + ((y + 0.105) / 0.035) ** 2))
        chin = math.exp(-((x / 0.070) ** 2 + ((z - 1.405) / 0.040) ** 2 + ((y + 0.095) / 0.045) ** 2))
        result.x *= 1.0 - 0.35 * nose - 0.15 * lips
        result.y += 0.086 * nose + 0.068 * lips + 0.055 * chin
        for eye_x in (-0.049, 0.049):
            socket = math.exp(-(((x - eye_x) / 0.060) ** 2 + ((z - 1.524) / 0.050) ** 2 + ((y + 0.052) / 0.060) ** 2))
            result.z = 1.524 + (result.z - 1.524) * (1.0 - 0.55 * socket)
            result.y -= 0.006 * socket
        ear = math.exp(-(((ax - 0.145) / 0.050) ** 2 + ((z - 1.515) / 0.075) ** 2))
        result.x -= math.copysign(0.030 * ear, x)
    neck = math.exp(-((z - 1.27) / 0.105) ** 2)
    result.x *= 1.0 - 0.10 * neck
    shoulder = math.exp(-((z - 1.16) / 0.135) ** 2) * min(1.0, ax / 0.16)
    result.x *= 1.0 - 0.055 * shoulder
    # Two supported breast lobes around z~1.2, with no center-abdomen proxy.
    chest_z = math.exp(-((z - 1.20) / 0.10) ** 2)
    lobes = math.exp(-((abs(x) - 0.075) / 0.070) ** 2)
    if y < 0.045:
        result.y -= 0.040 * chest_z * lobes
    waist = math.exp(-((z - 1.04) / 0.10) ** 2)
    result.x *= 1.0 - 0.070 * waist
    result.y *= 1.0 - 0.025 * waist
    hip = math.exp(-((z - 0.91) / 0.13) ** 2)
    result.x *= 1.0 + 0.040 * hip
    result.y *= 1.0 + 0.022 * hip
    return result


def sculpt_with_shared_field(obj, basis_name, sculpt_name):
    basis = obj.shape_key_add(name=basis_name, from_mix=False)
    sculpt = obj.shape_key_add(name=sculpt_name, from_mix=False)
    sculpt.value = 1.0
    inverse = obj.matrix_world.inverted()
    for index, point in enumerate(basis.data):
        sculpt.data[index].co = inverse @ deform_world(world_vertex(obj, point.co))
    return len(basis.data)


def sculpt_body(body):
    """Shape the retained basis into an adult, narrow-faced Mia proportion."""
    return sculpt_with_shared_field(body, "Foundation_Basis", "Mia_FaceBody_Sculpt_v02")
    basis = body.shape_key_add(name="Foundation_Basis", from_mix=False)
    sculpt = body.shape_key_add(name="Mia_FaceBody_Sculpt_v02", from_mix=False)
    sculpt.value = 1.0
    inverse = body.matrix_world.inverted()
    original = [Vector(point.co) for point in basis.data]

    for index, source_local in enumerate(original):
        point = world_vertex(body, source_local)
        x, y, z = point.x, point.y, point.z
        ax = abs(x)
        changed = point.copy()

        # Face: remove the base's childlike breadth without clipping the full
        # head. The falloff keeps ears and skull volume continuous.
        if 1.30 < z < 1.69:
            # Compress the generic doll head into a less childlike adult anime
            # head, retaining every surface and the complete forehead.
            changed.z = 1.47 + (changed.z - 1.47) * 0.88
            changed.x *= 0.90
            face_weight = max(0.0, 1.0 - abs(z - 1.49) / 0.20)
            jaw_weight = max(0.0, 1.0 - abs(z - 1.36) / 0.12)
            changed.x *= 1.0 - 0.12 * face_weight - 0.09 * jaw_weight
            if z < 1.42:
                changed.x *= 0.94
            # Front-face support: a little less projecting nose/lips, but no
            # deletion and no front-projected texture.
            if y < -0.02 and 1.40 < z < 1.57 and ax < 0.09:
                changed.y += 0.018 * (1.0 - ax / 0.09) * (1.0 - abs(z - 1.49) / 0.09)
            # Gentle cheek/under-eye support gives the sleepy expression
            # actual side volume rather than painted shading.
            if y < -0.035 and 1.45 < z < 1.55 and 0.045 < ax < 0.16:
                changed.y -= 0.010 * (1.0 - abs(z - 1.50) / 0.05)

        # Keep the original eyelid rings intact but make their openings more
        # almond-shaped.  The falloff is continuous in all directions so the
        # socket does not get an obvious rectangular edit seam.
        for eye_x in (-0.049, 0.049):
            socket = math.exp(-(((x - eye_x) / 0.060) ** 2 + ((z - 1.524) / 0.050) ** 2 + ((y + 0.052) / 0.060) ** 2))
            if socket > 0.01:
                changed.z = 1.524 + (changed.z - 1.524) * (1.0 - 0.24 * socket)
                changed.y -= 0.006 * socket

        # Reduce the generic large ear projection while retaining a complete
        # ear surface and a soft jaw-to-ear transition.
        ear = math.exp(-(((ax - 0.145) / 0.050) ** 2 + ((z - 1.515) / 0.075) ** 2))
        if ear > 0.02:
            changed.x -= math.copysign(0.030 * ear, x)

        # Neck is longer/slenderer; shoulder width is reduced while retaining
        # a physically continuous torso for later open cardigan/crop coverage.
        neck = math.exp(-((z - 1.27) / 0.105) ** 2)
        changed.x *= 1.0 - 0.10 * neck
        shoulder = math.exp(-((z - 1.16) / 0.135) ** 2) * min(1.0, ax / 0.16)
        changed.x *= 1.0 - 0.055 * shoulder

        # Adult torso silhouette: modestly narrower waist plus supported
        # chest and hip volumes. This acts on body vertices, not proxy spheres.
        chest = math.exp(-((z - 1.08) / 0.14) ** 2) * math.exp(-(x / 0.21) ** 2)
        if y < 0.045:
            changed.y -= 0.038 * chest
        changed.x *= 1.0 - 0.018 * chest
        waist = math.exp(-((z - 0.84) / 0.12) ** 2)
        changed.x *= 1.0 - 0.070 * waist
        changed.y *= 1.0 - 0.025 * waist
        hip = math.exp(-((z - 0.66) / 0.17) ** 2)
        changed.x *= 1.0 + 0.040 * hip
        changed.y *= 1.0 + 0.022 * hip

        # Subtle leg elongation below hip, preserving feet on the floor.
        if 0.20 < z < 0.58:
            changed.z += 0.018 * ((z - 0.20) / 0.38)
        sculpt.data[index].co = inverse @ changed

    body["role"] = "complete_mia_anatomy_master"
    body["topology_policy"] = "Foundation_Basis retained; sculpt shape key moves vertices only; no face/body deletion"
    return len(original)


def add_eye_lids(collection, center, side, lid_material):
    """Create thin, anatomically seated upper/lower lid accent curves.

    They sit on the existing eyelid region as small sculpt guides, never replace
    the existing eye objects with free floating spheres.
    """
    for label, z_offset, arc_scale in (("Upper", 0.016, 1.0), ("Lower", -0.012, 0.72)):
        curve = bpy.data.curves.new("Mia_%sLid_%s" % (label, side), "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.0022 if label == "Upper" else 0.0014
        curve.bevel_resolution = 3
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(2)
        direction = -1 if side == "L" else 1
        points = ((-0.050, 0.0), (0.0, z_offset), (0.050, 0.0))
        for bezier, (horizontal, vertical) in zip(spline.bezier_points, points):
            bezier.co = (center.x + direction * horizontal, center.y - 0.047, center.z + vertical * arc_scale)
            bezier.handle_left_type = "AUTO"
            bezier.handle_right_type = "AUTO"
        obj = bpy.data.objects.new(curve.name, curve)
        collection.objects.link(obj)
        curve.materials.append(lid_material)
        obj["role"] = "eyelid_accent_on_existing_anatomy"


def add_mouth(collection, center, lip_material):
    curve = bpy.data.curves.new("Mia_NeutralMouth", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = 0.0018
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(2)
    for point, offset in zip(spline.bezier_points, ((-0.026, 0.0), (0.0, -0.004), (0.026, 0.0))):
        point.co = (center.x + offset[0], center.y - 0.057, center.z + offset[1])
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new("Mia_NeutralMouth", curve)
    collection.objects.link(obj)
    curve.materials.append(lip_material)
    obj["role"] = "neutral_expression_guide"


def add_scene_lights(collection):
    for name, position, energy, size in (
        ("Mia_Key", (2.4, -3.2, 3.0), 650, 3.5),
        ("Mia_Fill", (-2.0, -2.0, 2.2), 280, 3.0),
        ("Mia_Rim", (1.6, 2.2, 2.7), 480, 2.8),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        obj.location = position
        obj.rotation_euler = (Vector((0, 0, 1.0)) - obj.location).to_track_quat("-Z", "Y").to_euler()
        collection.objects.link(obj)


def main():
    args = parse_args()
    source = Path(args.input).resolve()
    output = Path(args.output).resolve()
    inventory_path = Path(args.inventory).resolve()
    before = sha256(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    body = bpy.data.objects.get("BodyHead_Master")
    if body is None:
        raise RuntimeError("Foundation has no BodyHead_Master")
    anatomy = bpy.data.collections.get("Anatomy")
    if anatomy is None:
        raise RuntimeError("Foundation has no Anatomy collection")
    details = bpy.data.collections.get("FaceDetails") or bpy.data.collections.new("FaceDetails")
    if details.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(details)
    lights = bpy.data.collections.get("PresentationLights") or bpy.data.collections.new("PresentationLights")
    if lights.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(lights)
    vertices = sculpt_body(body)
    body["role"] = "complete_mia_anatomy_master"
    body["topology_policy"] = "Foundation basis retained; shared world-space sculpt moves complete body and eye vertices without deletion"
    for polygon in body.data.polygons:
        polygon.use_smooth = True
    subdivision = body.modifiers.get("Mia_PreviewSubdivision") or body.modifiers.new("Mia_PreviewSubdivision", "SUBSURF")
    subdivision.levels = 1
    subdivision.render_levels = 1
    skin = material("Mia_Skin_Neutral", (0.73, 0.53, 0.49, 1.0), 0.72)
    set_material(body, skin)
    eye_items = [obj for obj in anatomy.objects if obj.name.startswith("Eyes_")]
    sclera = material("Mia_EyeSclera", (0.67, 0.72, 0.70, 1.0), 0.42)
    iris = material("Mia_Iris_DesaturatedGrey", (0.20, 0.31, 0.33, 1.0), 0.35)
    pupil = material("Mia_EyePupil", (0.025, 0.035, 0.040, 1.0), 0.3)
    for eye in eye_items:
        sculpt_with_shared_field(eye, "Foundation_EyeBasis", "Mia_EyeSeating_Sculpt_v02")
        assign_eye_surface_materials(eye, sclera, iris, pupil)
        for polygon in eye.data.polygons:
            polygon.use_smooth = True
        eye["role"] = "seated_existing_eye_geometry"
    bpy.context.view_layer.update()
    centers = sorted((eye.matrix_world.translation for eye in eye_items), key=lambda p: p.x)
    if len(centers) != 2:
        raise RuntimeError("Expected exactly two foundation eye objects")
    # The generic eye mesh remains seated in the native eyelid topology.  Do
    # not fake sleepy lids with floating line meshes; the later face pass will
    # refine the retained eyelid loops and expression shape keys.
    for eye in eye_items:
        # They are parented to the body. Leave the verified local seating
        # intact; the face sculpt intentionally keeps the eye region close to
        # its source position until a proper eyelid-loop pass is made.
        eye["seating_policy"] = "preserved foundation local transform; no floating replacement eye"
    add_scene_lights(lights)
    if bpy.context.scene.world is None:
        bpy.context.scene.world = bpy.data.worlds.new("Mia_Anatomy_World")
    bpy.context.scene.world.color = (0.035, 0.042, 0.055)
    bpy.context.scene["mia_stage"] = "ANATOMY_ONLY"
    bpy.context.scene["mia_stage_status"] = "READY_FOR_HUMAN_MULTIVIEW_REVIEW"
    bpy.context.scene["mia_not_started"] = "Hair, Garments, Bag, Hardware, Rig, Animation"
    bpy.context.scene["source_foundation_sha256"] = before
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    after = sha256(source)
    if before != after:
        raise RuntimeError("Foundation source mutated")
    result = {
        "schema": "mia-v02-anatomy/v1",
        "stage": "ANATOMY_ONLY",
        "status": "READY_FOR_HUMAN_MULTIVIEW_REVIEW",
        "source_foundation": str(source),
        "source_foundation_sha256_before": before,
        "source_foundation_sha256_after": after,
        "source_immutable": before == after,
        "output": str(output),
        "output_sha256": sha256(output),
        "body": {"object": body.name, "vertices": vertices, "polygons": len(body.data.polygons), "shape_keys": [key.name for key in body.data.shape_keys.key_blocks]},
        "eyes": [{"object": eye.name, "world_center": [round(value, 6) for value in eye.matrix_world.translation]} for eye in eye_items],
        "face_details": [obj.name for obj in details.objects],
        "collections_unimplemented": [name for name in ("ScalpGuide", "Hair", "Garments", "Bag", "Hardware", "RigGuide") if bpy.data.collections.get(name)],
        "claims": [
            "No v45 geometry or projected texture was read.",
            "The body remains a complete topology; this stage deletes no face, scalp, or torso geometry.",
            "Hair, garments, bag, hardware, rig, and animation remain unimplemented.",
        ],
    }
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
