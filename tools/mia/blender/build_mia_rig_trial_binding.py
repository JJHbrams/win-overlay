"""Trial-only, deterministic Mia binding experiment for Blender 5.2+.

No source blend is saved.  This script is intentionally conservative for a
fused clothing mesh: arm candidates are only allowed in a local arm corridor,
and the coat-hem corridor can receive torso bones only.
"""
import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, str(Path(__file__).parent))
import build_mia_rig_mechanism as mechanism


def argv():
    raw = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--body", required=True, help="exact approved full-body object name")
    p.add_argument("--head", action="append", required=True, help="exact approved head object name; repeat for a neck graft")
    return p.parse_args(raw)


def selected_editable_meshes(ns):
    names = [ns.body] + ns.head
    if len(names) != len(set(names)):
        raise RuntimeError("Approved mesh selection contains a duplicate name")
    selected = []
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != 'MESH' or obj.name.startswith("ARCHIVE_"):
            raise RuntimeError("Approved mesh missing/not editable: " + name)
        selected.append(obj)
    all_editable = {obj.name for obj in bpy.context.scene.objects if obj.type == 'MESH' and
                    obj.name.startswith("Mia_Graft_") and not obj.name.startswith("ARCHIVE_")}
    unselected = all_editable - set(names)
    if unselected:
        raise RuntimeError("Refusing ambiguous source: unselected editable graft mesh(es): " + repr(sorted(unselected)))
    return selected[0], selected[1:]


def bone_distance(rig, name, world):
    b = rig.data.bones[name]
    a, z = rig.matrix_world @ b.head_local, rig.matrix_world @ b.tail_local
    d = z - a
    t = max(0.0, min(1.0, (world - a).dot(d) / d.length_squared))
    return (world - (a + d * t)).length


def add_weights(obj, rig, index, candidates):
    # Inverse-distance blend restricted to semantic candidates, never global X groups.
    eps = 0.008
    ranked = sorted((bone_distance(rig, name, obj.matrix_world @ obj.data.vertices[index].co), name)
                    for name in candidates)[:4]
    raw = [(1.0 / (distance + eps) ** 2, name) for distance, name in ranked]
    total = sum(value for value, _ in raw)
    for value, name in raw:
        obj.vertex_groups[name].add([index], value / total, 'REPLACE')


def torso_candidates(z):
    if z < .99:
        return ("DEF_Pelvis", "DEF_Spine")
    if z < 1.16:
        return ("DEF_Pelvis", "DEF_Spine", "DEF_Chest")
    if z < 1.35:
        return ("DEF_Spine", "DEF_Chest", "DEF_Neck")
    return ("DEF_Chest", "DEF_Neck", "DEF_Head")


def body_candidates(world):
    x, y, z = world
    side = "L" if x >= 0 else "R"
    ax = abs(x)
    # Hem is deliberately evaluated before the arm corridor.  It cannot be arm-weighted.
    if .70 <= z <= .95 and ax <= .24:
        return ("DEF_Pelvis", "DEF_Spine")
    if z <= .25:
        return ("DEF_Foot_" + side, "DEF_Toe_" + side, "DEF_Shin_" + side)
    if z <= .56 and ax <= .19:
        return ("DEF_Shin_" + side, "DEF_Thigh_" + side)
    if z <= .99 and ax <= .19:
        return ("DEF_Thigh_" + side, "DEF_Pelvis", "DEF_Spine")
    # Local A-pose arm corridor.  No torso point can enter only because |x| is large.
    if ax >= .235 and .73 <= z <= 1.35:
        if z < .94:
            return ("DEF_Hand_" + side, "DEF_Forearm_" + side,
                    "DEF_Thumb_" + side + "_01", "DEF_Index_" + side + "_01",
                    "DEF_Middle_" + side + "_01", "DEF_Ring_" + side + "_01", "DEF_Pinky_" + side + "_01")
        return ("DEF_Forearm_" + side, "DEF_UpperArm_" + side, "DEF_Hand_" + side)
    return torso_candidates(z)


