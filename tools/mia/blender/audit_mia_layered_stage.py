#!/usr/bin/env python3
"""Read-only art and structure evidence renderer for a saved Mia stage."""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Saved .blend to inspect (never saved).")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--stage", required=True, help="Human-readable checkpoint label.")
    parser.add_argument("--resolution", type=int, default=384)
    parser.add_argument("--quick", action="store_true", help="Use eight yaw angles instead of the full twelve.")
    parser.add_argument("--probe", action="store_true",
                        help="Twelve-frame runtime smoke test: two yaws, one elevation, three crops and two modes.")
    return parser.parse_args(values)


def digest(path):
    result = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def linked(obj):
    bpy.context.scene.collection.objects.link(obj)
    return obj


def material_terms(obj):
    return [slot.material.name if slot.material else None for slot in obj.material_slots]


def excluded(obj):
    """Archives and reference helpers are evidence, not part of the stage assembly."""
    chain = []
    collection = getattr(obj, "users_collection", ())
    for item in collection:
        chain.append(item.name.upper())
    text = " ".join([obj.name.upper()] + chain)
    return ("SOURCE_ARCHIVE" in text or "REFERENCE" in text or obj.type == "EMPTY"
            or obj.type in {"CAMERA", "LIGHT"})


def stage_meshes():
    """Include renderable curves and respect parent collection visibility."""
    render_collections = set()

    def visit(layer, allowed=True):
        allowed = allowed and not layer.exclude and not layer.collection.hide_render
        if allowed:
            render_collections.add(layer.collection.name)
        for child in layer.children:
            visit(child, allowed)

    visit(bpy.context.view_layer.layer_collection)
    return [obj for obj in bpy.context.scene.objects
            if obj.type in {"MESH", "CURVE"} and not obj.hide_render and not excluded(obj)
            and any(collection.name in render_collections for collection in obj.users_collection)]


def make_camera():
    data = bpy.data.cameras.new("MIA_STAGE_AUDIT_CAMERA")
    data.type = "ORTHO"
    obj = linked(bpy.data.objects.new("MIA_STAGE_AUDIT_CAMERA", data))
    bpy.context.scene.camera = obj
    return obj


def aim(camera, location, target, ortho):
    camera.data.ortho_scale = ortho
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def point_for(yaw, elevation, target, distance):
    yaw_rad, elevation_rad = math.radians(yaw), math.radians(elevation)
    return Vector(target) + Vector((
        math.sin(yaw_rad) * distance * math.cos(elevation_rad),
        -math.cos(yaw_rad) * distance * math.cos(elevation_rad),
        math.sin(elevation_rad) * distance,
    ))


