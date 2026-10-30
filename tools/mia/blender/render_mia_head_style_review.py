"""Render six read-only Mia head views against a neutral reference background."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = Path(args.input).resolve()
    output = Path(args.output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source_hash = sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    keys = bpy.data.objects["Mia_Face_AnimeTopology"].data.shape_keys.key_blocks
    neutral = {key.name: key.value for key in keys}
    world = bpy.data.worlds.new("MIA_REFERENCE_GRAY_REVIEW")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.66,.69,.72,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1
    scene.world = world
    scene.render.film_transparent = False
    camera = scene.camera
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = .46
    scene.render.resolution_x = scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    records = []
    try:
        for proof, angles in (("neutral",(0,35,90,180)),("blink",(0,)),("mouth_a",(35,))):
            for key in keys:
                key.value = neutral[key.name]
            channel = "Fcl_EYE_" if proof == "blink" else "Fcl_MTH_" if proof == "mouth_a" else None
            if channel:
                for key in keys:
                    if channel in key.name:
                        key.value = 0
                suffix = "Fcl_EYE_Close" if proof == "blink" else "Fcl_MTH_A"
                next(key for key in keys if key.name.endswith(suffix)).value = 1
            bpy.context.view_layer.update()
            for angle in angles:
                yaw = math.radians(angle)
                target = Vector((0,0,1.565))
                camera.location = target + Vector((.8*math.sin(yaw),-.8*math.cos(yaw),0))
                camera.rotation_euler = (target-camera.location).to_track_quat("-Z","Y").to_euler()
                path = output / f"{proof}_y{angle:03d}.png"
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
                records.append({"pose":proof,"yaw":angle,"path":path.name,"sha256":sha(path)})
    finally:
        for key in keys:
            key.value = neutral[key.name]
    assert neutral == {key.name:key.value for key in keys}
    assert source_hash == sha(source), "Read-only review changed source bytes"
    report = {"input":str(source),"source_sha256":source_hash,"source_unchanged":True,
              "neutral_restored":True,"world_gray":[.66,.69,.72],"camera_ortho_scale":.46,
              "frames":records,"status":"EVIDENCE_ONLY; no artistic acceptance inferred"}
    (output / "report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8",newline="\n")


if __name__ == "__main__":
    main()
