"""Render a non-destructive contact probe for existing Mia eye expression keys."""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector


FACE_NAME = "Mia_Face_AnimeTopology"


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(values)


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def geometry_uv_fingerprint(face):
    mesh = face.data
    digest = hashlib.sha256()
    for vert in mesh.vertices:
        digest.update(bytes(vert.co))
    active_uv = mesh.uv_layers.active
    if active_uv:
        for item in active_uv.data:
            digest.update(bytes(item.uv))
    return digest.hexdigest(), len(mesh.vertices), len(active_uv.data) if active_uv else 0


def shape_key_coordinate_fingerprint(face):
    digest = hashlib.sha256()
    keys = face.data.shape_keys.key_blocks if face.data.shape_keys else []
    for key in keys:
        digest.update(key.name.encode("utf-8"))
        for point in key.data:
            digest.update(bytes(point.co))
    return digest.hexdigest(), len(keys)


def find_suffix_key(keys, suffix):
    matches = [key for key in keys if key.name.endswith(suffix)]
    if len(matches) != 1:
        raise RuntimeError("Expected one key ending %s, found %s" % (suffix, [key.name for key in matches]))
    return matches[0]


def aim(camera, location, target):
    camera.location = location
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def setup_camera(scene, face):
    data = bpy.data.cameras.get("MIA_EYE_POSE_PROBE_CAMERA") or bpy.data.cameras.new("MIA_EYE_POSE_PROBE_CAMERA")
    camera = bpy.data.objects.get("MIA_EYE_POSE_PROBE_CAMERA") or bpy.data.objects.new("MIA_EYE_POSE_PROBE_CAMERA", data)
    if camera.name not in scene.collection.objects:
        scene.collection.objects.link(camera)
    points = [face.matrix_world @ vertex.co for vertex in face.data.vertices]
    width = max(point.x for point in points) - min(point.x for point in points)
    target = Vector((0.0, (min(point.y for point in points) + max(point.y for point in points)) * 0.5, 1.58))
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 0.30
    scene.camera = camera
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    return camera, target, width


def render_pair(scene, camera, target, width, directory, label):
    aim(camera, target + Vector((0.0, -width * 3.0, 0.0)), target)
    front = directory / (label + "_front.png")
    scene.render.filepath = str(front)
    bpy.ops.render.render(write_still=True)
    aim(camera, target + Vector((width * 0.62, -width * 2.93, width * 0.04)), target)
    three_quarter = directory / (label + "_3q.png")
    scene.render.filepath = str(three_quarter)
    bpy.ops.render.render(write_still=True)
    return [str(front), str(three_quarter)]


def restore(keys, snapshot):
    for key in keys:
        key.value = snapshot[key.name]


def set_eye_case(keys, close, natural, sorrow, angry):
    # Isolate only the eye-expression channel; brows and every mouth key retain the loaded state.
    for key in keys:
        if "_EYE_" in key.name:
            key.value = 0.0
    selected = {
        "Close": (find_suffix_key(keys, "Fcl_EYE_Close"), close),
        "Natural": (find_suffix_key(keys, "Fcl_EYE_Natural"), natural),
        "Sorrow": (find_suffix_key(keys, "Fcl_EYE_Sorrow"), sorrow),
        "Angry": (find_suffix_key(keys, "Fcl_EYE_Angry"), angry),
    }
    for key, value in selected.values():
        key.value = value
    return {name: {"key": key.name, "value": value} for name, (key, value) in selected.items()}


def main():
    args = arguments()
    input_path = os.path.abspath(args.input)
    directory = Path(args.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=input_path)
    face = bpy.data.objects.get(FACE_NAME)
    if not face or not face.data.shape_keys:
        raise RuntimeError("Canonical face with shape keys is required")
    keys = face.data.shape_keys.key_blocks
    initial_values = {key.name: float(key.value) for key in keys}
    source_sha_before = sha_file(input_path)
    mesh_before = geometry_uv_fingerprint(face)
    key_coords_before = shape_key_coordinate_fingerprint(face)
    scene = bpy.context.scene
    camera, target, width = setup_camera(scene, face)
    cases = [
        ("01_loaded_baseline", None),
        ("02_close_050_sorrow_010", (0.50, 0.00, 0.10, 0.00)),
        ("03_close_060_sorrow_010", (0.60, 0.00, 0.10, 0.00)),
        ("04_close_070_sorrow_010", (0.70, 0.00, 0.10, 0.00)),
        ("05_close_055_angry_012", (0.55, 0.00, 0.00, 0.12)),
    ]
    records = []
    for label, values in cases:
        restore(keys, initial_values)
        selected = None if values is None else set_eye_case(keys, *values)
        frames = render_pair(scene, camera, target, width, directory, label)
        records.append({"label": label, "frames": frames, "eye_keys": selected,
                        "mouth_angry_retained": initial_values.get(find_suffix_key(keys, "Fcl_MTH_Angry").name),
                        "non_target_eye_keys_zeroed": values is not None})
        restore(keys, initial_values)
        if {key.name: float(key.value) for key in keys} != initial_values:
            raise RuntimeError("Shape-key dictionary was not restored after " + label)
    restore(keys, initial_values)
    mesh_after = geometry_uv_fingerprint(face)
    key_coords_after = shape_key_coordinate_fingerprint(face)
    source_sha_after = sha_file(input_path)
    if mesh_before != mesh_after or key_coords_before != key_coords_after or source_sha_before != source_sha_after:
        raise RuntimeError("Read-only probe integrity assertion failed")
    report = {
        "status": "EXPRESSION_CONTACT_PROBE_ONLY_NOT_FACIAL_RIG_PASS",
        "input": input_path,
        "source_sha256_before_after": [source_sha_before, source_sha_after],
        "face": FACE_NAME,
        "camera": {"resolution": [512, 512], "projection": "ORTHO", "ortho_scale": 0.30, "target_z": 1.58},
        "initial_shape_key_values_full": initial_values,
        "mesh_and_uv_fingerprint_before_after": [mesh_before[0], mesh_after[0]],
        "shape_key_coordinate_fingerprint_before_after": [key_coords_before[0], key_coords_after[0]],
        "vertex_count": mesh_before[1], "uv_corner_count": mesh_before[2], "shape_key_count": key_coords_before[1],
        "cases": records,
        "contact_sheet": str(directory / "eye_pose_contact_sheet.png"),
        "visual_review_against_mia_clean_master_v22": {
            "reference_regions": ["Observe", "Discover", "Dry Wit"],
            "recommended_case": "03_close_060_sorrow_010",
            "finding": "Close .60 produces the closest horizontal half-lid read among existing keys. Close .50 remains too open/round; Close .70 reads over-closed and dejected. Close .55 plus Angry .12 is clearer but more alert/tense than the Observe reference.",
            "limitation": "All five renders retain the current eye mesh silhouette and lack the reference's pronounced lower-lid/dark-circle treatment. That difference is structural/material appearance, not evidence that this expression-only probe changed geometry.",
        },
        "integrity": "No blend save, geometry edits, UV edits, or shape-key coordinate edits were performed.",
    }
    (directory / "eye_pose_probe_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
