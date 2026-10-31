"""Incremental head refinement for the already v04-fitted Mia Face44 source.

Input contract: call once on the v04-mapped Face44/body-headcap pair.  This is
not a source importer and must not be applied to an already refined v06 study.
All Face44 key blocks receive the identical positional map, preserving the
original Face42 prefix, topology and UV correspondence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


FACE_NAME = "MIA_V06_FACE_SKIN"
BODY_NAME = "MIA_V06_BODY_SKIN"


def _smooth(v):
    v = max(0.0, min(1.0, v))
    return v * v * (3.0 - 2.0 * v)


def _crown_dome(q, upper):
    """Preserve the source cap, but restore volume lost by uniform z scaling."""
    radial = max(0.0, 1.0 - (q.x / .112) ** 2 - ((q.y + .010) / .115) ** 2)
    q.z += .027 * upper * radial
    return q


def _face_map(p):
    """A conservative adult proportion pass in the face's local coordinate space."""
    q = p.copy()
    # v04 had already shortened the whole cap.  This is a non-uniform second
    # pass: only the upper cranium narrows/shortens, preserving eye placement.
    upper = _smooth((q.z - 1.635) / .075)
    q.z -= .038 * upper
    q.x *= 1.0 - .072 * upper
    q = _crown_dome(q, upper)
    # Give the lower third cheek/jaw planes before the chin converges.  It
    # removes the childlike V silhouette without making the jaw square.
    cheek = _smooth((1.585 - q.z) / .080) * (1.0 - _smooth((1.505 - q.z) / .030))
    chin = _smooth((1.515 - q.z) / .040)
    q.x *= 1.0 + .055 * cheek - .018 * chin
    # A shallow facial plane keeps the profile from reading as a flat mask.
    q.y += .0035 * cheek
    return q


def _body_head_map(p, head_weight, neck_weight):
    q = p.copy()
    # Body has no expression keys. Restrict to Head/Neck weighted vertices so
    # torso, shoulders and limbs remain the body specialist's ownership.
    if head_weight <= .001:
        return q
    # v04 applied this exact base transform to *every* Face44 key but skipped
    # the body's cap.  The source Body Head island is the other half of the
    # cranium; it must receive the same map before any local refinement.
    q.z = 1.465 + (q.z - 1.465) * (1.0 - .060 * head_weight)
    upper = _smooth((q.z - 1.635) / .075) * head_weight
    q.z -= .038 * upper
    q.x *= 1.0 - .072 * upper
    q = _crown_dome(q, upper)
    # Blend a very small neck widening toward the head to avoid a pinched join.
    neck_blend = _smooth((q.z - 1.49) / .085) * min(head_weight, neck_weight)
    q.x *= 1.0 + .018 * neck_blend
    return q


def _weight(vertex, group_index):
    if group_index is None:
        return 0.0
    return next((item.weight for item in vertex.groups if item.group == group_index), 0.0)


