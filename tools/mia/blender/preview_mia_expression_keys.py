#!/usr/bin/env python3
"""Non-destructive v11 mouth-key contact render for the anatomy freeze decision."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(values)


def aim(camera, location, target):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def main():
    args = arguments()
    bpy.ops.wm.open_mainfile(filepath=args.input)
    face = bpy.data.objects.get("Mia_Face_AnimeTopology")
    body = bpy.data.objects.get("Mia_Body_Anatomy_Skin")
    visible = sorted(obj.name for obj in bpy.data.objects if obj.type == "MESH" and not obj.hide_render
                     and obj.name.startswith("Mia_"))
    if not face or not body or visible != ["Mia_Body_Anatomy_Skin", "Mia_Face_AnimeTopology"]:
        raise RuntimeError("Expected exactly one visible v11 Face and Body assembly")
    directory = Path(args.output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = scene.camera
    aim(camera, (0, -0.72, 1.59), (0, -0.02, 1.57))
    keys = face.data.shape_keys.key_blocks
    snapshot = {key.name: key.value for key in keys}
    choices = (("basis_no_mth", None, 0.0),
               ("mth_neutral_1", "Face.M_F00_000_00_Fcl_MTH_Neutral", 1.0),
               ("mth_down_1", "Face.M_F00_000_00_Fcl_MTH_Down", 1.0),
               ("mth_angry_1", "Face.M_F00_000_00_Fcl_MTH_Angry", 1.0),
               ("mth_sorrow_1", "Face.M_F00_000_00_Fcl_MTH_Sorrow", 1.0),
               ("mth_fun_050", "Face.M_F00_000_00_Fcl_MTH_Fun", 0.5))
    records = []
    for label, selected, value in choices:
        for key in keys:
            if "_MTH_" in key.name:
                key.value = 0.0
        if selected:
            key = keys.get(selected)
            if not key:
                raise RuntimeError("Missing requested mouth key: " + selected)
            key.value = value
        scene.render.filepath = str(directory / (label + ".png"))
        bpy.ops.render.render(write_still=True)
        records.append({"file": label + ".png", "mouth_key": selected, "value": value,
                        "all_other_mth_keys": 0.0})
    for key in keys:
        key.value = snapshot[key.name]
    Path(args.report).write_text(json.dumps({
        "input": args.input,
        "non_destructive": True,
        "visible_mia_meshes_preflight": visible,
        "camera": "front 384px; non-mouth eyelid/brow state retained from v11",
        "records": records,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
