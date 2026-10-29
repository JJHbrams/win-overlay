"""Add proof-of-rig draft actions and compact PNG evidence to a trial blend."""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector


def args():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--render-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--render", action="store_true", help="required to emit proof PNGs")
    return parser.parse_args(raw)


def reset(rig):
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def clear_prior_proof_actions(rig):
    """Build exact native action names without retaining stale .001 actions."""
    rig.animation_data_create().action = None
    for track in list(rig.animation_data.nla_tracks):
        rig.animation_data.nla_tracks.remove(track)
    roots = ("Idle_90f", "Turn_60f", "Click_30f")
    for action in list(bpy.data.actions):
        if any(action.name == root or action.name.startswith(root + ".") for root in roots):
            bpy.data.actions.remove(action)


def local_world_rotation(pb, axis, degrees):
    rest = pb.bone.matrix_local.to_3x3()
    world = Quaternion(Vector(axis), math.radians(degrees)).to_matrix()
    return (rest.inverted() @ world @ rest).to_quaternion()


def key_location(pb, frame, xyz):
    pb.location = xyz
    pb.keyframe_insert("location", frame=frame)


def key_rotation(pb, frame, quat):
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = quat
    pb.keyframe_insert("rotation_quaternion", frame=frame)


def key_identity_all_bones(rig, first, last):
    """Prevent pose-channel leakage when native actions are switched."""
    for pb in rig.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        for frame in (first, last):
            key_location(pb, frame, (0, 0, 0))
            key_rotation(pb, frame, (1, 0, 0, 0))
            pb.scale = (1, 1, 1)
            pb.keyframe_insert("scale", frame=frame)


def finish(action, end):
    action.frame_start, action.frame_end = 1, end
    action.use_fake_user = True
    action["proof_scope"] = "draft rig mechanism only; not production character animation"
    # Blender 5.2 stores action curves in layered channel bags.
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for curve in bag.fcurves:
                    for key in curve.keyframe_points:
                        key.interpolation = 'BEZIER'


def action_idle(rig):
    action = bpy.data.actions.new("Idle_90f")
    rig.animation_data_create().action = action
    reset(rig)
    key_identity_all_bones(rig, 1, 90)
    chest = rig.pose.bones["DEF_Chest"]
    hair_l, hair_r = rig.pose.bones["DEF_HairLower_L"], rig.pose.bones["DEF_HairLower_R"]
    for frame, z in ((1, 0), (23, .006), (45, 0), (68, -.004), (90, 0)):
        key_location(chest, frame, (0, 0, z))
    for frame, angle in ((1, 0), (30, .6), (60, -.6), (90, 0)):
        key_rotation(hair_l, frame, local_world_rotation(hair_l, (0, 0, 1), angle))
        key_rotation(hair_r, frame, local_world_rotation(hair_r, (0, 0, 1), -angle))
    finish(action, 90)
    return action


def action_turn(rig):
    action = bpy.data.actions.new("Turn_60f")
    rig.animation_data.action = action
    reset(rig)
    key_identity_all_bones(rig, 1, 60)
    head, chest, pelvis = rig.pose.bones["DEF_Head"], rig.pose.bones["DEF_Chest"], rig.pose.bones["DEF_Pelvis"]
    hair_l, hair_r = rig.pose.bones["DEF_HairLower_L"], rig.pose.bones["DEF_HairLower_R"]
    for frame, yaw, chest_yaw, shift in ((1, 0, 0, 0), (15, 10, 2, -.006), (30, 18, 4, -.012), (45, 10, 2, -.006), (60, 0, 0, 0)):
        key_rotation(head, frame, local_world_rotation(head, (0, 0, 1), yaw))
        key_rotation(chest, frame, local_world_rotation(chest, (0, 0, 1), chest_yaw))
        key_location(pelvis, frame, (shift, 0, 0))
    for frame, angle in ((1, 0), (20, -.6), (35, -1.6), (50, -.5), (60, 0)):
        key_rotation(hair_l, frame, local_world_rotation(hair_l, (0, 0, 1), angle))
        key_rotation(hair_r, frame, local_world_rotation(hair_r, (0, 0, 1), -angle))
    finish(action, 60)
    return action


