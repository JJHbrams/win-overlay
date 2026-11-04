"""Background CPU check of the exact, live-readback AP-profile01 coordinates.

No native is opened or saved. Reconstruct the deterministic field, bind its
hash to the actual apply/capture, then reuse conservative grid + triangle SAT.
Blender BVH overlap misses coplanar intersections in the controlled witness.
"""
from pathlib import Path
import hashlib
import importlib.util
import itertools
import json
import runpy
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/body-h/live/ap-profile01'
report_path = OUT/'collision-verification-v2.json'
assert not report_path.exists(), 'Immutable verification already exists'
start = time.time()
helper = ROOT/'tools/mia/body_grab_live/ap_profile01.py'
lib = runpy.run_path(str(helper), init_globals={'MIA_AP_PROFILE01_NO_MAIN': True})
baseline = np.load(ROOT/'.mia-cache/body-h/shape/assembly/live-D/geometry.npz')
rows = dict(np.load(ROOT/'.mia-cache/migration-to-C/row-ownership.npz'))
v0, faces = baseline['world'], baseline['triangles']
v, changed, _, _, forecast = lib['forecast'](v0, faces, rows, baseline['source_part'])
live = json.loads((OUT/'apply.json').read_text())
capture = json.loads((OUT/'after-v2/capture.json').read_text())
assert lib['sha'](v) == live['candidate_sha256'] == capture['world_sha256'] == lib['EXPECTED']
assert live['actual_coordinate_readback_exact']
changed_faces = np.flatnonzero(changed[faces].any(1))
spec = importlib.util.spec_from_file_location('ap_profile_sat', ROOT/'asset/mia/blender/mia-fit-v003/body/posterior-continuity08/geometry.py')
narrow = importlib.util.module_from_spec(spec); spec.loader.exec_module(narrow)
tri = v[faces].astype(float)
old_tri = v0[faces].astype(float)
lo, hi = tri.min(1), tri.max(1)
region_min, region_max = lo[changed_faces].min(0)-1e-8, hi[changed_faces].max(0)+1e-8
relevant = np.flatnonzero((lo <= region_max).all(1)&(hi >= region_min).all(1))
cell = .006

def cells(i):
    first = np.floor((lo[i]-1e-9)/cell).astype(int)
    last = np.floor((hi[i]+1e-9)/cell).astype(int)
    return itertools.product(*(range(int(a), int(b)+1) for a, b in zip(first, last)))

bins = {}
for i in relevant:
    for key in cells(i): bins.setdefault(key, []).append(int(i))
print('AP_PROFILE_GRID_READY', len(changed_faces), len(relevant), len(bins), flush=True)
# Known crossing, coplanar overlap and separation: SAT must handle all three.
witness_a = np.asarray([(0, 0, 0), (.001, 0, 0), (0, .001, 0)], float)
witness = dict(crossing=np.asarray([(.0002,.0002,-.0005),(.0002,.0002,.0005),(.0008,.0002,0)]),
               coplanar=np.asarray([(.0001,.0001,0),(.0008,.0001,0),(.0001,.0008,0)]),
               separated=np.asarray([(.0002,.0002,.001),(.0002,.0002,.002),(.0008,.0002,.0015)]))
witness_results = {name:bool(narrow.triangle_intersects(witness_a, value)) for name, value in witness.items()}
assert witness_results == dict(crossing=True, coplanar=True, separated=False)
seen = set(); hits = []; inherited = []; tested = 0; shared = 0
for i in changed_faces:
    candidates = set()
    for key in cells(i): candidates.update(bins.get(key, ()))
    for j in candidates:
        pair = (min(int(i), j), max(int(i), j))
        if i == j or pair in seen: continue
        seen.add(pair)
        if (lo[i] > hi[j]+1e-9).any() or (lo[j] > hi[i]+1e-9).any(): continue
        if np.intersect1d(faces[i], faces[j], assume_unique=True).size:
            shared += 1; continue
        tested += 1
        if narrow.triangle_intersects(tri[i], tri[j]):
            (inherited if narrow.triangle_intersects(old_tri[i], old_tri[j]) else hits).append(pair)
report = dict(status='CHANGED_SURFACE_TECHNICAL_PASS' if not hits else 'CHANGED_SURFACE_TECHNICAL_FAIL',
              candidate_sha256=lib['sha'](v), actual_live_readback_bound=True,
              helper_sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
              changed_vertices=int(changed.sum()), tested_changed_faces=len(changed_faces),
              whole_mesh_faces=len(faces), nonadjacent_narrow_phase_pairs=tested,
              shared_vertex_pairs_excluded=shared, new_intersections=hits,
              inherited_changed_region_intersections=inherited,
              controlled_SAT_witnesses=witness_results,
              broadphase='Conservative spatial AABB grid, including coplanar boxes',
              supersedes='collision-verification.json used Blender BVH overlap; controlled coplanar witness failed, so that earlier packet is incomplete',
              profile_min_positive_step_m=forecast['minimum_discrete_front_row_step_m'],
              scope='Every changed incident triangle versus whole mesh; unchanged-only inherited intersections not reevaluated. Shared-vertex neighbors excluded; forecast separately checks orientation and dihedral.',
              native_opened_or_saved=False, art_accepted=False, seconds=time.time()-start)
report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
print(json.dumps(report), flush=True)
assert not hits, 'New nonadjacent triangle intersections'