def _paper_material(name, rgba):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Roughness"].default_value = .70
    bsdf.inputs["Specular IOR Level"].default_value = .18
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _flat_paper_material(name, rgba):
    """Unlit paper response for the body headcap review; no face UV is sampled."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    emit = nodes.new("ShaderNodeEmission"); emit.inputs["Color"].default_value = rgba; emit.inputs["Strength"].default_value = 1.0
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return mat


def _body_paper_response_from_face(face):
    """Match the face's normal→toon-ramp→emission response without face UVs."""
    source = face.material_slots[7].material
    ramp_source = next(node for node in source.node_tree.nodes if node.type == "VALTORGB")
    dot_source = next(node for node in source.node_tree.nodes if node.type == "VECT_MATH")
    map_source = next(node for node in source.node_tree.nodes if node.type == "MAP_RANGE")
    mat = bpy.data.materials.get("MIA_V06_HeadcapPaperMatchedResponse") or bpy.data.materials.new("MIA_V06_HeadcapPaperMatchedResponse")
    mat.use_nodes = True; nodes=mat.node_tree.nodes; nodes.clear()
    out=nodes.new("ShaderNodeOutputMaterial"); geom=nodes.new("ShaderNodeNewGeometry")
    dot=nodes.new("ShaderNodeVectorMath"); dot.operation="DOT_PRODUCT"; dot.inputs[1].default_value=dot_source.inputs[1].default_value
    mapr=nodes.new("ShaderNodeMapRange"); mapr.clamp=True
    for source_name, target_name in (("From Min","From Min"),("From Max","From Max"),("To Min","To Min"),("To Max","To Max")):
        mapr.inputs[target_name].default_value=map_source.inputs[source_name].default_value
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = ramp_source.color_ramp.interpolation
    ramp.color_ramp.elements[0].position=ramp_source.color_ramp.elements[0].position
    ramp.color_ramp.elements[0].color=ramp_source.color_ramp.elements[0].color
    ramp.color_ramp.elements[-1].position=ramp_source.color_ramp.elements[-1].position
    ramp.color_ramp.elements[-1].color=ramp_source.color_ramp.elements[-1].color
    # Sampled from the unpainted Face slot-7 forehead/temple UV region.  The
    # face graph is image × toon ramp (not ramp alone), so Body needs this
    # constant base pigment multiplier without receiving facial UV mapping.
    pigment=nodes.new("ShaderNodeRGB"); pigment.outputs[0].default_value=(.94118,.87843,.85098,1)
    mix=nodes.new("ShaderNodeMixRGB"); mix.blend_type="MULTIPLY"; mix.inputs[0].default_value=1.0
    emit=nodes.new("ShaderNodeEmission"); emit.inputs["Strength"].default_value=1.0
    links=mat.node_tree.links; links.new(geom.outputs["Normal"],dot.inputs[0]); links.new(dot.outputs["Value"],mapr.inputs["Value"])
    links.new(mapr.outputs["Result"],ramp.inputs["Fac"]); links.new(pigment.outputs[0],mix.inputs[1]); links.new(ramp.outputs["Color"],mix.inputs[2]); links.new(mix.outputs[0],emit.inputs["Color"]); links.new(emit.outputs[0],out.inputs[0])
    return mat


def _restore_rim(face):
    """Re-enable the existing UV-card rim using its own alpha/pigment image.

    No new lash topology is introduced; the card lives on Face44 and therefore
    inherits every existing blink/expression key.
    """
    if len(face.material_slots) <= 2 or not face.material_slots[2].material:
        return {"status": "missing_rim_slot"}
    source = face.material_slots[2].material
    mat = source.copy()
    mat.name = "MIA_V06_MatureUpperRim_ExistingUV"
    mat.surface_render_method = "DITHERED"
    # Reuse the card's archived alpha image rather than adding a new lash mesh.
    # Its surface is already in the Face44 key block, so this remains blink-safe.
    source_image = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
    nodes = mat.node_tree.nodes; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); tex = nodes.new("ShaderNodeTexImage"); tex.image = source_image
    trans = nodes.new("ShaderNodeBsdfTransparent"); emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (.025, .035, .052, 1.0); emit.inputs["Strength"].default_value = .72
    mix = nodes.new("ShaderNodeMixShader")
    mat.node_tree.links.new(tex.outputs["Alpha"], mix.inputs[0]); mat.node_tree.links.new(trans.outputs[0], mix.inputs[1])
    mat.node_tree.links.new(emit.outputs[0], mix.inputs[2]); mat.node_tree.links.new(mix.outputs[0], out.inputs[0])
    face.material_slots[2].material = mat
    return {"status": "existing_uv_rim_restored", "alpha_image": source_image.name if source_image else None, "material": mat.name}


def _tune_existing_uv_ink(face, slot_index, name, color, strength):
    """Increase legibility using the existing card geometry, UV and alpha only."""
    if slot_index >= len(face.material_slots) or not face.material_slots[slot_index].material:
        return {"status": "missing_slot", "slot": slot_index}
    source = face.material_slots[slot_index].material
    image = next((node.image for node in source.node_tree.nodes if node.type == "TEX_IMAGE" and node.image), None)
    if not image:
        return {"status": "no_existing_alpha_image", "slot": slot_index}
    mat = source.copy(); mat.name = name; mat.surface_render_method = "DITHERED"
    nodes = mat.node_tree.nodes; nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial"); tex = nodes.new("ShaderNodeTexImage"); tex.image=image
    trans = nodes.new("ShaderNodeBsdfTransparent"); emit=nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value=color; emit.inputs["Strength"].default_value=strength
    mix=nodes.new("ShaderNodeMixShader")
    mat.node_tree.links.new(tex.outputs["Alpha"],mix.inputs[0]); mat.node_tree.links.new(trans.outputs[0],mix.inputs[1])
    mat.node_tree.links.new(emit.outputs[0],mix.inputs[2]); mat.node_tree.links.new(mix.outputs[0],out.inputs[0])
    face.material_slots[slot_index].material=mat
    return {"status":"existing_uv_alpha_preserved","slot":slot_index,"image":image.name,"material":mat.name}


