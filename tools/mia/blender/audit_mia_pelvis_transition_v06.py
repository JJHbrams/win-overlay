"""Read-only semantic diagnosis for the derived pelvis-to-thigh transition."""
import argparse
import collections
import json
import sys
from pathlib import Path

import bpy


def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def main():
    args = parse()
    bpy.ops.wm.open_mainfile(filepath=args.input)
    body = bpy.data.objects["MIA_V06_BODY_SKIN"]
    names = {group.index: group.name for group in body.vertex_groups}
    rows = []
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if not (.66 < point.z < 1.10 and abs(point.x) < .34):
            continue
        weights = sorted(((entry.weight, names.get(entry.group, "")) for entry in vertex.groups), reverse=True)
        rows.append({"x": point.x, "y": point.y, "z": point.z,
                     "dominant": weights[0][1] if weights else "",
                     "dominant_weight": weights[0][0] if weights else 0.0,
                     "weights": weights[:3]})
    slices = {}
    for center in (.70, .75, .80, .85, .90, .95, 1.00, 1.05):
        points = [item for item in rows if abs(item["z"] - center) <= .012]
        slices[str(center)] = {
            "vertices": len(points),
            "dominant_groups": dict(collections.Counter(item["dominant"] for item in points)),
            "bounds_world": [[min(item[key] for item in points) for key in ("x", "y", "z")],
                             [max(item[key] for item in points) for key in ("x", "y", "z")]] if points else None,
        }
    body_groups = {group.name: {"vertices_over_22": sum(any(entry.group == group.index and entry.weight > .22
                     for entry in vertex.groups) for vertex in body.data.vertices)} for group in body.vertex_groups
                   if any(token in group.name for token in ("Hips", "UpperLeg", "LowerLeg", "Spine"))}
    report = {"space": "evaluated object world space", "slices": slices,
              "transition_group_inventory": body_groups}
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
