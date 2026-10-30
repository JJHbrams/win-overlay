"""Actual annular eyelid skin proof, with a single closed aperture loop.

The globe is an ellipsoid. Lids are connected quad bands extending from its
front surface to the surrounding facial surface, rather than line objects.
This isolated proof is not a finished Mia face or a likeness acceptance.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = .72
    return m


def mesh_object(name, vertices, faces, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    ob = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(ob)
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    return ob


def eye_material(rx, rz):
    m = material("Eye_sclera_iris_pupil_on_globe", (.78, .79, .75))
    nt = m.node_tree
    n, links = nt.nodes, nt.links
    tex = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    links.new(tex.outputs["Generated"], sep.inputs[0])
    scalars = []
    for axis, radius in (("X", rx), ("Z", rz)):
        sub = n.new("ShaderNodeMath")
        sub.operation = "SUBTRACT"
        sub.inputs[1].default_value = .5
        links.new(sep.outputs[axis], sub.inputs[0])
        mul = n.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 2 * radius
        links.new(sub.outputs[0], mul.inputs[0])
        scalars.append(mul)
    combine = n.new("ShaderNodeCombineXYZ")
    links.new(scalars[0].outputs[0], combine.inputs[0])
    links.new(scalars[1].outputs[0], combine.inputs[2])
    length = n.new("ShaderNodeVectorMath")
    length.operation = "LENGTH"
    links.new(combine.outputs[0], length.inputs[0])
    scale = n.new("ShaderNodeMath")
    scale.operation = "DIVIDE"
    scale.inputs[1].default_value = .033
    links.new(length.outputs["Value"], scale.inputs[0])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "LINEAR"
    stops = [(0, (.012, .018, .02, 1)), (.16, (.012, .018, .02, 1)),
             (.19, (.16, .23, .24, 1)), (.37, (.28, .36, .36, 1)),
             (.40, (.07, .12, .13, 1)), (.425, (.78, .79, .75, 1)),
             (1, (.78, .79, .75, 1))]
    while len(ramp.color_ramp.elements) > 1:
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[-1])
    for i, (pos, color) in enumerate(stops):
        el = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(pos)
        el.position, el.color = pos, color
    links.new(scale.outputs[0], ramp.inputs[0])
    links.new(ramp.outputs["Color"], n.get("Principled BSDF").inputs["Base Color"])
    n.get("Principled BSDF").inputs["Roughness"].default_value = .36
    return m


def build_eye():
    rx, ry, rz = .033, .028, .030
    n, bands = 96, 12
    skin = material("Lid_connected_skin", (.57, .40, .35))
    lash = material("Upper_lash_seated_strip", (.018, .012, .014))
    vertices, faces, rims = [], [], []

    def globe_y(x, z):
        q = 1 - (x / rx) ** 2 - (z / rz) ** 2
        return -ry * math.sqrt(max(0, q)) if q >= 0 else None

    for j in range(bands + 1):
        t = j / bands
        smooth = t * t * (3 - 2 * t)
        for i in range(n):
            theta = 2 * math.pi * i / n
            c, s = math.cos(theta), math.sin(theta)
            # The upper/lower arcs meet at EXACTLY (+/- .028, 0).
            inner_x = .028 * c
            inner_z = (.005 if s >= 0 else .011) * s
            outer_x, outer_z = .057 * c, .047 * s
            x = inner_x * (1 - smooth) + outer_x * smooth
            z = inner_z * (1 - smooth) + outer_z * smooth
            inner_y = globe_y(inner_x, inner_z) - .00055
            outer_y = -.010 + .002 * c * c
            y = inner_y * (1 - smooth) + outer_y * smooth
            support = globe_y(x, z)
            if support is not None:
                y = min(y, support - .00055)
            vertices.append((x, y, z))
        if j < bands:
            for i in range(n):
                q = (i + 1) % n
                a, b = j * n + i, j * n + q
                faces.append((a, a + n, b + n, b))
    # Rear facial volume makes the profile an embedded assembly.
    rear_start = len(vertices)
    for i in range(n):
        th = 2 * math.pi * i / n
        vertices.append((.048 * math.cos(th), .040, .040 * math.sin(th)))
        a, b = bands * n + i, bands * n + (i + 1) % n
        faces.append((a, rear_start + i, rear_start + (i + 1) % n, b))
    center = len(vertices)
    vertices.append((0, .053, 0))
    for i in range(n):
        faces.append((rear_start + i, center, rear_start + (i + 1) % n))
    ob = mesh_object("Connected_lid_forehead_cheek_patch", vertices, faces, skin)
    ob["construction"] = "One closed aperture loop, twelve connected quad bands, rear skin volume"
    ob["aperture_boundary_expected"] = n
    # A lash ribbon lies directly on the first connected skin band.
    lv, lf = [], []
    for i in range(n // 2 + 1):
        a = Vector(vertices[i])
        b = Vector(vertices[n + i])
        b = a.lerp(b, .8)
        a.y -= .00015
        b.y -= .00015
        lv.extend((tuple(a), tuple(b)))
        if i:
            k = i * 2
            lf.append((k - 2, k - 1, k + 1, k))
    mesh_object("Upper_lash_ribbon_on_skin", lv, lf, lash)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40)
    eye = bpy.context.object
    eye.name = "Seated_ellipsoid_eye"
    eye.scale = (rx, ry, rz)
    eye.data.materials.append(eye_material(rx, rz))
    for p in eye.data.polygons:
        p.use_smooth = True
    counts = {}
    for edge in ob.data.edges:
        key = tuple(sorted(edge.vertices))
        counts[key] = 0
    for p in ob.data.polygons:
        for edge in p.edge_keys:
            counts[tuple(sorted(edge))] += 1
    boundary = sum(v == 1 for v in counts.values())
    assert boundary == n, (boundary, n)
    assert max(counts.values()) == 2
    return {"skin_vertices": len(vertices), "skin_faces": len(faces),
            "aperture_boundary_edges": boundary, "eye_vertices": len(eye.data.vertices),
            "shared_corners": [vertices[0], vertices[n // 2]],
            "status": "STRUCTURAL_PROOF_REQUIRES_VISUAL_REVIEW"}


def render(output):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.world.color = (.035, .035, .035)
    scene.view_settings.view_transform = "AgX"
    for name, pos, energy in (("Key", (.5, -.7, .7), 28), ("Fill", (-.5, -.5, .2), 12)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.size = energy, .65
        ob = bpy.data.objects.new(name, data)
        scene.collection.objects.link(ob)
        ob.location = pos
        ob.rotation_euler = (-ob.location).to_track_quat("-Z", "Y").to_euler()
    data = bpy.data.cameras.new("Camera")
    data.type, data.ortho_scale = "ORTHO", .145
    camera = bpy.data.objects.new("Camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    original = {ob: list(ob.data.materials) for ob in scene.objects if ob.type == "MESH"}
    for mode in ("saved", "clay"):
        if mode == "clay":
            clay = material("Proof_clay", (.32, .32, .32))
            for ob in original:
                ob.data.materials.clear()
                ob.data.materials.append(clay)
        for yaw in (0, 45, 90):
            a = math.radians(yaw)
            camera.location = (math.sin(a) * .6, -math.cos(a) * .6, .01)
            camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = str(output / f"{mode}_{yaw:03d}.png")
            bpy.ops.render.render(write_still=True)
    for ob, mats in original.items():
        ob.data.materials.clear()
        for mat in mats:
            ob.data.materials.append(mat)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", required=True)
    opts = ap.parse_args(sys.argv[sys.argv.index("--") + 1:])
    dest = Path(opts.output_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.world = bpy.data.worlds.new("Proof_world")
    report = build_eye()
    render(dest)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest / "eye-surface-proof.blend"))
    (dest / "inventory.json").write_text(json.dumps(report, indent=2), encoding="utf8")
