"""Summarize immutable eye inputs and an already captured read-only live probe."""
from pathlib import Path
import argparse
import hashlib
import json
import math

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', type=Path, required=True)
    args = ap.parse_args()
    root = args.root.resolve()
    out = root / '.mia-cache/eye-roi'
    out.mkdir(parents=True, exist_ok=True)
    fit = root / 'asset/mia/blender/mia-fit-v003'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    read = lambda p: json.loads(p.read_text(encoding='utf8'))
    audit = read(fit / 'eyes/baseline-eyes-fold.json')
    eye_rows = []
    for row in audit['eyes']:
        upper, lower = row['measure']['upper'], row['measure']['lower']
        width = upper['width_mm']
        samples = []
        for t in (.25, .5, .75):
            u = float(np.interp(t, upper['t'], upper['height_mm']))
            l = float(np.interp(t, lower['t'], lower['height_mm']))
            samples.append(dict(t=t, upper_percent_width=100*u/width,
                                lower_depth_percent_width=-100*l/width,
                                total_percent_width=100*(u-l)/width))
        eye_rows.append(dict(side=row['side'], screen=row['screen'],
                             projected_canthus_width_mm=width, samples=samples))
    matrix = np.asarray(audit['camera']['matrix'])
    camera_right_roll = math.degrees(math.atan2(float(matrix[2, 0]), float(matrix[0, 0])))
    call_path = out / 'live/stage-a-call.json'
    call = read(call_path)
    assert not call['is_error'] and call['structured']['status'] == 'ok'
    live = json.loads(call['structured']['stdout'])
    live['actors'] = {n: {k: value for k, value in row.items()
                          if k in ('exists','type','viewport_hidden','hide_render','visible_get',
                                   'raw_vertices','polygons','raw_co_sha256','key_count',
                                   'active_keys','lower_lid_corrective_present','eye_corrective_names',
                                   'basis_co_sha256','key_names_sha256','UV','material_slots',
                                   'evaluated','crease_material_signals')}
                      for n, row in live['actors'].items()}
    # The full driver/pose evidence remains in the unchanged raw call receipt.
    live['raw_call'] = dict(path=str(call_path), sha256=sha(call_path))
    files = [
        root/'asset/mia/references/received/mia-face-reaffirmed-20261031.png',
        root/'asset/mia/references/received/mia-eye-lash-user-markup-20261102.png',
        root/'asset/mia/references/mia-expression-style-confirmed-20261031.png',
        fit/'eyes/baseline-eyes-fold.json', fit/'eyes/lower-lid-balance.json',
        fit/'eyes/lower-lid-balance.npz', fit/'eyes/lower-lid-evaluated-checks.json',
        fit/'eyes/upper-crease-visible-C.json', fit/'eyes/quick-A/render-records.json',
        fit/'eyes/crease-C/render-records.json', fit/'integration/selected-components-cpu.json',
        root/'.mia-cache/face-live/brow-expression4/expression-evidence.json',
    ]
    lower = read(fit/'eyes/lower-lid-balance.json')
    ledger = dict(
        scope='A-C input/configuration ledger; no new eye geometry or source-error score',
        files=[dict(path=str(p), sha256=sha(p), bytes=p.stat().st_size) for p in files],
        native_sha256=audit['sha256'],
        baseline_measurement=dict(state='SAVED R3b, not current live final or source-registered error',
                                  camera_right_axis_roll_degrees=camera_right_roll,
                                  canthus_local_2D_frame_is_measurement_only=True, eyes=eye_rows,
                                  limitation='Removing projected roll does not remove 3D base/depth or source-pose differences. Width asymmetry is not an expansion target.'),
        composition_ledger=[
            dict(id='saved_R3b', apply=[], lower_lid=False, crease_C=False),
            dict(id='quick_A_after', apply=['eyes/apply_lower_lid.py:apply'], lower_lid=True, crease_C=False),
            dict(id='crease_C', apply=['eyes/apply_lower_lid.py:apply',
                                      'eyes/apply_aligned_crease.py:apply(upper-crease-visible-C.json)'],
                 lower_lid=True, crease_C=True,
                 material_cache='Render factory original slots explicitly refreshed after applying crease copies.'),
            dict(id='selected_composition_CPU', lower_lid=True, crease_C=True,
                 unrelated_changes=['v29 crown pigment','rear U cleanup','partial brow display'],
                 use_as_eye_only_baseline=False),
            dict(id='brow_expression8', apply=['partial_brow_display.py:.60'], lower_lid=False,
                 crease_C=False, genuine_shared_head_keys=47,
                 source_pose_registered=False,
                 limitation='Brow display evidence cannot establish latest composed eye or live regression.'),
        ],
        existing_lower_corrective=dict(method=lower['method'],
                                       owners=[dict(owner=r['owner'], changed_raw_points=r['vertices'],
                                                    raw_maximum_mm=r['maximum_delta_mm']) for r in lower['entries']],
                                       source_validated=False,
                                       gate='(1-max(Close,Joy,matching side Close/Joy))*(1-.5*Surprise)*(1-.8*Angry)',
                                       limitation='Nine historical key/depth cases are not arbitrary-pose collision or source-ART acceptance.'),
        actual_live=live,
        next_test=dict(compositions=['saved_R3b','lower_only','lower_plus_crease_C'],
                       first_views=['front','profile','left_oblique','right_oblique'],
                       first_mode='hairOFF target look + actual aperture coordinates, same source-package cameras',
                       remaining_gate=['hairON','matte geometry','high/low and continuous turn',
                                       'neutral/half/full blink/smile/surprise/frown'],
                       state='PREPARED, GPU not granted, no new candidate selected'),
        protected=dict(face_identity=True, orbital_cheek_volume=True, sclera_iris=True,
                       global_head_scale=True, body=True, hair=True,
                       future_body_remap='Require original_control_id correspondence; never replay raw62 indices into a new topology.'),
        ART=False, native_saved=False)
    destination = out/'input-ledger.json'
    destination.write_text(json.dumps(ledger, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(path=str(destination), sha256=sha(destination),
                          eye_metrics=eye_rows, live_key_values_unchanged=live['key_values_unchanged']), ensure_ascii=False))


if __name__ == '__main__':
    main()