def _tint_existing_paper_skin(face):
    """Keep the archived skin image/pigment path, but remove the white-mask read."""
    if len(face.material_slots) <= 7 or not face.material_slots[7].material:
        return {"status": "missing_paper_slot"}
    mat = face.material_slots[7].material.copy()
    mat.name = "MIA_V06_CoolPaperSkin_Calibrated"
    ramp = next((node for node in mat.node_tree.nodes if node.type == "VALTORGB"), None)
    if not ramp:
        return {"status": "no_color_ramp"}
    ramp.color_ramp.elements[0].color = (.72, .58, .52, 1.0)
    ramp.color_ramp.elements[-1].color = (.84, .72, .64, 1.0)
    face.material_slots[7].material = mat
    return {"status": "existing_paper_image_retained_tinted", "material": mat.name}


def refine_head(face, body, rig=None, expected_stage="v04-mapped"):
    """Refine one v04 Face44/body-headcap pair in place, exactly once."""
    if face.get("mia_head_refine_v06"):
        raise RuntimeError("Mia head refine v06 is already applied; do not compound this pass.")
    keys = list(face.data.shape_keys.key_blocks) if face.data.shape_keys else []
    if len(keys) != 44:
        raise RuntimeError("Expected v04 Face44; got %s keys." % len(keys))
    for key in keys:
        for point in key.data:
            point.co = _face_map(point.co)
    groups = {g.name: g.index for g in body.vertex_groups}
    head_i, neck_i = groups.get("J_Bip_C_Head"), groups.get("J_Bip_C_Neck")
    changed_indices = []
    for vertex in body.data.vertices:
        hw, nw = _weight(vertex, head_i), _weight(vertex, neck_i)
        old = vertex.co.copy()
        vertex.co = _body_head_map(old, hw, nw)
        if (vertex.co - old).length > 1e-8:
            changed_indices.append(vertex.index)
    # Keep authored face pigment. Body uses the same normal-to-toon-ramp
    # response, constructed without a face image/UV input.
    paper_face = _tint_existing_paper_skin(face)
    paper = _body_paper_response_from_face(face)
    replaced = []
    for index, slot in enumerate(body.material_slots):
        replaced.append({"slot": index, "old": slot.material.name if slot.material else None})
        slot.material = paper
    rim = _restore_rim(face)
    brow = _tune_existing_uv_ink(face, 4, "MIA_V06_ReadableGraphiteBrow", (.035,.045,.060,1), .56)
    face["mia_head_refine_v06"] = True
    face["mia_head_refine_input"] = expected_stage
    face["mia_head_refine_note"] = "all 44 keys mapped together; UV/topology/index order unchanged"
    body["mia_head_refine_v06"] = True
    brow_delta = _retune_owned_brow_delta(face)
    neutral = set_mia_neutral(face)
    return {"face_keys_mapped": [key.name for key in keys],
            "face_vertices_per_key": len(face.data.vertices),
            "face_vertex_indices": "all 0..%d" % (len(face.data.vertices) - 1),
            "face_change_reason": "upper-cranium reduction plus cheek/jaw plane correction, transported identically to preserve expression deltas",
            "body_head_neck_vertices_changed": changed_indices,
            "body_change_reason": "J_Bip_C_Head island first receives v04's exact Face44 base cap map, then the shared upper-cranium map; neck blending is only inside that Head island",
            "body_material_slots": replaced, "rim": rim, "paper_face": paper_face,
            "brow": brow,
            "body_pigment_multiplier": {"sample_region":"Face slot7 forehead/temple z>1.60 UV average","colorspace":"Non-Color","rgb":[.94118,.87843,.85098]},
            "eye_extra_slot_8": "preserved: source material is EyeExtra_01 and v04 fit treats it with iris/highlight family",
            "neutral_guide": neutral, "owned_brow_delta": brow_delta}


def set_mia_neutral(face):
    """Reference-guided idle guide: heavy upper lid, visible low iris, dry mouth."""
    values = {"Fcl_EYE_Close": .38, "Fcl_EYE_Sorrow": .12,
              "Fcl_BRW_Angry": .10, "Fcl_MTH_Angry": .05,
              "Fcl_MTH_Neutral": .23,
              # Owned v05 design correctives: wider horizontal eye aperture,
              # reduced iris, then lowered/sloped brow card placement.
              "MIA_FaceArt_EyeProportion": 1.0,
              "MIA_FaceArt_OwnedBrowPlacement": 1.0}
    applied = {}
    for key in face.data.shape_keys.key_blocks:
        key.value = 0.0
        for suffix, value in values.items():
            if key.name.endswith(suffix):
                key.value = value; applied[key.name] = value
    return applied


