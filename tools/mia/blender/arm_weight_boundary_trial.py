"""Isolated arm/sleeve weight-continuity trial for Mia v44.

The source file is read-only: this writes only a copied trial blend, two
single-pose renders, and a JSON report.  It does not attempt modelling.
"""
import argparse
from array import array
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
    parser.add_argument("--out-dir", required=True)
    return parser.parse_args(raw)


def arm_groups(obj, side):
    names = ["DEF_UpperArm_" + side, "DEF_Forearm_" + side, "DEF_Hand_" + side]
    return [obj.vertex_groups[name] for name in names], names


def weights(vertex, groups):
    by_index = {group.group: group.weight for group in vertex.groups}
    return [by_index.get(group.index, 0.0) for group in groups]


def set_pose_identity(rig):
    for bone in rig.pose.bones:
        bone.rotation_mode = 'QUATERNION'
        bone.location = (0, 0, 0)
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def suspend_animation(rig):
    """Disable the loaded all-bone Idle keys before a manual pose probe."""
    if rig.animation_data:
        rig.animation_data.action = None
        for track in rig.animation_data.nla_tracks:
            track.mute = True
    bpy.context.view_layer.update()


def local_world_rotation(bone, degrees):
    rest = bone.bone.matrix_local.to_3x3()
    world = Quaternion(Vector((1, 0, 0)), math.radians(degrees)).to_matrix()
    return (rest.inverted() @ world @ rest).to_quaternion()


def pose_click_probe(rig):
    suspend_animation(rig)
    set_pose_identity(rig)
    upper = rig.pose.bones["DEF_UpperArm_R"]
    fore = rig.pose.bones["DEF_Forearm_R"]
    upper.rotation_quaternion = local_world_rotation(upper, 5.0)
    fore.rotation_quaternion = local_world_rotation(fore, 14.0)
    bpy.context.view_layer.update()


def probe_motion_evidence(rig, body, baseline):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated_rig = rig.evaluated_get(dg)
    bones = {}
    for name in ("DEF_UpperArm_R", "DEF_Forearm_R"):
        rest = rig.matrix_world @ rig.data.bones[name].matrix_local
        current = evaluated_rig.matrix_world @ evaluated_rig.pose.bones[name].matrix
        bones[name] = max(abs(current[row][column] - rest[row][column])
                          for row in range(4) for column in range(4))
    moved = max((point - reference).length for point, reference in zip(evaluated_coords(body), baseline))
    result = {"evaluated_bone_matrix_max_abs_delta": bones,
              "evaluated_body_vertex_max_displacement_m": moved}
    if min(bones.values()) <= 1e-4 or moved <= .001:
        raise RuntimeError("Manual probe was not evaluated: " + json.dumps(result))
    return result


def render(scene, path):
    scene.camera = bpy.data.objects.get("QA_Camera_Front") or scene.camera
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 512, 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def image_diff_metrics(first, second):
    image_a = bpy.data.images.load(first, check_existing=False)
    image_b = bpy.data.images.load(second, check_existing=False)
    try:
        pixels_a = array('f', [0.0]) * (image_a.size[0] * image_a.size[1] * 4)
        pixels_b = array('f', [0.0]) * (image_b.size[0] * image_b.size[1] * 4)
        image_a.pixels.foreach_get(pixels_a)
        image_b.pixels.foreach_get(pixels_b)
        changed_pixels = sum(any(abs(pixels_a[i + channel] - pixels_b[i + channel]) > 1e-7
                                 for channel in range(4)) for i in range(0, len(pixels_a), 4))
        return {"changed_pixels": changed_pixels,
                "total_pixels": image_a.size[0] * image_a.size[1],
                "max_channel_delta": max(abs(a - b) for a, b in zip(pixels_a, pixels_b))}
    finally:
        bpy.data.images.remove(image_a, do_unlink=True)
        bpy.data.images.remove(image_b, do_unlink=True)


def adjacency(obj):
    result = [[] for _ in obj.data.vertices]
    for polygon in obj.data.polygons:
        ids = list(polygon.vertices)
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]
            result[a].append(b)
            result[b].append(a)
    return [list(set(values)) for values in result]


def smoothstep(x, left, right):
    t = max(0.0, min(1.0, (x - left) / (right - left)))
    return t * t * (3.0 - 2.0 * t)


def allowed(world):
    # This is a capsule-adjacent sleeve/cuff corridor, not the prior flat
    # |x|=.235 split.  A narrow central lower-torso island stays untouched.
    return .72 <= world.z <= 1.35 and abs(world.x) >= .14


def true_lower_torso_hem(world):
    # Preserve only the central lower cardigan/torso hem.  The old broad
    # .70-.95/|x|<=.24 rule swallowed inner cuff vertices beside the hand.
    return .70 <= world.z <= .88 and abs(world.x) <= .14