def neutral_material(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (.46, .47, .49, 1)
        bsdf.inputs["Roughness"].default_value = .82
    return material


def disable_outline_nodes(obj):
    disabled = []
    for modifier in obj.modifiers:
        if modifier.type == "NODES" and "OUTLINE" in modifier.name.upper():
            modifier.show_render = False
            disabled.append(modifier.name)
    return disabled


def has_name_token(name, token):
    return bool(re.search(r"(^|[_ .-])" + re.escape(token) + r"($|[_ .-])", name, re.I))


def is_face(obj):
    """Only identify a deliberately named face mesh, never arbitrary *surface* meshes."""
    role = str(obj.get("part_role", obj.get("role", ""))).upper()
    if role:
        return role == "ANATOMY_FACE_TOPOLOGY"
    return (role == "ANATOMY_FACE_TOPOLOGY" or obj.name.upper().startswith("MIA_FACE")
            or obj.name.upper().startswith("FACE_") or has_name_token(obj.name, "face"))


def alpha_face_layer(obj):
    """Skip only a standalone expression card, not an integrated face with eye slots."""
    if is_face(obj):
        return False
    materials = [name.upper() for name in material_terms(obj) if name]
    has_skin_core = any("SKIN" in name or "FACEMOUTH" in name for name in materials)
    expression_only = any(term in " ".join(materials) for term in
                          ("BROW", "LASH", "EYEL", "IRIS", "EYE_", "EYEBALL"))
    return expression_only and not has_skin_core


def is_body_core(obj):
    role = str(obj.get("part_role", obj.get("role", ""))).upper()
    if role:
        return role in {"ANATOMY_BODY_SKIN", "ANATOMY_BODY_SKIN_ONLY"}
    return role == "ANATOMY_BODY_SKIN" or obj.name.upper().startswith("MIA_BODY") or has_name_token(obj.name, "body")


def copy_face_core(source, result):
    """Keep SKIN/FaceMouth polygons; alpha expression cards must not become clay slabs."""
    copy = source.copy()
    copy.data = source.data.copy()
    copy.name = "QA_FACE_CORE_" + source.name
    linked(copy)
    copy.hide_render = False
    copy.hide_viewport = False
    accepted = {index for index, material in enumerate(copy.data.materials)
                if material and ("SKIN" in material.name.upper() or "FACEMOUTH" in material.name.upper())}
    if not accepted:
        bpy.data.objects.remove(copy, do_unlink=True)
        return None, {"source": source.name, "kept_material_slots": [], "skipped": "no SKIN/FaceMouth"}
    bpy.context.view_layer.objects.active = copy
    copy.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for polygon in copy.data.polygons:
        polygon.select = polygon.material_index not in accepted
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.delete(type="FACE")
    bpy.ops.object.mode_set(mode="OBJECT")
    copy.select_set(False)
    names = [copy.data.materials[i].name for i in sorted(accepted)]
    copy.data.materials.clear()
    copy.data.materials.append(neutral_material("QA_CLAY_FACE_CORE"))
    return copy, {"source": source.name, "kept_material_slots": names, "skipped": None}


def structure_copies(meshes):
    copies, details, skipped, outlines = [], [], [], {}
    for source in meshes:
        if alpha_face_layer(source):
            skipped.append(source.name)
            continue
        if is_face(source):
            copy, detail = copy_face_core(source, details)
            details.append(detail)
            if copy is None:
                skipped.append(source.name)
                continue
        else:
            copy = source.copy()
            copy.data = source.data.copy()
            copy.name = "QA_CLAY_" + source.name
            linked(copy)
            copy.hide_render = False
            copy.hide_viewport = False
            copy.data.materials.clear()
            copy.data.materials.append(neutral_material("QA_CLAY_" + source.name))
        outlines[copy.name] = disable_outline_nodes(copy)
        copies.append(copy)
    return copies, {"face_core_isolation": details,
                    "excluded_alpha_face_layers": skipped,
                    "disabled_outline_nodes_on_copies": outlines}


def inventory(meshes):
    rows = []
    for obj in meshes:
        rows.append({
            "name": obj.name,
            "object_type": obj.type,
            "collections": sorted(collection.name for collection in obj.users_collection),
            "vertices": len(getattr(obj.data, "vertices", ())),
            "edges": len(getattr(obj.data, "edges", ())),
            "polygons": len(getattr(obj.data, "polygons", ())),
            "splines": len(getattr(obj.data, "splines", ())),
            "materials": material_terms(obj),
            "part_ownership_custom_properties": {
                key: obj[key] for key in obj.keys() if key not in {"_RNA_UI"}},
            "shape_keys": len(obj.data.shape_keys.key_blocks) if obj.data.shape_keys else 0,
            "hide_render": obj.hide_render,
        })
    return rows


def canonical_owner_check(meshes):
    """Reject duplicated active source cores, while allowing separate alpha face parts."""
    faces = []
    bodies = []
    for obj in meshes:
        role = str(obj.get("part_role", obj.get("role", ""))).upper()
        source_mesh = str(obj.get("source_mesh", "")).upper()
        if role == "ANATOMY_FACE_TOPOLOGY" or (not role and obj.name.upper().startswith("MIA_FACE")):
            faces.append(obj.name)
        if role in {"ANATOMY_BODY_SKIN", "ANATOMY_BODY_SKIN_ONLY"} or (not role and
                (source_mesh == "BODY" or obj.name.upper().startswith("MIA_BODY"))):
            bodies.append(obj.name)
    result = {
        "canonical_visible_face_names": sorted(faces),
        "canonical_visible_body_names": sorted(bodies),
        "required_face_count": 1,
        "required_body_count": 1,
        "passed": len(faces) == 1 and len(bodies) == 1,
    }
    if not result["passed"]:
        result["failure"] = (
            "Expected exactly one visible canonical anatomy Face and Body; "
            "faces=[{faces}], bodies=[{bodies}]".format(
                faces=", ".join(result["canonical_visible_face_names"]) or "<none>",
                bodies=", ".join(result["canonical_visible_body_names"]) or "<none>"))
    return result


def shape_key_names(obj):
    if not obj or not obj.data.shape_keys:
        return []
    return [key.name for key in obj.data.shape_keys.key_blocks]


def canonical_face_morph_report(owner_check):
    """Compare the active face against the archived source without limiting additions."""
    active_name = next(iter(owner_check["canonical_visible_face_names"]), None)
    active = bpy.data.objects.get(active_name) if active_name else None
    archived = bpy.data.objects.get("Face")
    active_names = shape_key_names(active)
    archived_names = shape_key_names(archived)
    missing = [name for name in archived_names if name not in active_names]
    extras = [name for name in active_names if name not in archived_names]
    archived_sequence_in_active_order = [name for name in active_names if name in archived_names]
    return {
        "canonical_face_object": active.name if active else None,
        "canonical_face_key_count": len(active_names),
        "canonical_face_key_names": active_names,
        "archived_source_face_object": archived.name if archived else None,
        "archived_source_face_key_count": len(archived_names),
        "archived_source_face_key_names": archived_names,
        "missing_archived_source_key_names": missing,
        "extra_corrective_key_names": extras,
        "all_archived_source_names_preserved": bool(archived) and not missing,
        "archived_source_order_preserved": bool(archived) and archived_sequence_in_active_order == archived_names,
        "note": "Extra corrective keys are reported, not rejected solely because of count.",
    }


def render_set(scene, camera, output, mode, views):
    records = []
    for scale_name, target, ortho, distance in views:
        for elevation in views.elevations:
            for yaw in views.yaws:
                name = f"{mode}_{scale_name}_y{yaw:03d}_e{elevation:+03d}.png"
                aim(camera, point_for(yaw, elevation, target, distance), target, ortho)
                path = output / name
                scene.render.filepath = str(path)
                bpy.ops.render.render(write_still=True)
                records.append({"file": name, "mode": mode, "scale": scale_name,
                                "yaw": yaw, "elevation": elevation, "ortho_scale": ortho})
    return records


class Views(list):
    pass


def main():
    args = arguments()
    source = Path(args.input).resolve()
    output = Path(args.output_dir).resolve()
    report = Path(args.report).resolve()
    if not source.is_file():
        raise SystemExit("input does not exist: " + str(source))
    before = digest(source)
    output.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = args.resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = make_camera()
    meshes = stage_meshes()
    owner_check = canonical_owner_check(meshes)
    morph_report = canonical_face_morph_report(owner_check)
    if not owner_check["passed"]:
        after = digest(source)
        report.write_text(json.dumps({
            "stage": args.stage, "input": str(source),
            "input_sha256_before": before, "input_sha256_after": after,
            "input_unchanged": before == after,
            "inventory": inventory(meshes),
            "duplicate_owner_checks": owner_check,
            "canonical_face_morphs": morph_report,
            "status": "EVIDENCE_ONLY: PRE_RENDER_OWNER_GATE_FAILED",
        }, indent=2), encoding="utf-8")
        raise RuntimeError(owner_check["failure"])
    original_hidden = [(obj, obj.hide_render) for obj in meshes]
    views = Views([
        ("full", (0, 0, .88), 2.0, 3.0),
        ("torso", (0, 0, 1.20), 1.05, 1.7),
        ("head", (0, 0, 1.57), .60, 1.0),
    ])
    views.yaws = [0, 180] if args.probe else list(range(0, 360, 45 if args.quick else 30))
    views.elevations = [0] if args.probe else [-10, 0, 10]
    art = render_set(scene, camera, output, "art", views)
    for obj, _ in original_hidden:
        obj.hide_render = True
    copies, isolation = structure_copies(meshes)
    face_sources = [obj.name for obj in meshes if is_face(obj)]
    body_sources = [obj.name for obj in meshes if is_body_core(obj)]
    face_copies = [obj.name for obj in copies if obj.name.startswith("QA_FACE_CORE_")]
    body_copies = [obj.name for obj in copies if obj.name.removeprefix("QA_CLAY_") in body_sources]
    # A known source face/body pair is an assembly contract: a structural run
    # with either component absent would be misleading evidence, not a valid audit.
    if face_sources and not face_copies:
        raise RuntimeError("structure audit omitted all recognized face cores: " + ", ".join(face_sources))
    if body_sources and not body_copies:
        raise RuntimeError("structure audit omitted all recognized body cores: " + ", ".join(body_sources))
    isolation["structure_copy_visibility"] = [
        {"name": obj.name, "hide_render": obj.hide_render, "hide_viewport": obj.hide_viewport}
        for obj in copies]
    isolation["assembled_core_assertion"] = {
        "recognized_face_sources": face_sources, "rendered_face_core_copies": face_copies,
        "recognized_body_sources": body_sources, "rendered_body_core_copies": body_copies,
        "passed": bool((not face_sources or face_copies) and (not body_sources or body_copies)),
    }
    structure = render_set(scene, camera, output, "structure", views)
    for obj, state in original_hidden:
        obj.hide_render = state
    for obj in copies:
        bpy.data.objects.remove(obj, do_unlink=True)
    after = digest(source)
    expected_per_mode = len(views.yaws) * len(views.elevations) * 3
    document = {
        "stage": args.stage,
        "input": str(source),
        "input_sha256_before": before, "input_sha256_after": after,
        "input_unchanged": before == after,
        "render": {"engine": scene.render.engine, "resolution": args.resolution,
                   "camera": {"type": camera.data.type, "front": "-Y", "yaw_count": len(views.yaws),
                              "elevations": views.elevations,
                              "views": [{"scale": n, "target": t, "ortho": o} for n, t, o, _ in views]}},
        "inventory": inventory(meshes),
        "duplicate_owner_checks": owner_check,
        "canonical_face_morphs": morph_report,
        "isolation": isolation,
        "art_records": art, "structure_records": structure,
        "actual_art_count": len(art), "actual_structure_count": len(structure),
        "expected_per_mode": expected_per_mode,
        "status": "EVIDENCE_ONLY: renders and inventory require independent visual review; no likeness PASS inferred.",
    }
    report.write_text(json.dumps(document, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
