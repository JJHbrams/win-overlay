"""Project the supplied original-art face region onto an existing Pixal head mesh.

This script changes UV/attribute/material data only.  It deliberately never edits
vertices, edges, or polygons, and asserts that invariant before saving.
"""
import argparse
import hashlib
import json
import math
import os
import sys
from array import array

import bpy
from mathutils import Vector


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--art", required=True)
    parser.add_argument("--uv-scale", type=float, default=1.0)
    parser.add_argument("--offset-u", type=float, default=0.0)
    parser.add_argument("--offset-v", type=float, default=0.0)
    parser.add_argument("--strength", type=float, default=1.0)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def fingerprint():
    digest = hashlib.sha256()
    totals = [0, 0]
    for obj in sorted((o for o in bpy.data.objects if o.type == "MESH"), key=lambda o: o.name):
        digest.update(obj.name.encode("utf8"))
        digest.update(("%d/%d;" % (len(obj.data.vertices), len(obj.data.polygons))).encode())
        totals[0] += len(obj.data.vertices)
        totals[1] += len(obj.data.polygons)
        coordinates = array("f", [0.0]) * (len(obj.data.vertices) * 3)
        obj.data.vertices.foreach_get("co", coordinates)
        for index in range(0, len(coordinates), 3):
            digest.update(("%.9f,%.9f,%.9f;" % (coordinates[index], coordinates[index + 1], coordinates[index + 2])).encode())
    return {"sha256": digest.hexdigest(), "vertices": totals[0], "polygons": totals[1]}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def smoothstep(edge0, edge1, value):
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    x = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def ellipse_weight(u, v, center_u, center_v, radius_u, radius_v, feather=0.14):
    distance = math.sqrt(((u - center_u) / radius_u) ** 2 + ((v - center_v) / radius_v) ** 2)
    return 1.0 - smoothstep(1.0 - feather, 1.0, distance)


def find_mesh_and_root():
    mesh = bpy.data.objects.get("Mesh_0")
    if mesh is None or mesh.type != "MESH":
        meshes = [obj for obj in bpy.data.objects if obj.type == "MESH"]
        if len(meshes) != 1:
            raise RuntimeError("Expected Mesh_0 (or exactly one mesh), found: " + ", ".join(o.name for o in meshes))
        mesh = meshes[0]
    roots = [obj for obj in bpy.data.objects if obj.type == "EMPTY" and obj.name.upper().endswith("ROOT")]
    if len(roots) != 1:
        raise RuntimeError("Expected exactly one ROOT empty, found: " + ", ".join(o.name for o in roots))
    return mesh, roots[0]


def add_projection_coordinates(mesh, root, scale, offset_u, offset_v):
    uv_layer = mesh.data.uv_layers.get("UV_PROJ_FRONT") or mesh.data.uv_layers.new(name="UV_PROJ_FRONT")
    weight = mesh.data.attributes.get("FaceProjectionWeight")
    if weight is None:
        weight = mesh.data.attributes.new("FaceProjectionWeight", "FLOAT", "POINT")
    if weight.domain != "POINT":
        raise RuntimeError("FaceProjectionWeight exists with unsupported domain " + weight.domain)
    root_inverse = root.matrix_world.inverted()
    canonical_transform = root_inverse @ mesh.matrix_world
    normal_transform = root_inverse.to_3x3() @ mesh.matrix_world.to_3x3()
    tangent = math.tan(math.radians(10.0))
    count = len(mesh.data.vertices)
    coordinates = array("f", [0.0]) * (count * 3)
    normals = array("f", [0.0]) * (count * 3)
    mesh.data.vertices.foreach_get("co", coordinates)
    mesh.data.vertices.foreach_get("normal", normals)
    points = array("f", [0.0]) * (count * 2)
    weights = array("f", [0.0]) * count
    for index in range(count):
        base = index * 3
        point = canonical_transform @ Vector((coordinates[base], coordinates[base + 1], coordinates[base + 2]))
        depth = point.y + 3.1192050007897403
        if depth <= 0:
            raise RuntimeError("A vertex lies behind the specified front camera")
        u = 0.5 + point.x / (2.0 * depth * tangent)
        v = 0.5 + point.z / (2.0 * depth * tangent)
        # Calibration is intentionally explicit/CLI-controlled rather than guessed.
        u = 0.5 + (u - 0.5) * scale + offset_u
        v = 0.5 + (v - 0.5) * scale + offset_v
        normal = (normal_transform @ Vector((normals[base], normals[base + 1], normals[base + 2]))).normalized()
        frontal = smoothstep(0.15, 0.65, -normal.y)
        face = ellipse_weight(u, v, 0.5, 0.65, 0.20, 0.21)
        neck = ellipse_weight(u, v, 0.5, 0.43, 0.13, 0.17)
        weights[index] = max(face, neck) * frontal
        points[index * 2] = u
        points[index * 2 + 1] = v
    weight.data.foreach_set("value", weights)
    loop_count = len(mesh.data.loops)
    loop_vertices = array("i", [0]) * loop_count
    mesh.data.loops.foreach_get("vertex_index", loop_vertices)
    loop_uvs = array("f", [0.0]) * (loop_count * 2)
    for loop_index, vertex_index in enumerate(loop_vertices):
        loop_uvs[loop_index * 2] = points[vertex_index * 2]
        loop_uvs[loop_index * 2 + 1] = points[vertex_index * 2 + 1]
    uv_layer.data.foreach_set("uv", loop_uvs)
    return uv_layer.name


