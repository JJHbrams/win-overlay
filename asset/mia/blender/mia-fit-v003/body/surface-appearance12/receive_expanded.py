"""Independent E topology/source-face receipt; never edits producer files."""
from pathlib import Path
import argparse
import hashlib
import sys
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[6] / 'tools/mia/review_h'))
from paths import recorded_path
from surface_api import load_surface, read_json, write_json, sha, array_sha
from topology_revision_guard import certify_retained_correspondence, physical_replacement_mask


def exact(a, b, label):
    a, b = np.ascontiguousarray(a), np.ascontiguousarray(b)
    if a.shape != b.shape or a.dtype != b.dtype or not np.array_equal(a.view(np.uint8), b.view(np.uint8)):
        raise ValueError('Protected data differs: '+label)


def read_npz(path):
    with np.load(path, allow_pickle=False) as values:
        return {key: values[key] for key in values.files}


def source_branches(previous, target, old, new):
    """Retained donor branches inherit validated D3 SAME source-face labels."""
    labels = {}
    for part, face, region in zip(old['source_part'][previous['meshfaceid']],
                                  old['source_face'][previous['meshfaceid']], previous['face_region']):
        if region in [6, 7] and face >= 0:
            key = (int(part), int(face))
            if key in labels and labels[key] != int(region):
                raise ValueError('Old original source-face arm branch is ambiguous')
            labels[key] = int(region)
    expected = np.array([labels.get((int(part),int(face)), -1)
                         for part, face in zip(new['source_part'][target['meshfaceid']],
                                               new['source_face'][target['meshfaceid']])], np.int16)
    known = expected > 0
    if not np.array_equal(target['face_region'][known], expected[known]):
        raise ValueError('E lost retained donor hand/finger/forearm ownership via SAME original source_face')
    points = target['world'][target['triangles']].mean(1)
    lateral = np.isin(target['face_region'], [8,9]) & (abs(points[:,0])>.30)
    if lateral.any():
        raise ValueError('E pelvis branch includes lateral hands in this frozen pose')
    return dict(status='PASS actual original source-part/source-face branch inheritance',
                matched_retained_donor_arm_faces=int(known.sum()), branch_mismatches=0,
                lateral_hand_in_pelvis_diagnostic=0,
                correction_policy='No position-based label patch; positions only diagnose this frozen pose.')


