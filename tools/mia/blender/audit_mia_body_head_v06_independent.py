"""Independent structural and deformation audit for the Mia v06 native file.

This tool never saves either supplied blend.  It deliberately reports only
technical `pass_structure`; visual/art acceptance remains a human review.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector


BODY = "Mia_Body_Anatomy_Skin"
FACE = "Mia_Face_AnimeTopology"
DERIVED_BODY = "MIA_V06_BODY_SKIN"
DERIVED_FACE = "MIA_V06_FACE_SKIN"
DERIVED_RIG = "MIA_V06_RIG"


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def digest(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def hash_json(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def float32_coordinate_hash(points):
    hasher = hashlib.sha256()
    for point in points:
        hasher.update(struct.pack("<3f", point.co.x, point.co.y, point.co.z))
    return hasher.hexdigest()


def mesh_hashes(obj, include_coords=False):
    mesh = obj.data
    topology = [[int(index) for index in polygon.vertices] for polygon in mesh.polygons]
    uv = []
    for layer in mesh.uv_layers:
        uv.append([layer.name, [[round(loop.uv.x, 8), round(loop.uv.y, 8)] for loop in layer.data]])
    result = {"vertices": len(mesh.vertices), "polygons": len(mesh.polygons),
              "topology_order_hash": hash_json(topology), "uv_hash": hash_json(uv),
              "uv_layers": [layer.name for layer in mesh.uv_layers]}
    if include_coords:
        result["coordinate_hash_float32"] = float32_coordinate_hash(mesh.vertices)
    return result


def matrix(obj):
    return [[round(value, 7) for value in row] for row in obj.matrix_world]


def finite_shape_keys(obj):
    keys = list(obj.data.shape_keys.key_blocks) if obj and obj.data.shape_keys else []
    finite = all(math.isfinite(value) for key in keys for point in key.data for value in point.co)
    return {"count": len(keys), "names": [key.name for key in keys], "finite_coordinates": finite}


def shape_key_coordinate_hashes(obj, limit=None):
    keys = list(obj.data.shape_keys.key_blocks) if obj and obj.data.shape_keys else []
    if limit is not None:
        keys = keys[:limit]
    return {key.name: float32_coordinate_hash(key.data) for key in keys}


def mesh_world_positions(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return points


def delta(before, after):
    distances = [(right - left).length for left, right in zip(before, after)]
    return {"vertices_compared": len(distances), "max_m": round(max(distances, default=0.0), 8),
            "mean_m": round(sum(distances) / len(distances), 8) if distances else 0.0}


def snapshot_pose(rig):
    return {bone.name: {"mode": bone.rotation_mode, "euler": list(bone.rotation_euler),
                        "quaternion": list(bone.rotation_quaternion), "axis_angle": list(bone.rotation_axis_angle),
                        "location": list(bone.location), "scale": list(bone.scale)} for bone in rig.pose.bones}


def restore_pose(rig, snapshot):
    for name, values in snapshot.items():
        bone = rig.pose.bones.get(name)
        if not bone:
            continue
        bone.rotation_mode = values["mode"]
        bone.rotation_euler = values["euler"]
        bone.rotation_quaternion = values["quaternion"]
        bone.rotation_axis_angle = values["axis_angle"]
        bone.location = values["location"]
        bone.scale = values["scale"]


def pose_deformation_cases(body, rig):
    baseline = mesh_world_positions(body)
    snapshot = snapshot_pose(rig)
    cases = (("upper_arm_raise", "J_Bip_L_UpperArm", "Y", .55),
             ("torso_yaw", "J_Bip_C_Spine", "Z", .38),
             ("knee_bend", "J_Bip_L_LowerLeg", "X", .65))
    result = {}
    for label, bone_name, axis, radians in cases:
        restore_pose(rig, snapshot)
        bone = rig.pose.bones.get(bone_name)
        if not bone:
            result[label] = {"control": bone_name, "missing": True}
            continue
        bone.rotation_mode = "XYZ"
        bone.rotation_euler.rotate_axis(axis, radians)
        bpy.context.view_layer.update()
        result[label] = {"control": bone_name, "axis": axis, "radians": radians,
                         "evaluated_body_delta": delta(baseline, mesh_world_positions(body))}
    restore_pose(rig, snapshot)
    bpy.context.view_layer.update()
    result["neutral_return"] = delta(baseline, mesh_world_positions(body))
    return result


def expression_deformation_cases(face):
    baseline = mesh_world_positions(face)
    keys = list(face.data.shape_keys.key_blocks)
    initial = {key.name: key.value for key in keys}
    candidates = {"blink": next((key for key in keys if key.name.endswith("Fcl_EYE_Close")), None),
                  "mouth": next((key for key in keys if key.name.endswith("Fcl_MTH_A")), None)}
    report = {}
    for label, key in candidates.items():
        for item in keys:
            item.value = initial[item.name]
        if not key:
            report[label] = {"missing": True}
            continue
        key.value = 1.0
        bpy.context.view_layer.update()
        report[label] = {"control": key.name, "value": key.value,
                         "identity_profile_actual_values": identity_profile_values(face),
                         "evaluated_face_delta": delta(baseline, mesh_world_positions(face))}
    for key in keys:
        key.value = initial[key.name]
    bpy.context.view_layer.update()
    report["neutral_return"] = delta(baseline, mesh_world_positions(face))
    return report


def identity_profile_values(face):
    return {key.name: key.value for key in face.data.shape_keys.key_blocks if key.name.startswith("MIA_FaceArt_")}


def gaze_deformation_cases(face, rig):
    baseline = mesh_world_positions(face)
    snapshot = snapshot_pose(rig)
    eyes = [rig.pose.bones.get(name) for name in ("J_Adj_L_FaceEye", "J_Adj_R_FaceEye")]
    eyes = [bone for bone in eyes if bone]
    report = {"expected_eye_bones": ["J_Adj_L_FaceEye", "J_Adj_R_FaceEye"],
              "found_eye_bones": [bone.name for bone in eyes], "cases": {}}
    for label, radians in (("gaze_left", .16), ("gaze_right", -.16)):
        restore_pose(rig, snapshot)
        for bone in eyes:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = (0, 0, radians)
        bpy.context.view_layer.update()
        report["cases"][label] = {"axis": "local Z", "radians": radians,
                                  "actual_rotation_euler": {bone.name: list(bone.rotation_euler) for bone in eyes},
                                  "identity_profile_actual_values": identity_profile_values(face),
                                  "evaluated_face_delta": delta(baseline, mesh_world_positions(face))}
    restore_pose(rig, snapshot)
    bpy.context.view_layer.update()
    report["neutral_return"] = delta(baseline, mesh_world_positions(face))
    return report


def material_paths():
    missing = []
    for image in bpy.data.images:
        if image.packed_file or not image.filepath:
            continue
        path = Path(bpy.path.abspath(image.filepath))
        if not path.exists():
            missing.append({"name": image.name, "path": str(path)})
    return missing


def render_fresh_head(output, body, face):
    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in (body, face)
        if obj.type == "LIGHT":
            obj.hide_render = True
    camera_data = bpy.data.cameras.new("MIA_V06_INDEPENDENT_AUDIT_CAMERA")
    camera_data.type = "ORTHO"; camera_data.ortho_scale = .44
    camera = bpy.data.objects.new(camera_data.name, camera_data); scene.collection.objects.link(camera)
    camera.location = (0, -4, 1.58); camera.rotation_euler = (Vector((0, 0, 1.58)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for index, (location, energy) in enumerate((((2, -3, 3), 170), ((-2, -2, 2), 80), ((0, 2, 2), 90))):
        data = bpy.data.lights.new("MIA_V06_INDEPENDENT_AUDIT_LIGHT_%d" % index, "AREA")
        data.energy = energy; data.shape = "DISK"; data.size = 2
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj)
        obj.location = location; obj.rotation_euler = (Vector((0, 0, 1.58)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_x = 900; scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = "PNG"
    path = output / "fresh_reopen_actual_head.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    return str(path)


def render_head_yaw_checks(output, body, face, rig):
    """Render only the cap/neck inspection poses; pose changes stay in memory."""
    scene = bpy.context.scene
    for obj in scene.objects:
        if obj.type == "MESH":
            obj.hide_render = obj not in (body, face)
        if obj.type == "LIGHT":
            obj.hide_render = True
    camera_data = bpy.data.cameras.new("MIA_V06_INDEPENDENT_YAW_CAMERA")
    camera_data.type = "ORTHO"; camera_data.ortho_scale = .44
    camera = bpy.data.objects.new(camera_data.name, camera_data); scene.collection.objects.link(camera)
    camera.location = (0, -3.5, 1.58); camera.rotation_euler = (Vector((0, 0, 1.58)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    for index, (location, energy) in enumerate((((2, -3, 3), 170), ((-2, -2, 2), 80), ((0, 2, 2), 90))):
        data = bpy.data.lights.new("MIA_V06_INDEPENDENT_YAW_LIGHT_%d" % index, "AREA")
        data.energy = energy; data.shape = "DISK"; data.size = 2
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj)
        obj.location = location; obj.rotation_euler = (Vector((0, 0, 1.58)) - obj.location).to_track_quat("-Z", "Y").to_euler()
    clay = bpy.data.materials.new("MIA_V06_INDEPENDENT_YAW_CLAY")
    clay.use_nodes = True
    shader = next(node for node in clay.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (.22, .25, .30, 1); shader.inputs["Roughness"].default_value = .86
    snapshot = snapshot_pose(rig); baseline = mesh_world_positions(face); head = rig.pose.bones.get("J_Bip_C_Head")
    report = {"control": "J_Bip_C_Head", "found": bool(head), "cases": {}}
    if not head:
        return report
    def face_skin_copy():
        copy = face.copy(); copy.data = face.data.copy(); copy.name = "MIA_V06_INDEPENDENT_YAW_FACE_SKIN"
        bpy.context.scene.collection.objects.link(copy); copy.hide_render = False
        bpy.context.view_layer.objects.active = copy; copy.select_set(True); bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
        for polygon in copy.data.polygons: polygon.select = polygon.material_index not in {0, 7}
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
        copy.select_set(False); return copy
    for label, radians in (("yaw_left_20deg", math.radians(20)), ("yaw_right_20deg", math.radians(-20))):
        restore_pose(rig, snapshot); head.rotation_mode = "XYZ"; head.rotation_euler = (0, 0, radians)
        bpy.context.view_layer.update()
        record = {"radians": radians, "actual_rotation_euler": list(head.rotation_euler),
                  "evaluated_face_delta": delta(baseline, mesh_world_positions(face)), "renders": {}}
        for mode, override in (("actual", None), ("clay", clay)):
            skin = None
            if mode == "clay":
                face.hide_render = True; skin = face_skin_copy()
            bpy.context.view_layer.material_override = override
            path = output / ("head_" + label + "_" + mode + ".png")
            scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); record["renders"][mode] = str(path)
            if skin: bpy.data.objects.remove(skin, do_unlink=True); face.hide_render = False
        report["cases"][label] = record
    bpy.context.view_layer.material_override = None
    restore_pose(rig, snapshot); bpy.context.view_layer.update()
    report["neutral_return"] = delta(baseline, mesh_world_positions(face))
    return report


def main():
    args = parse(); source = Path(args.source).resolve(); candidate = Path(args.input).resolve(); output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    hashes_before = {"source": digest(source), "candidate": digest(candidate)}
    bpy.ops.wm.open_mainfile(filepath=str(source))
    source_face = bpy.data.objects[FACE]
    source_data = {"body": mesh_hashes(bpy.data.objects[BODY], True), "face": mesh_hashes(source_face, True),
                   "face_keys": finite_shape_keys(source_face), "face_key_coordinate_hashes": shape_key_coordinate_hashes(source_face, 42)}
    bpy.ops.wm.open_mainfile(filepath=str(candidate))
    archive_body, archive_face = bpy.data.objects.get(BODY), bpy.data.objects.get(FACE)
    body, face, rig = bpy.data.objects.get(DERIVED_BODY), bpy.data.objects.get(DERIVED_FACE), bpy.data.objects.get(DERIVED_RIG)
    archive = {"body_present": bool(archive_body), "face_present": bool(archive_face)}
    if archive_body: archive["body"] = mesh_hashes(archive_body, True)
    if archive_face:
        archive["face"] = mesh_hashes(archive_face, True)
        archive["face_key_coordinate_hashes"] = shape_key_coordinate_hashes(archive_face, 42)
    derived = {"body": mesh_hashes(body) if body else None, "face": mesh_hashes(face) if face else None,
               "face_keys": finite_shape_keys(face) if face else None}
    rig_info = {"body_parent": body.parent.name if body and body.parent else None,
                "face_parent": face.parent.name if face and face.parent else None,
                "body_armature_targets": [modifier.object.name if modifier.object else None for modifier in body.modifiers if modifier.type == "ARMATURE"] if body else [],
                "face_armature_targets": [modifier.object.name if modifier.object else None for modifier in face.modifiers if modifier.type == "ARMATURE"] if face else [],
                "body_world": matrix(body) if body else None, "face_world": matrix(face) if face else None,
                "rig_world": matrix(rig) if rig else None}
    refs = [{"object": obj.name, "image": obj.data.name if obj.data else None,
             "packed": bool(obj.data and obj.data.packed_file)} for obj in bpy.data.objects if obj.name.startswith("REF_")]
    identity_profile = identity_profile_values(face) if face and face.data.shape_keys else {}
    expression = expression_deformation_cases(face) if face else {}
    gaze = gaze_deformation_cases(face, rig) if face and rig else {}
    pose = pose_deformation_cases(body, rig) if body and rig else {}
    image = render_fresh_head(output, body, face) if body and face else None
    head_yaw = render_head_yaw_checks(output, body, face, rig) if body and face and rig else {}
    hashes_after = {"source": digest(source), "candidate": digest(candidate)}
    archive_match = archive_body and archive_face and archive["body"] == source_data["body"] and archive["face"] == source_data["face"] and archive.get("face_key_coordinate_hashes") == source_data["face_key_coordinate_hashes"]
    structure_keys = ("vertices", "polygons", "topology_order_hash", "uv_hash", "uv_layers")
    derived_match = bool(body and face
                         and all(derived["body"].get(key) == source_data["body"].get(key) for key in structure_keys)
                         and all(derived["face"].get(key) == source_data["face"].get(key) for key in structure_keys))
    source_prefix = source_data["face_keys"]["names"]
    face_keys_ok = bool(derived["face_keys"] and derived["face_keys"]["count"] >= 44
                        and derived["face_keys"]["names"][:len(source_prefix)] == source_prefix
                        and derived["face_keys"]["finite_coordinates"])
    report = {"files": {"source": str(source), "candidate": str(candidate), "sha_before": hashes_before, "sha_after": hashes_after,
                        "files_unchanged": hashes_before == hashes_after}, "source": source_data, "archive": archive, "derived": derived,
              "archive_exact_match": bool(archive_match), "derived_structure_match": derived_match, "face_key_contract": {"source_prefix_count": len(source_prefix), "valid": face_keys_ok},
              "rig": rig_info, "references": {"expected": 3, "found": refs, "all_packed": len(refs) == 3 and all(item["packed"] for item in refs), "missing_textures": material_paths()},
              "identity_profile_actual_values": identity_profile, "expressions": expression, "gaze": gaze, "poses": pose, "head_yaw_checks": head_yaw, "fresh_reopen_actual_head": image,
              "pass_structure": False, "art_pass": "not evaluated"}
    rig_ok = rig and rig_info["body_parent"] == DERIVED_RIG and rig_info["face_parent"] == DERIVED_RIG and DERIVED_RIG in rig_info["body_armature_targets"] and DERIVED_RIG in rig_info["face_armature_targets"]
    expected_pose = {"upper_arm_raise", "torso_yaw", "knee_bend"}
    expected_expression = {"blink", "mouth"}
    expected_gaze = {"gaze_left", "gaze_right"}
    expected_yaw = {"yaw_left_20deg", "yaw_right_20deg"}
    expected_cases_present = expected_pose <= set(pose) and expected_expression <= set(expression) and expected_gaze <= set(gaze.get("cases", {})) and expected_yaw <= set(head_yaw.get("cases", {})) and len(gaze.get("found_eye_bones", [])) == 2
    identity_ok = all(value == 1.0 for value in identity_profile.values()) and len(identity_profile) == 2 and all(all(value == 1.0 for value in expression[item].get("identity_profile_actual_values", {}).values()) for item in expected_expression) and all(all(value == 1.0 for value in gaze["cases"][item].get("identity_profile_actual_values", {}).values()) for item in expected_gaze)
    deltas_ok = expected_cases_present and all(pose[item].get("evaluated_body_delta", {}).get("max_m", 0) > 0 for item in expected_pose) and all(expression[item].get("evaluated_face_delta", {}).get("max_m", 0) > 0 for item in expected_expression) and all(gaze["cases"][item].get("evaluated_face_delta", {}).get("max_m", 0) > 0 for item in expected_gaze)
    yaw_ok = all(head_yaw["cases"][item].get("evaluated_face_delta", {}).get("max_m", 0) > 0 for item in expected_yaw)
    returns_ok = pose.get("neutral_return", {}).get("max_m") == 0 and expression.get("neutral_return", {}).get("max_m") == 0 and gaze.get("neutral_return", {}).get("max_m") == 0 and head_yaw.get("neutral_return", {}).get("max_m") == 0
    report["pass_structure"] = bool(report["files"]["files_unchanged"] and archive_match and derived_match and face_keys_ok and rig_ok
                                    and report["references"]["all_packed"] and not report["references"]["missing_textures"] and identity_ok and deltas_ok and yaw_ok and returns_ok and image)
    (output / "independent-audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
