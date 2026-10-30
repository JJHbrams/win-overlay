#!/usr/bin/env python3
"""Render VRoid-aware anatomy QA without treating alpha face cards as solids."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def parse():
    vals = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--full-orbit", action="store_true")
    return p.parse_args(vals)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()


def link(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def camera():
    data = bpy.data.cameras.new("MIA_QA_CAMERA")
    obj = link(bpy.data.objects.new("MIA_QA_CAMERA", data))
    data.lens = 65
    bpy.context.scene.camera = obj
    return obj


def aim(cam, pos, target):
    cam.location = pos
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()


def render(cam, output, name, pos, target):
    aim(cam, pos, target)
    path = output / (name + ".png")
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return path


def neutral(name, color=(0.42, 0.43, 0.46, 1)):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.88
    return m


def set_outline(objects, enabled):
    state = []
    for obj in objects:
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and "OUTLINE" in modifier.name.upper():
                state.append((modifier, modifier.show_render))
                modifier.show_render = enabled
    return state


def restore_outline(state):
    for modifier, visible in state:
        modifier.show_render = visible


def unlit_copy(material):
    """Use only the existing MToon lit texture color/alpha on a diagnostic copy."""
    made = material.copy()
    made.name = "QA_UNLIT_" + material.name
    nodes, links = made.node_tree.nodes, made.node_tree.links
    target = next((n for n in nodes if n.name.endswith("Mtoon1Output")), None)
    output = next((n for n in nodes if n.type == "OUTPUT_MATERIAL"), None)
    if not target or not output:
        return made
    color_links = list(target.inputs["Lit Color Texture Color"].links)
    alpha_links = list(target.inputs["Lit Color Texture Alpha"].links)
    if not color_links:
        return made
    emission = nodes.new("ShaderNodeEmission")
    emission.name = "QA_RAW_BASECOLOR_EMISSION"
    links.new(color_links[0].from_socket, emission.inputs["Color"])
    for link in list(output.inputs["Surface"].links):
        links.remove(link)
    if alpha_links:
        transparent = nodes.new("ShaderNodeBsdfTransparent")
        mix = nodes.new("ShaderNodeMixShader")
        links.new(alpha_links[0].from_socket, mix.inputs[0])
        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], output.inputs["Surface"])
    else:
        links.new(emission.outputs[0], output.inputs["Surface"])
    return made


def raw_unlit_skin(objects):
    originals = []
    for obj in objects:
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            upper = mat.name.upper()
            if "MIA_COOLMUTEDSKIN" in upper or "BODY_00_SKIN" in upper:
                originals.append((slot, mat))
                slot.material = unlit_copy(mat)
    return originals


def restore_material_slots(originals):
    for slot, material in originals:
        slot.material = material


def head_pose_proof(objects, camera, output, target):
    """Non-destructively prove that source head core and face overlay co-move."""
    bindings = {}
    armatures = []
    for obj in objects:
        mods = [m for m in obj.modifiers if m.type == "ARMATURE" and m.object]
        bindings[obj.name] = [{"modifier": m.name, "target": m.object.name} for m in mods]
        armatures.extend(m.object for m in mods)
    armature = next((a for a in armatures if a.pose and a.pose.bones.get("J_Bip_C_Head")), None)
    if not armature:
        return bindings, []
    bone = armature.pose.bones["J_Bip_C_Head"]
    prior_mode, prior_rotation = bone.rotation_mode, tuple(bone.rotation_axis_angle)
    axis = bone.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))
    axis.normalize()
    rendered = []
    bone.rotation_mode = "AXIS_ANGLE"
    for degrees in (-30, 30):
        bone.rotation_axis_angle = (math.radians(degrees), axis.x, axis.y, axis.z)
        bpy.context.view_layer.update()
        rendered.append(render(camera, output, f"head_pose_yaw_{degrees:+03d}",
                               (0.53, -0.53, 1.59), target))
    bone.rotation_axis_angle = prior_rotation
    bone.rotation_mode = prior_mode
    bpy.context.view_layer.update()
    return bindings, [str(path) for path in rendered]


def material_isolation(source, role, material_term):
    """Copy only one semantic material region for clay/wire inspection."""
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = role
    link(obj)
    obj.hide_render = False
    obj.hide_viewport = False
    # VRM MToon outline geometry is a style shell, not anatomy.  Disable it on
    # this disposable inspection copy so clay reveals only source skin volume.
    disabled = []
    for modifier in obj.modifiers:
        if modifier.type == "NODES" and "OUTLINE" in modifier.name.upper():
            modifier.show_render = False
            disabled.append(modifier.name)
    if material_term == "FACE_RAW":
        # The VRoid face's opaque base is split between SKIN and FaceMouth;
        # retain both while excluding alpha eye/liner/brow cards from clay.
        keep = {i for i, m in enumerate(obj.data.materials)
                if m and ("SKIN" in m.name.upper() or "FACEMOUTH" in m.name.upper())}
    else:
        keep = {i for i, m in enumerate(obj.data.materials) if m and material_term in m.name.upper()}
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in obj.data.polygons:
        p.select = p.material_index not in keep
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    obj.data.materials.clear()
    obj.data.materials.append(neutral(role + "_CLAY"))
    return obj, len(keep), disabled


def main():
    args = parse()
    source = Path(args.input)
    before = sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    cam = camera()
    views = [("front", (0, -0.72, 1.59)), ("three_quarter", (0.53, -0.53, 1.59)), ("profile", (0.72, 0, 1.59))]
    target = (0, -0.02, 1.57)
    saved = [render(cam, output, "assembly_art_" + n, p, target) for n, p in views]

    # Alpha-masked eyelashes, brows and iris planes remain part of assembly art;
    # they are deliberately excluded from opaque clay.  Skin-only copies expose
    # real volume without falsely turning alpha cards into slabs.
    face = bpy.data.objects["Mia_Face_AnimeTopology"]
    body = bpy.data.objects["Mia_Body_Anatomy_Skin"]
    bindings, head_pose_views = head_pose_proof((face, body), cam, output, target)
    outline_state = set_outline((face, body), False)
    outline_off = [render(cam, output, "assembly_outline_off_" + n, p, target) for n, p in views]
    restore_outline(outline_state)
    unlit_originals = raw_unlit_skin((face, body))
    unlit = [render(cam, output, "assembly_unlit_diffuse_" + n, p, target) for n, p in views]
    restore_material_slots(unlit_originals)
    for obj in (face, body):
        obj.hide_render = True
    face_skin, face_slots, disabled_face_style = material_isolation(face, "QA_FACE_SKIN_ONLY", "FACE_RAW")
    body_clay = body.copy()
    body_clay.data = body.data.copy()
    body_clay.name = "QA_BODY_SKIN_ONLY"
    link(body_clay)
    body_clay.hide_render = False
    body_clay.hide_viewport = False
    disabled_body_style = []
    for modifier in body_clay.modifiers:
        if modifier.type == "NODES" and "OUTLINE" in modifier.name.upper():
            modifier.show_render = False
            disabled_body_style.append(modifier.name)
    body_clay.data.materials.clear()
    body_clay.data.materials.append(neutral("QA_BODY_CLAY"))
    # Face volume is inspected alone first; otherwise the source body's
    # material-isolated torso can contaminate the close facial profile.
    body_clay.hide_render = True
    structure = [render(cam, output, "face_skin_clay_" + n, p, target) for n, p in views]
    body_target = (0, 0, .92)
    body_clay.hide_render = False
    face_skin.hide_render = True
    structure += [render(cam, output, "body_skin_clay_front", (0, -3.4, .94), body_target),
                  render(cam, output, "body_skin_clay_profile", (3.35, 0, .94), body_target)]
    wire = face_skin.copy()
    wire.data = face_skin.data.copy()
    wire.name = "QA_FACE_SKIN_WIREFRAME"
    link(wire)
    modifier = wire.modifiers.new("QA_TOPOLOGY_WIREFRAME", "WIREFRAME")
    modifier.thickness = .00055
    modifier.use_even_offset = True
    wire.data.materials.clear()
    wire.data.materials.append(neutral("QA_WIREFRAME", (0.08, .72, .84, 1)))
    face_skin.hide_render = True
    body_clay.hide_render = True
    structure += [render(cam, output, "face_skin_wire_front", views[0][1], target),
                  render(cam, output, "face_skin_wire_three_quarter", views[1][1], target)]

    orbit_records = []
    if args.full_orbit:
        # Exactly 12 yaw * 3 elevation * 3 scale * 2 modes.  Saved art keeps
        # original MToon/alpha layers; raw mode exposes Body core + Face raw
        # overlay, with style outlines disabled on disposable copies.
        raw_face = face_skin.copy()
        raw_face.data = face_skin.data.copy()
        raw_face.name = "QA_RAW_FACE_OVERLAY"
        link(raw_face)
        raw_face.hide_render = False
        raw_body = body_clay.copy()
        raw_body.data = body_clay.data.copy()
        raw_body.name = "QA_RAW_BODY_CORE"
        link(raw_body)
        raw_body.hide_render = False
        raw_face.hide_render = True
        raw_body.hide_render = True
        scene.render.resolution_x = scene.render.resolution_y = 384
        scales = {"full": ((0, 0, .90), 3.4), "torso": ((0, 0, 1.10), 1.55), "head": ((0, -.02, 1.57), .66)}
        for mode in ("art", "raw_skin"):
            face.hide_render = mode != "art"
            body.hide_render = mode != "art"
            raw_face.hide_render = mode != "raw_skin"
            raw_body.hide_render = mode != "raw_skin"
            for scale_name, (center, distance) in scales.items():
                for elev in (-10, 0, 10):
                    for yaw in range(0, 360, 30):
                        rad, er = math.radians(yaw), math.radians(elev)
                        position = Vector(center) + Vector((math.sin(rad) * distance, -math.cos(rad) * distance, math.sin(er) * distance))
                        name = f"{mode}_{scale_name}_y{yaw:03d}_e{elev:+03d}"
                        path = render(cam, output, name, position, center)
                        orbit_records.append({"file": path.name, "mode": mode, "scale": scale_name, "yaw": yaw, "elevation": elev})
        face.hide_render = False
        body.hide_render = False
    after = sha(source)
    Path(args.report).write_text(json.dumps({
        "input_sha256_before": before, "input_sha256_after": after, "input_unchanged": before == after,
        "art_views": [str(x) for x in saved], "outline_off_views": [str(x) for x in outline_off],
        "unlit_diffuse_views": [str(x) for x in unlit], "structure_views": [str(x) for x in structure],
        "full_orbit_records": orbit_records,
        "head_pose_proof": {"bindings": bindings, "views": head_pose_views,
                            "status": "NON_DESTRUCTIVE_HEAD_YAW_ONLY_NOT_EVENT_RIG_ACCEPTANCE"},
        "isolation": {"face_skin_material_slots": face_slots,
                      "alpha_owned_layers_excluded_from_opaque_clay": True,
                      "body_source": "Mia_Body_Anatomy_Skin",
                      "disabled_style_modifiers_on_disposable_copies": {
                          "face": disabled_face_style, "body": disabled_body_style}},
        "status": "UNVERIFIED: inspect art and material-isolated structure separately"
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
