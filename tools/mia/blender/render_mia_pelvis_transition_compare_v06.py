"""Isolate source, derived-rest and derived-A-pose pelvis contours."""
import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def matte():
    material = bpy.data.materials.new("MIA_PELVIS_COMPARE_CLAY")
    material.diffuse_color = (.44, .49, .55, 1)
    material.use_nodes = True
    node = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value = (.44, .49, .55, 1)
    node.inputs["Roughness"].default_value = .85
    return material


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(scene):
    data = bpy.data.cameras.new("MIA_PELVIS_COMPARE_CAMERA")
    data.type = "ORTHO"; data.ortho_scale = .86
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj); scene.camera = obj
    return obj


def lights(scene):
    for index, (loc, energy) in enumerate((((2.0, -3.0, 2.1), 190), ((-2.0, -1.5, 1.4), 90), ((0, 2.5, 2.0), 110))):
        data = bpy.data.lights.new("MIA_PELVIS_COMPARE_LIGHT_%d" % index, "AREA")
        data.energy = energy; data.shape = "DISK"; data.size = 1.8
        obj = bpy.data.objects.new(data.name, data); scene.collection.objects.link(obj)
        obj.location = loc; aim(obj, (0, 0, .91))


def reset_pose(rig):
    for bone in rig.pose.bones:
        bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = (1, 0, 0, 0)
        bone.location = (0, 0, 0); bone.scale = (1, 1, 1)


def set_a_pose(rig):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_mia_body_head_v06 import set_reference_a_pose
    set_reference_a_pose(rig)


def bounds_evaluated(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return [[min(point[i] for point in points) for i in range(3)], [max(point[i] for point in points) for i in range(3)]]


def main():
    args = parse(); output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=args.input)
    scene = bpy.context.scene; scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"; scene.world.color = (.012, .015, .022)
    source = bpy.data.objects["Mia_Body_Anatomy_Skin"]
    derived = bpy.data.objects["MIA_V06_BODY_SKIN"]
    rig = bpy.data.objects["MIA_V06_RIG"]
    clay = matte()
    for obj in scene.objects:
        obj.hide_render = obj.type == "MESH"
    for obj in (source, derived):
        obj.data.materials.clear(); obj.data.materials.append(clay)
    cam = camera(scene); lights(scene)
    variants = (("source_rest", source, "rest"), ("derived_rest", derived, "rest"), ("derived_a_pose", derived, "a"))
    report = {}
    for name, active, pose in variants:
        reset_pose(rig)
        if pose == "a": set_a_pose(rig)
        bpy.context.view_layer.update()
        source.hide_render = active != source; derived.hide_render = active != derived
        report[name] = {"bounds_evaluated_world": bounds_evaluated(active)}
        for view, loc in (("profile", (-3.2, -0.0, 1.00)), ("three_quarter", (-2.3, -2.3, 1.00))):
            cam.location = loc; aim(cam, (0, 0, .91)); scene.render.filepath = str(output / (name + "_" + view + ".png")); bpy.ops.render.render(write_still=True)
    reset_pose(rig); bpy.context.view_layer.update()
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