def _retune_owned_brow_delta(face, scale=.55):
    """Reduce only the owned post-Face42 brow offset after the v04 face fit."""
    key = next((item for item in face.data.shape_keys.key_blocks
                if item.name == "MIA_FaceArt_OwnedBrowPlacement"), None)
    if not key:
        return {"status": "missing"}
    basis = face.data.shape_keys.key_blocks[0]
    changed = 0
    for index, point in enumerate(key.data):
        delta = point.co - basis.data[index].co
        if delta.length > 1e-8:
            point.co = basis.data[index].co + delta * scale
            changed += 1
    return {"status": "scaled_owned_delta", "key": key.name, "scale": scale,
            "vertices": changed, "reason": "rest-pose brow/lid clearance after v04 face fit"}


def _aim(camera, loc, target):
    camera.location = loc
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def _review_scene(face, body):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 720, 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.035, .045, .065)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.0
    for obj in list(scene.objects):
        if obj.type in {"LIGHT", "CAMERA"}: bpy.data.objects.remove(obj, do_unlink=True)
        elif obj not in {face, body}: obj.hide_render = True
    data = bpy.data.cameras.new("MIA_V06_HEAD_REVIEW_CAMERA")
    cam = bpy.data.objects.new(data.name, data); scene.collection.objects.link(cam)
    scene.camera = cam; data.type = "ORTHO"; data.ortho_scale = .45
    for name, loc, energy, size in (("HeadKey", (2.2,-2.9,2.7), 380, 2.0),
                                    ("HeadFill", (-2.0,-2.2,2.0), 150, 2.0),
                                    ("HeadRim", (0,2.4,2.4), 220, 1.3)):
        light = bpy.data.lights.new(name, "AREA"); light.energy, light.shape, light.size = energy, "DISK", size
        obj = bpy.data.objects.new(name, light); scene.collection.objects.link(obj); obj.location = loc
        _aim(obj, loc, (0, 0, 1.55))
    return scene, cam


def _face_skin_copy(face, name):
    """Temporary real Face44 skin geometry, excluding transparent eye/ink cards."""
    copy = face.copy(); copy.data = face.data.copy(); copy.name = name
    bpy.context.scene.collection.objects.link(copy)
    copy.hide_render = False
    bpy.context.view_layer.objects.active = copy; copy.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
    for polygon in copy.data.polygons:
        polygon.select = polygon.material_index not in {0, 7}
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="FACE"); bpy.ops.object.mode_set(mode="OBJECT")
    copy.select_set(False)
    return copy


def _render_set(scene, cam, face, body, out, stem, clay=False, wire=False):
    out.mkdir(parents=True, exist_ok=True)
    override = bpy.context.view_layer.material_override
    if clay:
        bpy.context.view_layer.material_override = _paper_material("MIA_V06_HEAD_REVIEW_CLAY", (.28,.32,.37,1))
    clones = []
    if clay:
        # Material override otherwise makes transparent liner cards opaque.
        # Retain actual Face44 skin slots 0/7 (nose, jaw, cheeks), while
        # excluding only eye/liner/brow cards. Keep the complete actual Body
        # skin too; no proof-only cap ownership deletion is performed here.
        face.hide_render = True
        skin = _face_skin_copy(face, "MIA_V06_CLAY_FACE44_SKIN")
        clones.append((face, skin))
    if wire:
        for src in (face, body):
            src.hide_render = True
            c = src.copy(); c.data = src.data.copy(); bpy.context.scene.collection.objects.link(c)
            c.hide_render = False
            c.data.materials.clear(); c.data.materials.append(_paper_material("MIA_V06_HEAD_REVIEW_WIRE", (.025,.035,.055,1)))
            mod = c.modifiers.new("MIA_V06_HEAD_REVIEW_WIREFRAME", "WIREFRAME"); mod.thickness = .0010
            clones.append((src,c))
    views = {"front":((0,-1.55,1.58),(0,0,1.58)), "profile":((1.55,-.08,1.58),(0,0,1.58)),
             "three_quarter_l":((1.10,-1.10,1.58),(0,0,1.58)), "three_quarter_r":((-1.10,-1.10,1.58),(0,0,1.58)),
             "back":((0,1.55,1.58),(0,.02,1.58))}
    made=[]
    for name,(loc,target) in views.items():
        _aim(cam,loc,target); path=out/(stem+"_"+name+".png"); scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True); made.append(str(path))
    for src,c in clones:
        if c: bpy.data.objects.remove(c,do_unlink=True)
        src.hide_render=False
    bpy.context.view_layer.material_override = override
    return made


