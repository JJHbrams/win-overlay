#!/usr/bin/env python3
"""Create an explicitly incomplete, CC0-only anatomy foundation for Mia.

This intentionally imports only the verified ``Body Female - Stylized`` asset
collection.  It does not use v45 geometry, generate clothes, or assert a Mia
likeness.  It is safe to rerun because it creates a new output blend only.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


CC0_COLLECTION = "Body Female - Stylized"
EXPECTED_BODY = "GEO-body_female_stylized"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def args():
    values = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-bundle", required=True)
    parser.add_argument("--reference-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(values)


def new_collection(name, parent=None):
    collection = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    target = parent or bpy.context.scene.collection
    if collection.name not in target.children:
        target.children.link(collection)
    return collection


def collection_bounds(objects):
    points = []
    for obj in objects:
        if obj.type == "MESH":
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("verified CC0 collection did not append mesh geometry")
    return (Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
            Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))))


def disable_mask_modifiers(objects):
    result = []
    removed_driver_paths = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        # The source bundle carries invalid visibility-driver paths.  Remove
        # them from the imported copy before evaluating disabled mask mods.
        removed_by_object = []
        if obj.animation_data:
            for driver in list(obj.animation_data.drivers):
                if "mask_" in driver.data_path.lower():
                    removed_by_object.append(driver.data_path)
                    removed_driver_paths.append({"object": obj.name, "data_path": driver.data_path})
                    obj.driver_remove(driver.data_path, driver.array_index)
        for modifier in obj.modifiers:
            if "mask" in modifier.name.lower() or modifier.type == "MASK":
                modifier.show_viewport = False
                modifier.show_render = False
                result.append({"object": obj.name, "modifier": modifier.name, "disabled": True, "drivers_removed": removed_by_object})
    return {"mask_modifiers": result, "invalid_visibility_drivers_removed": removed_driver_paths}


def add_reference_images(reference_dir, refs):
    collection = bpy.data.collections["Refs"]
    filenames = ["mia-clean-master-v22.png", "mia-canonical-source-v22.png", "mia-expressions-clean-16-v22.png"]
    for index, filename in enumerate(filenames):
        path = reference_dir / filename
        if not path.exists():
            raise FileNotFoundError(path)
        image = bpy.data.images.load(str(path), check_existing=True)
        image.name = "REF_" + path.stem
        image.pack()
        empty = bpy.data.objects.new("REF_" + path.stem, None)
        empty.empty_display_type = "IMAGE"
        empty.data = image
        empty.empty_display_size = 1.0
        empty.location = (10.0 + index * 2.0, 0.0, 1.0)
        empty.hide_render = True
        collection.objects.link(empty)
        refs.append({"file": filename, "packed": image.packed_file is not None, "object": empty.name})


def main():
    options = args()
    source_bundle = Path(options.source_bundle).resolve()
    reference_dir = Path(options.reference_dir).resolve()
    output = Path(options.output).resolve()
    source_sha_before = sha256(source_bundle)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(source_bundle), link=False) as (data_from, data_to):
        if CC0_COLLECTION not in data_from.collections:
            raise RuntimeError("missing verified collection %r" % CC0_COLLECTION)
        data_to.collections = [CC0_COLLECTION]
    imported = bpy.data.collections.get(CC0_COLLECTION)
    if not imported:
        raise RuntimeError("Blender did not append %r" % CC0_COLLECTION)
    bpy.context.scene.collection.children.link(imported)
    imported.name = "Anatomy"
    anatomy_objects = list(imported.objects)
    body = bpy.data.objects.get(EXPECTED_BODY)
    if body is None or body not in anatomy_objects:
        raise RuntimeError("expected CC0 body object %r not in scoped collection" % EXPECTED_BODY)
    source_counts = {"vertices": len(body.data.vertices), "polygons": len(body.data.polygons)}
    if source_counts != {"vertices": 12502, "polygons": 12500}:
        raise RuntimeError("unexpected CC0 body topology %s" % source_counts)
    body.name = "BodyHead_Master"
    body["role"] = "complete_generic_anatomy_master"
    body["mia_likeness"] = "NOT_STARTED"
    eyes = []
    for obj in anatomy_objects:
        if obj != body and obj.type == "MESH":
            obj.name = "Eyes_" + obj.name.removeprefix("GEO-")
            obj["role"] = "existing_base_eye_geometry"
            eyes.append(obj.name)
    mask_cleanup = disable_mask_modifiers(anatomy_objects)
    low, high = collection_bounds(anatomy_objects)
    original_height = high.z - low.z
    factor = 1.68 / original_height
    for obj in anatomy_objects:
        obj.location = Vector((obj.location.x, obj.location.y, (obj.location.z - low.z) * factor))
        obj.scale = obj.scale * factor
    for name in ("ScalpGuide", "Hair", "Garments", "Bag", "Hardware", "Refs", "RigGuide"):
        col = new_collection(name)
        col["status"] = "PLANNED_EMPTY"
    new_collection("ScalpGuide")["purpose"] = "future hair-root guide; no scalp deletion or hair asset exists yet"
    new_collection("Garments")["purpose"] = "future dedicated garment meshes; no body mask is enabled"
    new_collection("RigGuide")["purpose"] = "scale and joint-reference markers only; no armature exists"
    refs = []
    add_reference_images(reference_dir, refs)
    guide = bpy.data.objects.new("GUIDE_height_1_68m", None)
    guide.empty_display_type = "ARROWS"
    guide.empty_display_size = 0.12
    guide.location = (-0.55, 0.0, 0.84)
    guide["purpose"] = "scale reference only"
    bpy.data.collections["RigGuide"].objects.link(guide)
    status = bpy.data.objects.new("MIA_FOUNDATION_STATUS", None)
    status["overall_status"] = "INCOMPLETE"
    status["scope"] = "generic CC0 anatomy foundation; not Mia likeness, wardrobe, hair, bag, rig, or animation"
    status["source_collection"] = CC0_COLLECTION
    status["source_bundle_sha256"] = source_sha_before
    status["license_scope"] = "Only Body Female - Stylized (metadata CC0) appended; unrelated bundle assets were not imported."
    status["body_hide_groups"] = "NONE; no opaque garment coverage has been validated"
    status["pending"] = "Mia sculpt, scalp/hair, garments, bag, hardware, facial rig, body rig, corrective tests, animation events"
    bpy.context.scene.collection.objects.link(status)
    inventory = {
        "schema": "mia-layered-foundation/v1",
        "status": "INCOMPLETE",
        "source_bundle": str(source_bundle),
        "source_bundle_sha256_before": source_sha_before,
        "license": {
            "scoped_collection": CC0_COLLECTION,
            "metadata_author": "Julien Kaspar",
            "metadata_license": "CC0",
            "scope_note": "Other source-bundle contents, including the Rain Rig CC-BY license text, were not appended.",
        },
        "anatomy": {
            "body_object": body.name,
            "source_topology": source_counts,
            "existing_eye_objects": eyes,
            "original_height": original_height,
            "uniform_scale_factor": factor,
            "normalized_height_m": 1.68,
            "mask_modifiers_disabled": mask_cleanup["mask_modifiers"],
            "invalid_visibility_drivers_removed": mask_cleanup["invalid_visibility_drivers_removed"],
            "body_hide_groups": [],
        },
        "references": refs,
        "planned_empty_collections": ["ScalpGuide", "Hair", "Garments", "Bag", "Hardware", "RigGuide"],
        "pending": ["Mia-specific sculpt", "hair", "garments", "bag", "hardware", "rig", "correctives", "event animation"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    source_sha_after = sha256(source_bundle)
    if source_sha_after != source_sha_before:
        raise RuntimeError("SOURCE BUNDLE MUTATED")
    inventory["source_bundle_sha256_after"] = source_sha_after
    inventory["source_bundle_immutable"] = source_sha_before == source_sha_after
    report = Path(options.report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "body": body.name, "eyes": eyes, "source_immutable": True}))


if __name__ == "__main__":
    main()
