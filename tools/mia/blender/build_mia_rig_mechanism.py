"""Non-destructive Mia rig-mechanism builder (Blender 5.2+).

This creates an armature and control mechanism only.  It deliberately never
parents, modifiers, or vertex groups a mesh: production binding is gated on a
separate final-input approval.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector


JOINTS = {
    "pelvis": (0.0, 0.0, 0.94), "spine": (0.0, 0.0, 1.08),
    "chest": (0.0, 0.0, 1.26), "neck": (0.0, 0.0, 1.39),
    "head": (0.0, 0.0, 1.50), "head_tip": (0.0, 0.0, 1.67),
    "shoulder_l": (0.18, -0.02, 1.31), "elbow_l": (0.26, 0.03, 1.085),
    "wrist_l": (0.32, 0.12, 0.87), "shoulder_r": (-0.18, -0.02, 1.31),
    "elbow_r": (-0.26, 0.03, 1.085), "wrist_r": (-0.32, 0.12, 0.87),
    "hip_l": (0.105, 0.0, 0.94), "knee_l": (0.105, -0.02, 0.50),
    "ankle_l": (0.105, 0.0, 0.17), "toe_l": (0.105, -0.22, 0.08),
    "hip_r": (-0.105, 0.0, 0.94), "knee_r": (-0.105, -0.02, 0.50),
    "ankle_r": (-0.105, 0.0, 0.17), "toe_r": (-0.105, -0.22, 0.08),
}


def argv():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--mechanism-check", action="store_true")
    p.add_argument("--report", default="")
    return p.parse_args(args)


def point(v):
    return Vector(v)


def remove_our_rig():
    old = bpy.data.objects.get("Mia_RigMechanism")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)


def make_rig():
    remove_our_rig()
    data = bpy.data.armatures.new("Mia_RigMechanism")
    rig = bpy.data.objects.new("Mia_RigMechanism", data)
    bpy.context.scene.collection.objects.link(rig)
    rig["rig_type"] = "Mia FK/IK mechanism - unbound"
    rig["binding_gate"] = "FINAL_PROJECTED_INPUT_REQUIRED"
    rig["height_m"] = 1.68
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    def eb(name, head, tail, parent=None, deform=True):
        b = data.edit_bones.new(name)
        b.head, b.tail, b.use_deform = point(head), point(tail), deform
        if parent:
            b.parent = data.edit_bones[parent]
        return b

    eb("DEF_Root", (0, 0, 0), JOINTS["pelvis"], deform=False)
    eb("DEF_Pelvis", JOINTS["pelvis"], JOINTS["spine"], "DEF_Root")
    eb("DEF_Spine", JOINTS["spine"], JOINTS["chest"], "DEF_Pelvis")
    eb("DEF_Chest", JOINTS["chest"], JOINTS["neck"], "DEF_Spine")
    eb("DEF_Neck", JOINTS["neck"], JOINTS["head"], "DEF_Chest")
    eb("DEF_Head", JOINTS["head"], JOINTS["head_tip"], "DEF_Neck")
    # Small head children reserved for conservative lower-hair lag weighting.
    eb("DEF_HairLower_L", (0.10, 0.04, 1.55), (0.14, 0.08, 1.40), "DEF_Head")
    eb("DEF_HairLower_R", (-0.10, 0.04, 1.55), (-0.14, 0.08, 1.40), "DEF_Head")
    for side in ("L", "R"):
        s = side.lower()
        eb("DEF_Clavicle_" + side, JOINTS["chest"], JOINTS["shoulder_" + s], "DEF_Chest")
        eb("DEF_UpperArm_" + side, JOINTS["shoulder_" + s], JOINTS["elbow_" + s], "DEF_Clavicle_" + side)
        eb("DEF_Forearm_" + side, JOINTS["elbow_" + s], JOINTS["wrist_" + s], "DEF_UpperArm_" + side)
        hand_tail = point(JOINTS["wrist_" + s]) + Vector((0, -0.005, -0.045))
        eb("DEF_Hand_" + side, JOINTS["wrist_" + s], hand_tail, "DEF_Forearm_" + side)
        # Source A-pose hands hang down: thumb angles outward; other fingers are
        # short (7.5cm total) vertical chains, with a small relaxed spread.
        for fi, label in enumerate(("Thumb", "Index", "Middle", "Ring", "Pinky")):
            base = point(JOINTS["wrist_" + s]) + Vector(((0.010 if side == "L" else -0.010) * (2 - fi), 0.0, -0.040))
            direction = Vector(((0.016 if side == "L" else -0.016) if fi == 0 else 0,
                                -0.003, -0.018 if fi == 0 else -0.025))
            parent = "DEF_Hand_" + side
            for phalanx in range(1, 4):
                end = base + direction
                eb("DEF_%s_%s_%02d" % (label, side, phalanx), base, end, parent)
                parent, base = "DEF_%s_%s_%02d" % (label, side, phalanx), end
        eb("DEF_Thigh_" + side, JOINTS["hip_" + s], JOINTS["knee_" + s], "DEF_Pelvis")
        eb("DEF_Shin_" + side, JOINTS["knee_" + s], JOINTS["ankle_" + s], "DEF_Thigh_" + side)
        eb("DEF_Foot_" + side, JOINTS["ankle_" + s], JOINTS["toe_" + s], "DEF_Shin_" + side)
        eb("DEF_Toe_" + side, JOINTS["toe_" + s], point(JOINTS["toe_" + s]) + Vector((0, -0.08, 0)), "DEF_Foot_" + side)
        # Non-deforming controls; foot control is exactly the DEF foot's rest transform.
        eb("CTRL_Foot_" + side, JOINTS["ankle_" + s], JOINTS["toe_" + s], "DEF_Root", False)
        pole = point(JOINTS["knee_" + s]) + Vector((0, -0.50, 0))
        eb("CTRL_KneePole_" + side, pole, pole + Vector((0, 0, 0.12)), "DEF_Root", False)
        wrist = point(JOINTS["wrist_" + s])
        eb("CTRL_HandIK_" + side, wrist, wrist + Vector((0, -0.005, -0.045)), "DEF_Root", False)
        elbow_pole = point(JOINTS["elbow_" + s]) + Vector((0, -0.38, 0))
        eb("CTRL_ElbowPole_" + side, elbow_pole, elbow_pole + Vector((0, 0, 0.10)), "DEF_Root", False)
    bpy.ops.object.mode_set(mode="POSE")
    # Collections make DEF and CTRL selection explicit without changing mesh data.
    defs = data.collections.new("DEF")
    ctrls = data.collections.new("CTRL")
    for bone in data.bones:
        (ctrls if bone.name.startswith("CTRL_") else defs).assign(bone)
    for side in ("L", "R"):
        shin = rig.pose.bones["DEF_Shin_" + side]
        ik = shin.constraints.new("IK")
        ik.name, ik.target, ik.subtarget = "IK_Foot_" + side, rig, "CTRL_Foot_" + side
        ik.chain_count, ik.use_stretch, ik.use_tail = 2, False, True
        ik.pole_target, ik.pole_subtarget = rig, "CTRL_KneePole_" + side
        shin["neutral_pole_angle_candidates"] = "0,+pi/2,-pi/2,pi"
        foot = rig.pose.bones["DEF_Foot_" + side]
        rot = foot.constraints.new("COPY_ROTATION")
        rot.name, rot.target, rot.subtarget = "CopyRestFootRotation_" + side, rig, "CTRL_Foot_" + side
        rot.owner_space, rot.target_space, rot.mix_mode = 'WORLD', 'WORLD', 'REPLACE'
        arm = rig.pose.bones["DEF_Forearm_" + side]
        handik = arm.constraints.new("IK")
        handik.name, handik.target, handik.subtarget = "Optional_IK_Hand_" + side, rig, "CTRL_HandIK_" + side
        handik.chain_count, handik.use_stretch, handik.influence = 2, False, 0.0
        handik.pole_target, handik.pole_subtarget = rig, "CTRL_ElbowPole_" + side
        arm["optional_ik_enable_manually"] = True
    rig["arm_ik_default"] = "FK (Optional_IK_Hand influence=0)"
    rig["leg_ik_default"] = "ON; targets aligned to rest ankles"
    bpy.ops.object.mode_set(mode="OBJECT")
    return rig


def evaluated_point(rig, bone, tail=False):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = rig.evaluated_get(dg)
    p = evaluated.pose.bones[bone].tail if tail else evaluated.pose.bones[bone].head
    return evaluated.matrix_world @ p


def mechanism_check(rig):
    bpy.context.view_layer.update()
    candidates = (0.0, math.pi / 2, -math.pi / 2, math.pi)
    selected = {}
    checks = {}
    for side in ("L", "R"):
        ik = rig.pose.bones["DEF_Shin_" + side].constraints["IK_Foot_" + side]
        target = point(JOINTS["ankle_" + side.lower()])
        best = None
        for angle in candidates:
            ik.pole_angle = angle
            bpy.context.view_layer.update()
            ankle_error = (evaluated_point(rig, "DEF_Foot_" + side) - target).length
            knee_error = (evaluated_point(rig, "DEF_Shin_" + side) - point(JOINTS["knee_" + side.lower()])).length
            foot_tail_error = (evaluated_point(rig, "DEF_Foot_" + side, True) - point(JOINTS["toe_" + side.lower()])).length
            score = max(ankle_error, knee_error, foot_tail_error)
            if best is None or score < best[0]:
                best = (score, angle, ankle_error, knee_error, foot_tail_error)
        _, angle, ankle_error, knee_error, foot_tail_error = best
        ik.pole_angle = angle
        selected[side] = angle
        checks[side] = {"ankle_head_delta_m": ankle_error, "knee_head_delta_m": knee_error,
                        "foot_tail_delta_m": foot_tail_error, "pole_angle_rad": angle}
    bpy.context.view_layer.update()
    max_delta = max(value for side in checks.values() for key, value in side.items() if key.endswith("_m"))
    return {"pass": max_delta < 1.0e-4, "max_rest_bone_head_tail_delta_m": max_delta,
            "controls": {"foot_ik": "on", "arm_ik": "off (FK default)"}, "leg_checks": checks}


def mesh_safety_inventory():
    """Evidence that this checkpoint has not touched production mesh binding."""
    inventory = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH' and (obj.name.startswith("Mia_Graft_") or "ARCHIVE" in obj.name.upper()):
            inventory.append({"name": obj.name, "parent": obj.parent.name if obj.parent else None,
                              "armature_modifiers": [m.name for m in obj.modifiers if m.type == 'ARMATURE'],
                              "vertex_groups": len(obj.vertex_groups), "hidden": obj.hide_render})
    return inventory


def main():
    ns = argv()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ns.input))
    rig = make_rig()
    result = {"input": os.path.abspath(ns.input), "output": os.path.abspath(ns.output),
              "joint_coordinates_m": JOINTS, "mesh_safety_inventory": mesh_safety_inventory(),
              "unverified": ["No mesh weights are created at this mechanism checkpoint.",
                             "Face shape keys and actions await final projected/graft input gate.",
                             "No render, animation, or visual blink proof was requested/run."]}
    if ns.mechanism_check:
        result["mechanism_check"] = mechanism_check(rig)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ns.output))
    report = ns.report or os.path.splitext(ns.output)[0] + "-mechanism-report.json"
    with open(report, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    if ns.mechanism_check and not result["mechanism_check"]["pass"]:
        raise RuntimeError("Neutral foot IK mechanism check failed: " + json.dumps(result["mechanism_check"]))


if __name__ == "__main__":
    main()