def direct_distribution(rig, side, world):
    groups = ["DEF_UpperArm_" + side, "DEF_Forearm_" + side, "DEF_Hand_" + side]
    distances = []
    for name in groups:
        bone = rig.data.bones[name]
        a = rig.matrix_world @ bone.head_local
        b = rig.matrix_world @ bone.tail_local
        direction = b - a
        t = max(0.0, min(1.0, (world - a).dot(direction) / direction.length_squared))
        distances.append((world - (a + direction * t)).length)
    raw = [1.0 / (distance + .008) ** 2 for distance in distances]
    total = sum(raw)
    return [value / total for value in raw]


def evaluated_coords(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    evaluation = obj.evaluated_get(dg)
    mesh = evaluation.to_mesh()
    try:
        return [evaluation.matrix_world @ vertex.co for vertex in mesh.vertices]
    finally:
        evaluation.to_mesh_clear()


def rest_delta(obj, rig):
    original = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    set_pose_identity(rig)
    bpy.context.evaluated_depsgraph_get().update()
    current = evaluated_coords(obj)
    return max((a - b).length for a, b in zip(current, original))


def arm_weight(vertex, group_indexes):
    data = {item.group: item.weight for item in vertex.groups}
    return sum(data.get(index, 0.0) for index in group_indexes)


def boundary_stats(obj, worlds, graph, indexes):
    values = [arm_weight(vertex, indexes) for vertex in obj.data.vertices]
    differences = []
    for index, neighbors in enumerate(graph):
        if not allowed(worlds[index]):
            continue
        for other in neighbors:
            if other > index and allowed(worlds[other]):
                differences.append(abs(values[index] - values[other]))
    return {
        "eligible_vertices": sum(allowed(world) for world in worlds),
        "edge_count": len(differences),
        "mean_arm_weight_edge_delta": sum(differences) / max(1, len(differences)),
        "hard_edges_over_0_8": sum(value > .8 for value in differences),
        "max_arm_weight_edge_delta": max(differences, default=0.0),
    }


def coincident_clusters(obj, worlds, tolerance=1e-5):
    buckets = {}
    for index, world in enumerate(worlds):
        if allowed(world):
            buckets.setdefault(tuple(round(value / tolerance) for value in world), []).append(index)
    clusters = []
    for indexes in buckets.values():
        if len(indexes) < 2:
            continue
        anchor = obj.data.vertices[indexes[0]].normal.normalized()
        if all(anchor.dot(obj.data.vertices[index].normal.normalized()) > .95 for index in indexes[1:]):
            clusters.append(indexes)
    return clusters


def seam_diagnostics(obj, worlds, arm_indexes):
    clusters = coincident_clusters(obj, worlds)
    differences = []
    for indexes in clusters:
        values = [arm_weight(obj.data.vertices[index], arm_indexes) for index in indexes]
        differences.append(max(values) - min(values))
    return {"coincident_same_normal_clusters": len(clusters),
            "clusters_with_arm_weight_difference": sum(value > 1e-5 for value in differences),
            "max_arm_weight_difference": max(differences, default=0.0)}


def equalize_coincident_weights(obj, worlds, deform_groups):
    """Tie only same-facing UV/normal seam copies; UV loops and topology remain intact."""
    clusters = coincident_clusters(obj, worlds)
    for indexes in clusters:
        averages = {}
        for group in deform_groups:
            values = [next((item.weight for item in obj.data.vertices[index].groups
                            if item.group == group.index), 0.0) for index in indexes]
            averages[group.index] = sum(values) / len(values)
        for index in indexes:
            for group in deform_groups:
                if averages[group.index] > 1e-8:
                    group.add([index], averages[group.index], 'REPLACE')
                else:
                    group.remove([index])
    return {"seam_clusters_equalized": len(clusters),
            "vertices_equalized": sum(len(indexes) for indexes in clusters)}


def smooth_arm_transition(obj, rig):
    graph = adjacency(obj)
    worlds = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    all_arm_indexes = []
    for side in ('L', 'R'):
        all_arm_indexes += [group.index for group in arm_groups(obj, side)[0]]
    before = boundary_stats(obj, worlds, graph, set(all_arm_indexes))
    values = [arm_weight(vertex, set(all_arm_indexes)) for vertex in obj.data.vertices]
    targets = list(values)
    for index, world in enumerate(worlds):
        if allowed(world):
            # A smooth spatial bridge replaces the old hard |x|=.235 candidate cut.
            # Cuffs are permitted to follow the hand; the central hem is not.
            left, right = (.14, .285) if world.z >= .96 else (.14, .255)
            targets[index] = max(values[index], smoothstep(abs(world.x), left, right))
    for _ in range(4):
        next_values = list(values)
        for index, world in enumerate(worlds):
            if not allowed(world):
                continue
            neighbors = [values[other] for other in graph[index] if allowed(worlds[other])]
            if neighbors:
                next_values[index] = max(targets[index], .60 * values[index] + .40 * sum(neighbors) / len(neighbors))
        values = next_values
    changed = 0
    for index, (vertex, world) in enumerate(zip(obj.data.vertices, worlds)):
        # Do not touch coat hem; it must remain torso-owned.
        if true_lower_torso_hem(world):
            continue
        if not allowed(world):
            continue
        side = 'L' if world.x >= 0 else 'R'
        groups, _ = arm_groups(obj, side)
        target = min(.98, values[index])
        previous = sum(weights(vertex, groups))
        if abs(target - previous) < 1e-5:
            continue
        distribution = direct_distribution(rig, side, world)
        non_arm = [(item.group, item.weight) for item in vertex.groups if item.group not in all_arm_indexes]
        other_total = sum(value for _, value in non_arm)
        # Preserve all non-arm relative weights, then make the arm contribution continuous.
        if other_total > 1e-8:
            scale = (1.0 - target) / other_total
            for group_index, value in non_arm:
                obj.vertex_groups[group_index].add([index], value * scale, 'REPLACE')
        for group, value in zip(groups, distribution):
            group.add([index], target * value, 'REPLACE')
        # Clear opposite-side arm groups. They should never receive this transition.
        for group in arm_groups(obj, 'R' if side == 'L' else 'L')[0]:
            group.remove([index])
        changed += 1
    # Assert hem stays clear even if malformed source weights existed.
    for index, world in enumerate(worlds):
        if true_lower_torso_hem(world):
            for side in ('L', 'R'):
                for group in arm_groups(obj, side)[0]:
                    group.remove([index])
    bpy.context.view_layer.update()
    seam_before = seam_diagnostics(obj, worlds, set(all_arm_indexes))
    seam_fix = equalize_coincident_weights(
        obj, worlds, [group for group in obj.vertex_groups if group.name.startswith("DEF_")])
    seam_after = seam_diagnostics(obj, worlds, set(all_arm_indexes))
    after = boundary_stats(obj, worlds, graph, set(all_arm_indexes))
    hem_indices = [i for i, world in enumerate(worlds) if true_lower_torso_hem(world)]
    hem_arm = sum(arm_weight(obj.data.vertices[i], set(all_arm_indexes)) > 1e-8 for i in hem_indices)
    return {"changed_vertices": changed, "before": before, "after": after,
            "coincident_seam_weights": {"before": seam_before, "fix": seam_fix, "after": seam_after},
            "coat_hem_vertices": len(hem_indices), "coat_hem_arm_weighted": hem_arm}


def connected_components(obj, worlds):
    graph = adjacency(obj)
    candidates = {i for i, world in enumerate(worlds) if allowed(world)}
    count, sizes = 0, []
    while candidates:
        count += 1
        stack = [candidates.pop()]
        size = 0
        while stack:
            item = stack.pop(); size += 1
            for other in graph[item]:
                if other in candidates:
                    candidates.remove(other); stack.append(other)
        sizes.append(size)
    return {"transition_components": count, "largest_component_vertices": max(sizes, default=0),
            "component_sizes_top5": sorted(sizes, reverse=True)[:5]}


def main():
    ns = args()
    os.makedirs(ns.out_dir, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(ns.input))
    body = bpy.data.objects["Mia_Graft_Body_Editable"]
    head = bpy.data.objects["Mia_Graft_Head_Editable"]
    rig = bpy.data.objects["Mia_RigMechanism"]
    scene = bpy.context.scene
    suspend_animation(rig)
    set_pose_identity(rig)
    rest_body = evaluated_coords(body)
    worlds = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
    components = connected_components(body, worlds)
    before_path = os.path.join(ns.out_dir, "before-original-weights-click-pose.png")
    after_path = os.path.join(ns.out_dir, "after-smoothed-weights-click-pose.png")
    pose_click_probe(rig)
    before_motion = probe_motion_evidence(rig, body, rest_body)
    render(scene, before_path)
    set_pose_identity(rig)
    smooth = smooth_arm_transition(body, rig)
    rest = rest_delta(body, rig)
    pose_click_probe(rig)
    after_motion = probe_motion_evidence(rig, body, rest_body)
    render(scene, after_path)
    visual_delta = image_diff_metrics(before_path, after_path)
    set_pose_identity(rig)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(ns.output))
    report = {
        "source": os.path.abspath(ns.input), "output": os.path.abspath(ns.output),
        "scope": "isolated arm/sleeve continuity test; not production rig or mesh repair",
        "component_diagnostics": components, "weight_smoothing": smooth,
        "rest_neutral_body_delta_m": rest,
        "probe": {"side": "R", "upperarm_world_x_degrees": 5.0, "forearm_world_x_degrees": 14.0},
        "actual_probe_evaluation": {"before": before_motion, "after": after_motion},
        "renders": {"before": "before-original-weights-click-pose.png", "after": "after-smoothed-weights-click-pose.png"},
        "rendered_pose_difference": visual_delta,
        "pass_mechanical": rest < 1e-4 and smooth["coat_hem_arm_weighted"] == 0,
        "limitations": ["Visual comparison is required; topology and fused fingers are unchanged.",
                        "This does not establish face, finger, collision, or production animation quality."]
    }
    with open(os.path.join(ns.out_dir, "arm-weight-boundary-report.json"), "w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
