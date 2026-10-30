#!/usr/bin/env python3
"""Render version-bound multi-view diagnostics without saving the source blend.

Use neutral clay views as geometry inspection, not as an automatic hole or
likeness detector.  Human review gates intentionally begin UNVERIFIED.
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

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from audit_review import ReviewError, load_review, review_summary, sha256


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Read-only blend to diagnose")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--yaw-step", type=int, default=30)
    parser.add_argument("--resolution", type=int, default=640)
    parser.add_argument("--modes", nargs="+", choices=("saved", "clay"), default=("saved", "clay"))
    parser.add_argument("--scales", nargs="+", choices=("full", "torso", "head"), default=("full", "torso", "head"))
    parser.add_argument("--elevations", nargs="+", type=float, default=(-10.0, 0.0, 10.0))
    parser.add_argument("--manual-review")
    return parser.parse_args(argv)


def scene_inventory():
    meshes = []
    for obj in sorted((o for o in bpy.context.scene.objects if o.type == "MESH"), key=lambda o: o.name):
        meshes.append({
            "name": obj.name,
            "collections": sorted(c.name for c in obj.users_collection),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "visible_render": not obj.hide_render,
            "shape_keys": list(obj.data.shape_keys.key_blocks.keys()) if obj.data.shape_keys else [],
            "modifiers": [{"name": m.name, "type": m.type, "show_viewport": m.show_viewport, "show_render": m.show_render} for m in obj.modifiers],
        })
    armatures = []
    for obj in bpy.context.scene.objects:
        if obj.type == "ARMATURE":
            armatures.append({"name": obj.name, "bones": [b.name for b in obj.data.bones]})
    return {"meshes": meshes, "armatures": armatures}


def bounds():
    points = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.hide_render:
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("No render-visible mesh objects")
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def make_camera():
    data = bpy.data.cameras.new("AUDIT_CAMERA")
    data.type = "ORTHO"
    obj = bpy.data.objects.new("AUDIT_CAMERA", data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.scene.camera = obj
    return obj


def track(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def setup_render(resolution):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("AUDIT_WORLD")
    scene.world.color = (0.045, 0.045, 0.055)


def make_clay_material():
    material = bpy.data.materials.new("AUDIT_NEUTRAL_CLAY")
    material.diffuse_color = (0.32, 0.32, 0.32, 1.0)
    material.use_nodes = True
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = (0.32, 0.32, 0.32, 1.0)
    node.inputs["Roughness"].default_value = 1.0
    node.inputs["Metallic"].default_value = 0.0
    return material


def clay_override(material):
    original = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.hide_render:
            original[obj.name] = list(obj.data.materials)
            obj.data.materials.clear()
            obj.data.materials.append(material)
    return original


def restore_materials(original):
    for name, materials in original.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.data.materials.clear()
            for material in materials:
                obj.data.materials.append(material)


def lighting():
    for name, position, energy in (("AUDIT_KEY", (3, -4, 5), 900), ("AUDIT_FILL", (-4, -2, 3), 350), ("AUDIT_RIM", (2, 3, 4), 500)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = 4.0
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (0, 0, 0)
        obj.rotation_euler = (Vector((0, 0, 1)) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_views(args, source_hash):
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    setup_render(args.resolution)
    low, high = bounds()
    center = (low + high) / 2
    height = high.z - low.z
    camera = make_camera()
    lighting()
    scale_defs = {
        "full": (center.z, max(height * 1.12, 0.2)),
        "torso": (low.z + height * 0.57, max(height * 0.66, 0.2)),
        "head": (low.z + height * 0.83, max(height * 0.38, 0.2)),
    }
    records = []
    clay = make_clay_material()
    yaws = range(0, 360, args.yaw_step)
    for mode in args.modes:
        saved = clay_override(clay) if mode == "clay" else None
        for scale_name in args.scales:
            target_z, ortho = scale_defs[scale_name]
            camera.data.ortho_scale = ortho
            for elevation in args.elevations:
                for yaw in yaws:
                    radians = math.radians(yaw)
                    elev_radians = math.radians(elevation)
                    distance = max(height * 2.1, 2.0)
                    target = Vector((center.x, center.y, target_z))
                    camera.location = target + Vector((math.sin(radians) * distance, -math.cos(radians) * distance, math.sin(elev_radians) * distance))
                    track(camera, target)
                    name = "%s_%s_y%03d_e%+03d.png" % (mode, scale_name, yaw, int(elevation))
                    path = output / name
                    bpy.context.scene.render.filepath = str(path)
                    bpy.ops.render.render(write_still=True)
                    records.append({
                        "file": name,
                        "sha256": sha256(path),
                        "mode": mode,
                        "scale": scale_name,
                        "yaw_degrees": yaw,
                        "elevation_degrees": elevation,
                        "camera_location": [round(v, 6) for v in camera.location],
                        "target": [round(v, 6) for v in target],
                        "ortho_scale": round(ortho, 6),
                    })
        if saved is not None:
            restore_materials(saved)
    return records


def main():
    args = parse_args()
    source = Path(args.input).resolve()
    # open_mainfile changes Blender's working directory to the input's folder.
    # Resolve caller-relative evidence paths before that happens.
    args.output_dir = str(Path(args.output_dir).resolve())
    args.report = str(Path(args.report).resolve())
    if args.manual_review:
        args.manual_review = str(Path(args.manual_review).resolve())
    before = sha256(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    records = render_views(args, before)
    after = sha256(source)
    if after != before:
        raise RuntimeError("SOURCE MUTATED: before=%s after=%s" % (before, after))
    gates = {"artistic": "UNVERIFIED", "geometry": "UNVERIFIED", "manual": "UNVERIFIED"}
    review_info = None
    if args.manual_review:
        try:
            review = load_review(args.manual_review, before)
            gates.update(review_summary(review))
            review_info = {"path": str(Path(args.manual_review).resolve()), "accepted": True}
        except ReviewError as error:
            review_info = {"path": str(Path(args.manual_review).resolve()), "accepted": False, "error": str(error)}
            gates["manual"] = "UNVERIFIED"
    report = {
        "schema": "mia-multiview-audit/v1",
        "source": str(source),
        "source_sha256_before": before,
        "source_sha256_after": after,
        "source_immutable": before == after,
        "modes": list(args.modes),
        "scales": list(args.scales),
        "yaw_step": args.yaw_step,
        "elevations": args.elevations,
        "inventory": scene_inventory(),
        "gates": gates,
        "manual_review": review_info,
        "renders": records,
        "limitations": [
            "Image generation and mesh inventory are diagnostic evidence, not an artistic or topology pass.",
            "Neutral clay assigns a new Principled material and does not use image or normal-map nodes.",
            "The source blend is never saved by this tool.",
        ],
    }
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"source_immutable": True, "render_count": len(records), "report": args.report}))


if __name__ == "__main__":
    main()