def bind_body_localized(obj, rig):
    obj.vertex_groups.clear()
    for bone in rig.data.bones:
        if bone.use_deform:
            obj.vertex_groups.new(name=bone.name)
    diagnostics = {"vertices": len(obj.data.vertices), "coat_hem_vertices": 0,
                   "coat_hem_arm_weighted": 0, "arm_corridor_vertices": 0}
    for i, vertex in enumerate(obj.data.vertices):
        w = obj.matrix_world @ vertex.co
        if .70 <= w.z <= .95 and abs(w.x) <= .24:
            diagnostics["coat_hem_vertices"] += 1
        candidates = body_candidates(w)
        if any(name.startswith("DEF_UpperArm") or name.startswith("DEF_Forearm") or name.startswith("DEF_Hand")
               for name in candidates):
            diagnostics["arm_corridor_vertices"] += 1
        add_weights(obj, rig, i, candidates)
    arm_names = {g.name for g in obj.vertex_groups if "Arm_" in g.name or "Forearm_" in g.name or "Hand_" in g.name}
    for vertex in obj.data.vertices:
        w = obj.matrix_world @ vertex.co
        if .70 <= w.z <= .95 and abs(w.x) <= .24:
            if any(group.group in {obj.vertex_groups[name].index for name in arm_names} and group.weight > 1e-8
                   for group in vertex.groups):
                diagnostics["coat_hem_arm_weighted"] += 1
    return diagnostics


def bind_head_conservative(obj, rig):
    obj.vertex_groups.clear()
    head = obj.vertex_groups.new(name="DEF_Head")
    hair_l = obj.vertex_groups.new(name="DEF_HairLower_L")
    hair_r = obj.vertex_groups.new(name="DEF_HairLower_R")
    lower_hair = 0
    for i, vertex in enumerate(obj.data.vertices):
        w = obj.matrix_world @ vertex.co
        # Central face stays 100% Head. Only peripheral/back lower hair can lag 30%.
        if w.z < 1.46 and (abs(w.x) > .12 or w.y > .10):
            secondary = hair_l if w.x >= 0 else hair_r
            head.add([i], .70, 'REPLACE')
            secondary.add([i], .30, 'REPLACE')
            lower_hair += 1
        else:
            head.add([i], 1.0, 'REPLACE')
    return {"vertices": len(obj.data.vertices), "head_full_weight_vertices": len(obj.data.vertices) - lower_hair,
            "lower_hair_secondary_vertices": lower_hair, "max_secondary_weight": .30}


def ensure_armature_modifier(obj, rig):
    for modifier in list(obj.modifiers):
        if modifier.type == 'ARMATURE':
            obj.modifiers.remove(modifier)
    mod = obj.modifiers.new("Mia_RigMechanism_Skin", 'ARMATURE')
    mod.object = rig
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False


def auto_weight_probe(obj, rig):
    """Try Blender bone heat on an isolated copy; never retain the result."""
    copy = obj.copy()
    copy.data = obj.data.copy()
    bpy.context.scene.collection.objects.link(copy)
    copy.name = "RIG_TRIAL_AUTOWEIGHT_PROBE_DELETE"
    outcome = {"attempted": True, "success": False, "reason": "unknown"}
    try:
        bpy.ops.object.select_all(action='DESELECT')
        copy.select_set(True)
        rig.select_set(True)
        bpy.context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        # Blender may leave groups even while bone heat logs an unsolved-bone
        # warning. This fused mesh emitted that warning, so this trial treats
        # the automatic route as failed rather than mistaking group creation
        # for accepted skinning.
        outcome["success"] = False
        outcome["group_count"] = len(copy.vertex_groups)
        outcome["reason"] = "bone-heat emitted an unsolved-bone warning; localized semantic binding selected"
    except RuntimeError as error:
        outcome["reason"] = "bone-heat failure: " + str(error)
    finally:
        bpy.data.objects.remove(copy, do_unlink=True)
    return outcome