def action_click(rig):
    action = bpy.data.actions.new("Click_30f")
    rig.animation_data.action = action
    reset(rig)
    key_identity_all_bones(rig, 1, 30)
    # Bounded by the independently verified seam-weight trial: only 0..peak
    # values are used, never the previously failing negative/larger excursion.
    upper, fore = rig.pose.bones["DEF_UpperArm_R"], rig.pose.bones["DEF_Forearm_R"]
    for frame, upper_angle, fore_angle in ((1, 0, 0), (7, 1.5, 4), (15, 5, 14), (22, 2.5, 7), (30, 0, 0)):
        key_rotation(upper, frame, local_world_rotation(upper, (1, 0, 0), upper_angle))
        key_rotation(fore, frame, local_world_rotation(fore, (1, 0, 0), fore_angle))
    finish(action, 30)
    return action


def footplant(rig, action, frames):
    rig.animation_data.action = action
    scene = bpy.context.scene
    samples = []
    dg = bpy.context.evaluated_depsgraph_get()
    for frame in frames:
        scene.frame_set(frame)
        ev = rig.evaluated_get(dg)
        samples.append([tuple(ev.matrix_world @ ev.pose.bones[name].head) for name in ("DEF_Foot_L", "DEF_Foot_R")])
    reference = samples[0]
    return max((Vector(point) - Vector(reference[side])).length for pointset in samples for side, point in enumerate(pointset))


def shoulder_head_proximity(rig, action):
    rig.animation_data.action = action
    bpy.context.scene.frame_set(30)
    dg = bpy.context.evaluated_depsgraph_get()
    head = bpy.data.objects["Mia_Graft_Head_Editable"].evaluated_get(dg)
    body = bpy.data.objects["Mia_Graft_Body_Editable"].evaluated_get(dg)
    hm = head.to_mesh()
    bm = body.to_mesh()
    try:
        hs = [head.matrix_world @ v.co for v in hm.vertices if v.co.z > .25]
        bs = [body.matrix_world @ v.co for v in bm.vertices if abs((body.matrix_world @ v.co).x) > .12 and 1.22 < (body.matrix_world @ v.co).z < 1.40]
        # Sampling avoids falsely treating the intended neck seam as an intersection test.
        hs, bs = hs[::100], bs[::100]
        return min((a - b).length for a in hs for b in bs) if hs and bs else None
    finally:
        head.to_mesh_clear()
        body.to_mesh_clear()


def render(scene, rig, action, frame, path):
    rig.animation_data.action = action
    scene.frame_set(frame)
    scene.camera = bpy.data.objects.get("QA_Camera_Front") or scene.camera
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.film_transparent = True
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    ns = args()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ns.input))
    rig = bpy.data.objects["Mia_RigMechanism"]
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    scene.frame_start, scene.frame_end = 1, 90
    clear_prior_proof_actions(rig)
    idle, turn, click = action_idle(rig), action_turn(rig), action_click(rig)
    os.makedirs(ns.render_dir, exist_ok=True)
    renders = {"idle": os.path.join(ns.render_dir, "idle-frame001.png"),
               "turn": os.path.join(ns.render_dir, "turn-frame030.png"),
               "click": os.path.join(ns.render_dir, "click-frame015.png")}
    if ns.render:
        render(scene, rig, idle, 1, renders["idle"])
        render(scene, rig, turn, 30, renders["turn"])
        render(scene, rig, click, 15, renders["click"])
    foot = footplant(rig, idle, (1, 45, 90))
    proximity = shoulder_head_proximity(rig, turn)
    rig.animation_data.action = idle
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ns.output))
    report = {"actions": {"Idle_90f": [1, 90], "Turn_60f": [1, 60], "Click_30f": [1, 30]},
              "fps": 30, "active_action": "Idle_90f", "active_frame": 1,
              "saved_scene_fps": scene.render.fps, "saved_scene_fps_base": scene.render.fps_base,
              "saved_scene_frame_range": [scene.frame_start, scene.frame_end],
              "idle_footplant_max_delta_m": foot,
              "turn_shoulder_head_sampled_min_distance_m": proximity,
              "renders": renders if ns.render else {},
              "limitations": ["Idle contains breath only; no Blink action/shape key is claimed.",
                              "Shoulder/head value is a sampled proximity diagnostic, not collision proof.",
                              "Click uses only the independently trialed 0..5-degree upper-arm and 0..14-degree forearm range; fingers remain unverified.",
                              "Fused-mesh distal fingers remain unweighted in this trial."]}
    with open(ns.report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


if __name__ == "__main__":
    main()
