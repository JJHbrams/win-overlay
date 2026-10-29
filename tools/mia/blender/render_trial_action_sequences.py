"""Render-gated PNG sequence exporter for approved Mia rig drafts.

Nothing renders unless --render is supplied.  This is deliberately separate
from binding so final-graft approval controls the expensive/artifact-producing
step.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy


CLIPS = {"Idle": ("Idle_90f", 1, 90), "Turn": ("Turn_60f", 1, 60), "Click": ("Click_30f", 1, 30)}


def arguments():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--camera", default="QA_Camera_Front")
    p.add_argument("--clip", action="append", choices=tuple(CLIPS), help="render only this clip; default validates/renders all")
    p.add_argument("--render", action="store_true", help="required: actually write PNG frames")
    return p.parse_args(raw)


def action_for(name):
    action = bpy.data.actions.get(name)
    if action is None:
        raise RuntimeError("Required native action missing: " + name)
    return action


def configure(scene, camera):
    if camera is None or camera.type != 'CAMERA':
        raise RuntimeError("Requested camera is missing or not a camera")
    scene.camera = camera
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 512, 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    scene.render.fps = 30


def verify_rest_end(rig, action, first, last):
    scene = bpy.context.scene
    rig.animation_data_create().action = action
    scene.frame_set(first)
    start = [(pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in rig.pose.bones]
    scene.frame_set(last)
    end = [(pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in rig.pose.bones]
    deltas = []
    for left, right in zip(start, end):
        deltas.extend(((left[0] - right[0]).length, (left[2] - right[2]).length,
                       1.0 - abs(left[1].normalized().dot(right[1].normalized()))))
    return max(deltas)


def first_pose_hash(rig, action, frame):
    rig.animation_data_create().action = action
    # Force action evaluation even when switching while already at frame 1.
    bpy.context.scene.frame_set(frame + 1)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    values = []
    for pb in rig.pose.bones:
        quat = pb.rotation_quaternion.normalized()
        if quat.w < 0:  # q and -q represent the same rest orientation.
            quat.negate()
        # 1e-8 float noise from rest-local quaternion conversion is immaterial;
        # use a 1e-6m / quaternion-component canonical comparison tolerance.
        for value in (*pb.location, *quat, *pb.scale):
            rounded = round(value, 6)
            values.append(0.0 if rounded == 0 else rounded)  # normalize -0.0 for stable hashes
    return hashlib.sha256(repr(values).encode("ascii")).hexdigest()


def main():
    ns = arguments()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ns.input))
    rig = bpy.data.objects.get("Mia_RigMechanism")
    if rig is None or rig.type != 'ARMATURE':
        raise RuntimeError("Mia_RigMechanism armature missing")
    camera = bpy.data.objects.get(ns.camera)
    scene = bpy.context.scene
    configure(scene, camera)
    os.makedirs(ns.output_dir, exist_ok=True)
    result = {"input": os.path.abspath(ns.input), "render_requested": ns.render,
              "camera": ns.camera, "resolution": [512, 768], "transparent": True,
              "fps": 30, "clips": {},
              "limitations": ["This exporter does not establish rig quality or final-input approval.",
                              "Click uses only the independently trialed 0..5-degree upper-arm and 0..14-degree forearm range; fingers remain unverified.",
                              "Finger and Blink proof must remain separately verified."]}
    canonical_hash = first_pose_hash(rig, action_for("Idle_90f"), 1)
    result["canonical_idle_frame001_hash"] = canonical_hash
    active_clips = {label: CLIPS[label] for label in ns.clip} if ns.clip else CLIPS
    for label, (action_name, first, last) in active_clips.items():
        action = action_for(action_name)
        loop_delta = verify_rest_end(rig, action, first, last)
        start_hash = first_pose_hash(rig, action, first)
        frames = [os.path.join(ns.output_dir, label.lower(), "%04d.png" % frame) for frame in range(first, last + 1)]
        result["clips"][label] = {"action": action_name, "frames": [first, last], "frame_count": len(frames),
                                  "loop_end_pose_delta": loop_delta, "frame001_pose_hash": start_hash,
                                  "matches_canonical_idle_frame001": start_hash == canonical_hash,
                                  "frames_pattern": os.path.join(ns.output_dir, label.lower(), "%04d.png")}
        if ns.render:
            clip_dir = os.path.dirname(frames[0])
            os.makedirs(clip_dir, exist_ok=True)
            rig.animation_data.action = action
            for frame, output in zip(range(first, last + 1), frames):
                scene.frame_set(frame)
                scene.render.filepath = output
                bpy.ops.render.render(write_still=True)
    # Keep the canonical shared idle/rest frame active if this blend is saved later.
    rig.animation_data.action = action_for("Idle_90f")
    scene.frame_set(1)
    with open(ns.report, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)


if __name__ == "__main__":
    main()