def receive(previous_path, incoming_path, proof_path, destination):
    previous_path, incoming_path, proof_path = map(Path, [previous_path, incoming_path, proof_path])
    out = Path(destination); out.mkdir(exist_ok=True, parents=True)
    incoming_bytes = incoming_path.read_bytes()
    digest = hashlib.sha256(incoming_bytes).hexdigest()
    metadata_path = incoming_path.with_suffix('.json')
    metadata_bytes = metadata_path.read_bytes()
    snapshot = out/(digest[:12]+'.npz')
    snapshot.write_bytes(incoming_bytes)
    snapshot.with_suffix('.json').write_bytes(metadata_bytes)
    previous, target = load_surface(previous_path), load_surface(snapshot)
    meta, proof = target['meta'], read_json(proof_path)
    if meta['surface_npz_sha256'] != digest:
        raise ValueError('Incoming surface metadata SHA mismatch')
    old_path = recorded_path(proof['previous_joined_path'], expected_sha256=proof['previous_joined_sha256'])
    new_path = recorded_path(proof['new_joined_path'], expected_sha256=proof['new_joined_sha256'])
    corr_path = recorded_path(meta['retained_correspondence_path'], expected_sha256=meta['retained_correspondence_sha256'])
    expected_files = {str(old_path): proof['previous_joined_sha256'],
                      str(new_path): proof['new_joined_sha256'],
                      str(corr_path): meta['retained_correspondence_sha256']}
    for path, expected in expected_files.items():
        if sha(path) != expected:
            raise ValueError('Joined/correspondence source fingerprint changed: '+path)
    old, new, corr = map(read_npz, [old_path, new_path, corr_path])
    exact(old['world'], previous['world'], 'D3 full-joined/body-export world relation')
    exact(new['world'], target['world'], 'E full-joined/body-export world relation')
    exact(old['triangles'][previous['meshfaceid']], previous['triangles'], 'D3 body face-ID relation')
    exact(new['triangles'][target['meshfaceid']], target['triangles'], 'E body face-ID relation')
    # The declared old/new head triangle lists must cover ALL actual head faces.
    old_head, new_head = corr['old_head_triangle_id'], corr['new_head_triangle_id']
    if not np.array_equal(np.sort(old_head), np.flatnonzero(old['source_part']==1)):
        raise ValueError('Old head correspondence is a selected subset')
    if not np.array_equal(np.sort(new_head), np.flatnonzero(new['source_part']==1)):
        raise ValueError('New head correspondence is a selected subset')
    exact(old['world'][old['triangles'][old_head]], new['world'][new['triangles'][new_head]], 'ordered head world triangles')
    head_channels = ['old_loop_uv', 'source_corner_normals', 'source_corner_bary',
                     'triangle_materials', 'source_part', 'source_face']
    for key in head_channels:
        exact(old[key][old_head], new[key][new_head], 'complete head '+key)
    exact(old['world'][corr['old_neck_row_ids']], new['world'][corr['new_neck_row_ids']], 'fixed D3 neck rows')
    oi, ni = corr['old_vertex_id'], corr['new_vertex_id']
    for key in ['source_vertex', 'guide_vertex']:
        exact(old[key][oi], new[key][ni], 'retained point '+key)
    # Convert declared full-joined triangle IDs to actual body-export order.
    inverse = np.full(len(new['triangles']), -1, np.int64)
    inverse[target['meshfaceid']] = np.arange(len(target['triangles']))
    body_ids = inverse[corr['interpolated_new_triangle_id']]
    if np.any(body_ids < 0):
        raise ValueError('Artificial forearm representation points at a non-body triangle')
    representation = {key: corr[key] for key in ['interpolated_old_vertex_id', 'interpolated_new_barycentric', 'interpolated_source_face']}
    representation.update(interpolated_new_triangle_id=body_ids,
                          old_source_vertex=old['source_vertex'],
                          old_source_face=old['source_face'][previous['meshfaceid']],
                          new_source_face=new['source_face'][target['meshfaceid']],
                          old_source_corner_bary=old['source_corner_bary'][previous['meshfaceid']],
                          new_source_corner_bary=new['source_corner_bary'][target['meshfaceid']])
    physical = certify_retained_correspondence(previous, target, corr, meta['expanded_collar_sections'],
                                               corr['protected_core_old_ids'], representation=representation)
    branches = source_branches(previous, target, old, new)
    represented = np.union1d(oi, corr['interpolated_old_vertex_id'])
    if not np.array_equal(represented, corr['expected_retained_old_ids']):
        raise ValueError('Actual strict-or-source-face coverage differs from complete declared retained IDs')
    absent = np.setdiff1d(np.arange(len(previous['world'])), represented)
    if not np.array_equal(absent, corr['excluded_old_vertex_ids']):
        raise ValueError('Actual omitted old vertices differ from declared expanded replacement IDs')
    # Verify old source-face barycentric values against actual old corner arrays,
    # not just the provided per-point summary of the obsolete forearm split.
    target_source_bary = np.einsum('ij,ijk->ik', corr['interpolated_new_barycentric'], new['source_corner_bary'][corr['interpolated_new_triangle_id']])
    if np.max(abs(target_source_bary-corr['interpolated_old_source_corner_bary'])) > 1e-6:
        raise ValueError('Old/new original source barycentric relation differs')
    if sha(incoming_path)!=digest or metadata_path.read_bytes()!=metadata_bytes:
        raise ValueError('Incoming E files changed during receipt')
    for path, expected in expected_files.items():
        if sha(path)!=expected:
            raise ValueError('Joined/correspondence source changed during read: '+path)
    corr_copy = out/('E-correspondence-'+sha(corr_path)[:12]+'.npz')
    if not corr_copy.exists(): corr_copy.write_bytes(corr_path.read_bytes())
    proof_copy = out/('E-producer-proof-'+sha(proof_path)[:12]+'.json')
    if not proof_copy.exists(): proof_copy.write_bytes(proof_path.read_bytes())
    report = dict(status='PASS independent topology/source-physical/head-UV/source-branch receipt; raster/material/native gates remain separate',
                  snapshot=str(snapshot.resolve()), incoming=str(incoming_path.resolve()), surface_sha256=digest,
                  metadata_sha256=sha(snapshot.with_suffix('.json')),
                  previous_sha256=previous['input_sha256'], surface_guards=target['guards'],
                  joined_source_files=expected_files, correspondence_snapshot=str(corr_copy.resolve()),
                  producer_proof_snapshot=str(proof_copy.resolve()), physical=physical,
                  source_branch_ownership=branches,
                  complete_head_triangles=len(old_head), complete_head_channels_exact=head_channels,
                  D3_neck_rows_exact=int(corr['old_neck_row_ids'].size),
                  strict_retained_vertices=len(oi), source_face_representations=len(corr['interpolated_old_vertex_id']),
                  complete_declared_outside_band_coverage=len(represented),
                  replaced_old_vertices=len(absent), old_representation_summary_verified=True,
                  UV_numeric_quality=target['uv_numeric_stats'],
                  previous_variants_changed=False, producer_files_changed=False, GPU_used=False,
                  limits=['No semantic ownership, rendered anatomy/joins, native assignment or appearance ART approval follows from this receipt.',
                          'Head source IDs/corner data are exact; actual native POINT reconstruction/active UV/material routes remain producer checks.',
                          'The 200 obsolete artificial forearm cut points are source-face representations only, not geometric-movement exemptions.'])
    write_json(out/(digest[:12]+'-expanded-receipt.json'), report)
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('previous')
    parser.add_argument('incoming')
    parser.add_argument('proof')
    parser.add_argument('destination')
    args=parser.parse_args()
    result=receive(args.previous,args.incoming,args.proof,args.destination)
    print({key:result[key] for key in ['status','surface_sha256','complete_head_triangles','D3_neck_rows_exact',
                                     'strict_retained_vertices','source_face_representations','complete_declared_outside_band_coverage',
                                     'replaced_old_vertices','UV_numeric_quality']})
