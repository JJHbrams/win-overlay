#!/usr/bin/env python3
"""Fast, read-only frontal/profile anatomy review renders for Mia v02."""
import argparse
import hashlib
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def args():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(values)


def main():
    options = args()
    source = Path(options.input).resolve()
    output = Path(options.output_dir).resolve()
    before = sha256(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera_data = bpy.data.cameras.new("V02_KEY_CAMERA")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 0.47
    camera = bpy.data.objects.new("V02_KEY_CAMERA", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = Vector((0, -0.020, 1.515))
    for name, yaw in (("front", 0), ("three_quarter", 45), ("profile", 90), ("back", 180)):
        radians = math.radians(yaw)
        camera.location = target + Vector((math.sin(radians) * 2.0, -math.cos(radians) * 2.0, 0.03))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(output / (name + ".png"))
        bpy.ops.render.render(write_still=True)
    after = sha256(source)
    if before != after:
        raise RuntimeError("source changed during key render")
    print("source immutable", before == after, "output", output)


if __name__ == "__main__":
    main()
