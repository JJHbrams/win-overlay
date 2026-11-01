"""Compare real adjacent triangle normals on saved core contribution arrays.

This reports control-cage evidence at the visible lower/lateral crease. It is
not an anatomical PASS test; evaluated surfaces and rotating images are still
required. No native is opened or changed.
"""
from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def audit(source):
    q = np.load(source, allow_pickle=False)
    before, core = q['baseline_world'], q['core_world']
    triangles = q['triangles']
    triangles = triangles[triangles.max(axis=1) < 3957]
    def normals(points):
        raw = np.cross(points[triangles[:, 1]] - points[triangles[:, 0]],
                       points[triangles[:, 2]] - points[triangles[:, 0]])
        area = np.linalg.norm(raw, axis=1) / 2
        return raw / np.maximum(2 * area[:, None], 1e-20), area
    n0, a0 = normals(before)
    n1, a1 = normals(core)
    edges = defaultdict(list)
    for i, tri in enumerate(triangles):
        for a, b in zip(tri, np.roll(tri, -1)):
            edges[tuple(sorted((int(a), int(b))))].append(i)
    rows = []
    for edge, adjacent in edges.items():
        p = core[list(edge)].mean(axis=0)
        if len(adjacent) != 2 or not (1.17 < p[2] < 1.26 and .065 < abs(p[0]) < .115):
            continue
        i, j = adjacent
        angle = lambda n: float(np.degrees(np.arccos(np.clip(n[i] @ n[j], -1, 1))))
        rows.append({'edge': list(edge), 'world_midpoint': p.tolist(),
                     'before_angle_deg': angle(n0), 'core_angle_deg': angle(n1),
                     'triangles': triangles[adjacent].tolist(),
                     'area_ratio': (a1[adjacent] / np.maximum(a0[adjacent], 1e-20)).tolist()})
    return {'source': {'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
            'scope': 'Original Body control triangles at lower/lateral core; same saved-index topology, world coordinates',
            'largest_core_angles': sorted(rows, key=lambda r: r['core_angle_deg'], reverse=True)[:20],
            'interpretation': 'Near-opposed adjacent normals introduced from a previously shallow connection support a fold-back diagnosis at the visible crease. Area reduction alone is not a failure criterion. Do not call the crease a natural costal margin without evaluating the actual surface.',
            'art_acceptance': 'NOT_GRANTED'}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('source', type=Path)
    p.add_argument('report', type=Path)
    a = p.parse_args()
    result = audit(a.source)
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result['largest_core_angles'][:4], indent=2))
