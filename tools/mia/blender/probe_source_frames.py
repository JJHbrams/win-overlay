"""Read-only Blender proof for hidden source objects with stale world matrices.

Run Blender with --background --python this_file -- --input source.blend
--report report.json. Copies are temporary and the source is never saved.
"""

import argparse
import hashlib
import json
import os
import sys

import bpy


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rows(matrix):
    return [list(row) for row in matrix]


def delta(a, b):
    return max(abs(a[i][j] - b[i][j]) for i in range(4) for j in range(4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    input_path = os.path.abspath(args.input)
    before = sha256(input_path)
    bpy.ops.wm.open_mainfile(filepath=input_path)
    probe_collection = bpy.data.collections.new("READONLY_SOURCE_FRAME_PROBE")
    bpy.context.scene.collection.children.link(probe_collection)
    result = []
    for source_name, target_name in (
        ("Body", "Mia_Body_Anatomy_Skin"),
        ("Face", "Mia_Face_AnimeTopology"),
        ("Hair001", "Mia_Body_Anatomy_Skin"),
    ):
        source = bpy.data.objects[source_name]
        original_world = source.matrix_world.copy()
        original_basis = source.matrix_basis.copy()
        copy = source.copy()
        copy.name = "READONLY_ACTIVE_" + source_name
        probe_collection.objects.link(copy)
        copy.hide_viewport = False
        copy.hide_render = False
        copy.hide_set(False)
        bpy.context.view_layer.update()
        evaluated = copy.evaluated_get(bpy.context.evaluated_depsgraph_get())
        target_world = bpy.data.objects[target_name].matrix_world.copy()
        row = {
            "source": source_name,
            "target_frame": target_name,
            "source_cached_world_before_update": rows(original_world),
            "source_basis": rows(original_basis),
            "active_copy_world": rows(copy.matrix_world),
            "evaluated_active_world": rows(evaluated.matrix_world),
            "target_world": rows(target_world),
            "cached_to_active_max_abs_delta": delta(original_world, copy.matrix_world),
            "active_to_target_max_abs_delta": delta(copy.matrix_world, target_world),
            "active_to_evaluated_max_abs_delta": delta(copy.matrix_world, evaluated.matrix_world),
        }
        assert row["active_to_target_max_abs_delta"] < 1e-6, row
        assert row["active_to_evaluated_max_abs_delta"] < 1e-6, row
        result.append(row)
        bpy.data.objects.remove(copy, do_unlink=True)
    after = sha256(input_path)
    assert before == after, "Read-only probe changed source bytes"
    report = {
        "input": input_path,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "source_unchanged": before == after,
        "purpose": "Measure cached hidden-source frames before extracting donor geometry",
        "objects": result,
        "interpretation": (
            "This file's hidden source matrices are not reliable before dependency-graph "
            "evaluation. Active disposable copies agree with the canonical Mia frame. "
            "This is source registration evidence, not a general instruction to rotate assets."
        ),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
    with open(args.report, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print("SOURCE_FRAME_PROBE=" + args.report)


if __name__ == "__main__":
    main()