def base_color_socket(material):
    if not material or not material.use_nodes:
        raise RuntimeError("Mesh lacks a node-based PBR material")
    principled = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    if principled is None:
        raise RuntimeError("PBR Principled node missing in " + material.name)
    return principled, principled.inputs["Base Color"]


def connect_projection_material(material, art_image, uv_name, strength):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled, base = base_color_socket(material)
    # Preserve the actual existing albedo branch before changing Base Color.
    original = base.links[0].from_socket if base.links else None
    if original is None:
        original_color = base.default_value[:]
    else:
        original_color = None
    for node in list(nodes):
        if node.name.startswith("Mia Original Art Projection"):
            nodes.remove(node)
    uv = nodes.new("ShaderNodeUVMap"); uv.name = "Mia Original Art Projection UV"; uv.uv_map = uv_name
    texture = nodes.new("ShaderNodeTexImage"); texture.name = "Mia Original Art Projection"; texture.image = art_image; texture.extension = "CLIP"; texture.interpolation = "Linear"
    attribute = nodes.new("ShaderNodeAttribute"); attribute.name = "Mia Original Art Projection Weight"; attribute.attribute_name = "FaceProjectionWeight"
    rgb_to_bw = nodes.new("ShaderNodeRGBToBW"); rgb_to_bw.name = "Mia Original Art Projection Foreground"
    foreground = nodes.new("ShaderNodeMath"); foreground.name = "Mia Original Art Projection Nonblack"; foreground.operation = "GREATER_THAN"; foreground.inputs[1].default_value = 0.0001
    weighted = nodes.new("ShaderNodeMath"); weighted.name = "Mia Original Art Projection Mask"; weighted.operation = "MULTIPLY"
    weighted_strength = nodes.new("ShaderNodeMath"); weighted_strength.name = "Mia Original Art Projection Strength"; weighted_strength.operation = "MULTIPLY"; weighted_strength.inputs[1].default_value = max(0.0, min(1.0, strength))
    mix = nodes.new("ShaderNodeMixRGB"); mix.name = "Mia Original Art Projection Mix"; mix.blend_type = "MIX"; mix.inputs[0].default_value = 1.0
    links.new(uv.outputs["UV"], texture.inputs["Vector"])
    links.new(texture.outputs["Color"], rgb_to_bw.inputs["Color"])
    links.new(rgb_to_bw.outputs["Val"], foreground.inputs[0])
    links.new(attribute.outputs["Fac"], weighted.inputs[0])
    links.new(foreground.outputs["Value"], weighted.inputs[1])
    links.new(weighted.outputs["Value"], weighted_strength.inputs[0])
    links.new(weighted_strength.outputs["Value"], mix.inputs[0])
    if original:
        links.new(original, mix.inputs[1])
    else:
        mix.inputs[1].default_value = original_color
    links.new(texture.outputs["Color"], mix.inputs[2])
    for link in list(base.links):
        links.remove(link)
    links.new(mix.outputs["Color"], base)
    return {"material": material.name, "base_albedo_source": original.node.name if original else "Principled default", "projection_image": art_image.name}


def main():
    args = arguments()
    source = os.path.abspath(args.input)
    output = os.path.abspath(args.output)
    art_path = os.path.abspath(args.art)
    if not os.path.isfile(source) or not os.path.isfile(art_path):
        raise FileNotFoundError("Missing input blend or original-art PNG")
    os.makedirs(os.path.dirname(output), exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=source)
    bpy.context.view_layer.update()
    before = fingerprint()
    mesh, root = find_mesh_and_root()
    uv_name = add_projection_coordinates(mesh, root, args.uv_scale, args.offset_u, args.offset_v)
    art_image = bpy.data.images.load(art_path, check_existing=False)
    art_image.name = "OriginalArt_head_mv_condition_front"
    art_image.colorspace_settings.name = "sRGB"
    art_image.pack()
    material_reports = [connect_projection_material(material, art_image, uv_name, args.strength) for material in mesh.data.materials if material]
    bpy.context.view_layer.update()
    after = fingerprint()
    if before != after:
        raise RuntimeError("Geometry fingerprint changed: %s -> %s" % (before, after))
    # Make the saved deliverable self-contained, including original base-color and PBR maps.
    bpy.ops.file.pack_all()
    packed = sorted(image.name for image in bpy.data.images if image.packed_file)
    if art_image.name not in packed:
        raise RuntimeError("Original art was not packed")
    scene = bpy.context.scene
    scene["original_art_projection"] = "original2Dartprojectedontogenerated3Dsurface"
    scene["original_art_sha256"] = sha256(art_path)
    scene["projection_camera"] = "front C=(0,-3.1192050007897403,0), forward +Y, right +X, up +Z, FOV 20 degrees"
    scene["projection_uv"] = uv_name
    bpy.ops.wm.save_as_mainfile(filepath=output)
    report = {"input": source, "output": output, "source_art": art_path, "source_art_sha256": sha256(art_path), "geometry_before": before, "geometry_after": after, "mesh": mesh.name, "root": root.name, "uv_layer": uv_name, "attribute": "FaceProjectionWeight", "calibration": {"uv_scale": args.uv_scale, "offset_u": args.offset_u, "offset_v": args.offset_v, "strength": args.strength}, "packed_images": packed, "materials": material_reports}
    with open(os.path.splitext(output)[0] + "-projection-report.json", "w", encoding="utf8") as handle:
        json.dump(report, handle, indent=2)


if __name__ == "__main__":
    main()