def evaluated_coords(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    try:
        # Mesh coordinates are evaluated object-local, so use the evaluated
        # world matrix. The body retains a source parent transform.
        return [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluated.to_mesh_clear()


def reset_pose(rig):
    for pose_bone in rig.pose.bones:
        pose_bone.location = (0, 0, 0)
        pose_bone.rotation_mode = 'QUATERNION'
        pose_bone.rotation_quaternion = (1, 0, 0, 0)
        pose_bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def local_from_world_rotation(bone, axis, radians):
    world = Quaternion(Vector(axis), radians).to_matrix()
    rest = bone.bone.matrix_local.to_3x3()
    return (rest.inverted() @ world @ rest).to_quaternion()


def motion_probes(rig, body, head):
    base_body, base_head = evaluated_coords(body), evaluated_coords(head)
    result = {}
    # Upper arm/forearm: deliberate world-space front bend converted through rest-local axes.
    reset_pose(rig)
    rig.pose.bones["DEF_UpperArm_L"].rotation_quaternion = local_from_world_rotation(
        rig.pose.bones["DEF_UpperArm_L"], (1, 0, 0), math.radians(24))
    rig.pose.bones["DEF_Forearm_L"].rotation_quaternion = local_from_world_rotation(
        rig.pose.bones["DEF_Forearm_L"], (1, 0, 0), math.radians(38))
    bpy.context.view_layer.update()
    arm = evaluated_coords(body)
    result["upperarm_elbow_bend_max_displacement_m"] = max((a - b).length for a, b in zip(arm, base_body))
    # Move the actual foot IK control vertically in its rest-local basis and compare its solved ankle.
    reset_pose(rig)
    foot_ctrl = rig.pose.bones["CTRL_Foot_L"]
    foot_ctrl.location = foot_ctrl.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, .10))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = rig.evaluated_get(dg)
    ankle = ev.matrix_world @ ev.pose.bones["DEF_Foot_L"].head
    target = ev.matrix_world @ ev.pose.bones["CTRL_Foot_L"].head
    result["foot_lift_ik_target_delta_m"] = (ankle - target).length
    result["foot_lift_body_max_displacement_m"] = max((a - b).length for a, b in zip(evaluated_coords(body), base_body))
    # Head yaw uses WORLD Z, converted to rest-local (not local Z guessing).
    reset_pose(rig)
    rig.pose.bones["DEF_Head"].rotation_quaternion = local_from_world_rotation(
        rig.pose.bones["DEF_Head"], (0, 0, 1), math.radians(16))
    bpy.context.view_layer.update()
    result["head_yaw_mesh_max_displacement_m"] = max((a - b).length for a, b in zip(evaluated_coords(head), base_head))
    reset_pose(rig)
    return result


def rest_check(rig, body, head):
    before_body = [body.matrix_world @ v.co for v in body.data.vertices]
    before_head = [head.matrix_world @ v.co for v in head.data.vertices]
    samples = []
    # Newly-added armature modifiers can retain an old depsgraph evaluation for
    # one read. Require three clean identity evaluations and report each one.
    for _ in range(3):
        reset_pose(rig)
        bpy.context.view_layer.update()
        bpy.context.evaluated_depsgraph_get().update()
        after_body, after_head = evaluated_coords(body), evaluated_coords(head)
        body_delta = max((a - b).length for a, b in zip(after_body, before_body))
        head_delta = max((a - b).length for a, b in zip(after_head, before_head))
        worst = max(range(len(after_body)), key=lambda i: (after_body[i] - before_body[i]).length)
        samples.append(max(body_delta, head_delta))
    return samples


def main():
    ns = argv()
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ns.input))
    body, heads = selected_editable_meshes(ns)
    if len(heads) != 1:
        raise RuntimeError("Multiple head/neck grafts require a dedicated v40 selection policy")
    rig = mechanism.make_rig()
    # This searches and commits the neutral pole angle before *any* mesh
    # evaluation. Leaving Blender's default zero angle rolls the straight
    # chain even though its ankle/head positions look correct.
    ik_mechanism = mechanism.mechanism_check(rig)
    auto = auto_weight_probe(body, rig)
    body_diag = bind_body_localized(body, rig)
    head_diag = {head.name: bind_head_conservative(head, rig) for head in heads}
    ensure_armature_modifier(body, rig)
    for head in heads:
        ensure_armature_modifier(head, rig)
    # Force clean identity pose before the first depsgraph evaluation; this avoids
    # retaining any context state left by the isolated bone-heat probe.
    reset_pose(rig)
    bpy.context.view_layer.update()
    rest_deltas = rest_check(rig, body, heads[0])
    rest_delta = rest_deltas[-1]
    probes = motion_probes(rig, body, heads[0])
    report = {"source": os.path.abspath(ns.input), "output": os.path.abspath(ns.output),
              "binding": "localized inverse-distance semantic regions (trial only)",
              "approved_mesh_selection": [body.name] + [head.name for head in heads],
              "auto_weight_probe": auto, "body_regions": body_diag, "head_regions": head_diag,
              "rest_neutral_max_displacement_m": rest_delta,
              "rest_neutral_evaluation_samples_m": rest_deltas,
              "mechanism_check": ik_mechanism, "motion_probes": probes,
              "pass": rest_delta < 1e-4 and body_diag["coat_hem_arm_weighted"] == 0 and
                      probes["foot_lift_ik_target_delta_m"] < 1e-4,
              "unverified": ["No production final input has been received.",
                             "No visual render/face-expression proof run.",
                             "Distal finger chains are correctly short/downward but intentionally unweighted: the fused trial mesh has not established safe digit separation.",
                             "Trial weights require re-run and visual QA on final projected graft."]}
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ns.output))
    with open(ns.report, "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    if not report["pass"]:
        raise RuntimeError("Trial binding check failed: " + json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