def _material_id_three_quarter(scene, cam, face, body, out):
    """Flat ownership diagnostic: Face skin red, Body skin blue, cards black."""
    out.mkdir(parents=True, exist_ok=True)
    face_old=[slot.material for slot in face.material_slots]; body_old=[slot.material for slot in body.material_slots]
    face_id=_flat_paper_material("MIA_V06_ID_FACE", (1.0,.08,.08,1)); body_id=_flat_paper_material("MIA_V06_ID_BODY", (.05,.20,1.0,1)); card_id=_flat_paper_material("MIA_V06_ID_CARD", (.02,.02,.02,1))
    for i,slot in enumerate(face.material_slots): slot.material=face_id if i in {0,7} else card_id
    for slot in body.material_slots: slot.material=body_id
    _aim(cam,(1.10,-1.10,1.58),(0,0,1.58)); path=out/"head_material_id_three_quarter_l.png"; scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    for slot,old in zip(face.material_slots,face_old): slot.material=old
    for slot,old in zip(body.material_slots,body_old): slot.material=old
    return str(path)


def _pose_proof(scene, cam, face, out):
    keys = face.data.shape_keys.key_blocks
    saved = {key.name: key.value for key in keys}
    identity = {name: saved.get(name, 0.0) for name in
                ("MIA_FaceArt_EyeProportion", "MIA_FaceArt_OwnedBrowPlacement")}
    output=[]; cases=[]
    for case, suffix, value in (("blink","Fcl_EYE_Close",1.0),("mouth_a","Fcl_MTH_A",1.0)):
        # Reset only stock expression controls.  Mia identity correctives stay
        # active, so tests expose additive clipping rather than stock-face rig.
        for key in keys:
            if key.name.startswith("Face.") or key.name.startswith("EyeExtra"):
                key.value=0.0
        for name, profile_value in identity.items():
            found = next((key for key in keys if key.name == name), None)
            if found: found.value = profile_value
        found=next((key for key in keys if key.name.endswith(suffix)),None)
        if found: found.value=value
        _aim(cam,(0,-1.55,1.58),(0,0,1.58)); path=out/("expression_"+case+".png")
        scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); output.append(str(path))
        if case == "blink":
            _aim(cam,(1.10,-1.10,1.58),(0,0,1.58)); path=out/"expression_blink_three_quarter_l.png"
            scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); output.append(str(path))
        cases.append({"case":case,"expression":found.name if found else None,"identity_profiles":identity.copy()})
    rig = bpy.data.objects.get("MIA_V06_RIG")
    eye_bones = []
    if rig and rig.type == "ARMATURE":
        # Gaze proof is explicitly neutral-plus-gaze, never the preceding
        # mouth-A case with a moved pupil.
        for key in keys:
            if key.name.startswith("Face.") or key.name.startswith("EyeExtra"):
                key.value = 0.0
        for name, profile_value in identity.items():
            found = next((key for key in keys if key.name == name), None)
            if found: found.value = profile_value
        for name, neutral_value in (("Fcl_EYE_Close", .38), ("Fcl_EYE_Sorrow", .12),
                                    ("Fcl_BRW_Angry", .10), ("Fcl_MTH_Angry", .05),
                                    ("Fcl_MTH_Neutral", .23)):
            found = next((key for key in keys if key.name.endswith(name)), None)
            if found: found.value = neutral_value
        for name in ("J_Adj_L_FaceEye", "J_Adj_R_FaceEye"):
            bone = rig.pose.bones.get(name)
            if bone:
                old_mode, old_rotation = bone.rotation_mode, tuple(bone.rotation_euler)
                bone.rotation_mode="XYZ"; bone.rotation_euler=(.10,0,0); eye_bones.append((bone,old_mode,old_rotation))
        if eye_bones:
            bpy.context.view_layer.update(); _aim(cam,(0,-1.55,1.58),(0,0,1.58)); path=out/"expression_gaze.png"
            scene.render.filepath=str(path); bpy.ops.render.render(write_still=True); output.append(str(path))
            cases.append({"case":"gaze_neutral","bones":[bone.name for bone,_,_ in eye_bones],"identity_profiles":identity.copy(),"expression_reset":"neutral guide restored before eye-bone motion"})
            for bone, old_mode, old_rotation in eye_bones:
                bone.rotation_euler=old_rotation; bone.rotation_mode=old_mode
            bpy.context.view_layer.update()
    for key in keys: key.value = saved[key.name]
    return {"renders":output,"cases":cases,"restored_values":saved}


def _digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()


def _boundary_check(face, body):
    """Nearest-surface evidence for the front Face44 / Body Head cap handoff."""
    groups = {g.name: g.index for g in body.vertex_groups}
    head_i = groups.get("J_Bip_C_Head")
    cap = [v for v in body.data.vertices if _weight(v, head_i) > .50]
    tree = KDTree(len(cap))
    for n, vertex in enumerate(cap): tree.insert(vertex.co, n)
    tree.balance()
    # This is the forehead/crown band where both source surfaces coexist; it
    # rejects lower face features that intentionally sit forward of the cap.
    samples = [v.co for v in face.data.vertices if v.co.z > 1.610]
    distances = [tree.find(point)[2] for point in samples]
    return {"body_head_cap_vertices": len(cap), "face_crown_samples": len(samples),
            "nearest_cap_distance_min": round(min(distances), 7),
            "nearest_cap_distance_mean": round(sum(distances) / len(distances), 7),
            "nearest_cap_distance_max": round(max(distances), 7),
            "interpretation": "comparison is positional only; meshes remain separate and no UV/index welding was performed"}


def build(source, output):
    source, output = Path(source), Path(output)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    face, body = bpy.data.objects.get(FACE_NAME), bpy.data.objects.get(BODY_NAME)
    if not face or not body: raise RuntimeError("v04 MIA_V06 face/body objects not found")
    report=refine_head(face, body, bpy.data.objects.get("MIA_V06_RIG"))
    report["crown_boundary_check"] = _boundary_check(face, body)
    scene,cam=_review_scene(face,body); proof=output/"proof"
    report["actual"]=_render_set(scene,cam,face,body,proof,"head_actual")
    report["material_id_three_quarter"]=_material_id_three_quarter(scene,cam,face,body,proof)
    report["clay"]=_render_set(scene,cam,face,body,proof,"head_clay",clay=True)
    report["wire"]=_render_set(scene,cam,face,body,proof,"head_wire",wire=True)
    report["expressions"]=_pose_proof(scene,cam,face,proof)
    report["postproof_neutral"]=_render_set(scene,cam,face,body,proof,"head_actual_neutral_postproof")
    output.mkdir(parents=True,exist_ok=True)
    blend=output/"Mia_HeadRefine_v06.blend"; bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    # Reopen the saved native study and render the neutral again.  This catches
    # accidental persistence of the last blink/mouth test state.
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    face, body = bpy.data.objects.get(FACE_NAME), bpy.data.objects.get(BODY_NAME)
    scene, cam = _review_scene(face, body)
    report["reopened_neutral"] = _render_set(scene,cam,face,body,proof,"head_actual_neutral_reopened")
    report["color_management"] = {"view_transform": scene.view_settings.view_transform,
                                  "look": scene.view_settings.look,
                                  "exposure": scene.view_settings.exposure,
                                  "gamma": scene.view_settings.gamma,
                                  "skin_ramp": {"interpolation":"EASE","elements":[[.3,.72,.58,.52,1],[.7,.84,.72,.64,1]]},
                                  "body_multiplier": {"rgb":[.94118,.87843,.85098],"source":"Non-Color Face slot7 forehead/temple UV sample"}}
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report.update({"source":str(source),"source_sha256":_digest(source),"output":str(blend),
                   "protocol":"Run once only on v04-mapped Face44 + matching body headcap; body fitting must skip head/neck ROI.",
                   "geometry":"Face: all 44 shape-key vertex positions mapped identically. Body: J_Bip_C_Head/J_Bip_C_Neck weights only.",
                   "lookdev":"Face UV pigment image is multiplied by its toon ramp; Body uses matched response plus a constant Non-Color base-pigment multiplier, with no facial UV image.",
                   "study_context":"v04 torso context only; integrate with v12 body asset",
                   "helper_sha256":_digest(Path(__file__)),"final_native_sha256":_digest(blend)})
    (output/"head_refine_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--source",required=True); parser.add_argument("--output",required=True)
    ns=parser.parse_args(__import__("sys").argv[__import__("sys").argv.index("--") + 1:])
    print(json.dumps(build(ns.source,ns.output),ensure_ascii=False,indent=2))
