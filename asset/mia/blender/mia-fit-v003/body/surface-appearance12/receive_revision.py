"""Receive a versioned collar-only surface revision without mutating producer data."""
from pathlib import Path
import argparse
import hashlib
import numpy as np
from surface_api import load_surface, read_json, write_json, sha


def receive(previous_npz, incoming_npz, destination, *, incoming_json=None):
    previous = load_surface(previous_npz)
    incoming = Path(incoming_npz).resolve()
    metadata = Path(incoming_json).resolve() if incoming_json else incoming.with_suffix('.json')
    # Read completed versioned data once. Source fingerprints are checked again
    # after copying so a producer's in-place change cannot silently mix revisions.
    npz_bytes, json_bytes = incoming.read_bytes(), metadata.read_bytes()
    digest = hashlib.sha256(npz_bytes).hexdigest()
    out = Path(destination).resolve()
    out.mkdir(parents=True, exist_ok=True)
    snapshot = out/(digest[:12]+'.npz')
    snapshot_json = snapshot.with_suffix('.json')
    if snapshot.exists() and sha(snapshot) != digest:
        raise ValueError('Snapshot name collision')
    snapshot.write_bytes(npz_bytes)
    snapshot_json.write_bytes(json_bytes)
    if sha(incoming) != digest or metadata.read_bytes() != json_bytes:
        raise ValueError('Incoming revision changed during receipt; do not bake this snapshot')
    target = load_surface(snapshot)
    for key in ['triangles', 'triangle_uv', 'face_region', 'meshfaceid']:
        if not np.array_equal(np.ascontiguousarray(previous[key]).view(np.uint8),
                              np.ascontiguousarray(target[key]).view(np.uint8)):
            raise ValueError('Collar-only revision changed protected '+key)
    if previous['world'].shape != target['world'].shape:
        raise ValueError('Collar-only revision changed world vertex count')
    if previous['meta']['source_context'] != target['meta']['source_context']:
        raise ValueError('Frozen source cameras/registration changed')
    collar_faces = np.isin(previous['face_region'], [12, 13, 14, 15])
    allowed = np.zeros(len(previous['world']), bool)
    allowed[np.unique(previous['triangles'][collar_faces])] = True
    # Endpoints shared with retained skin/core are protected. This independently
    # derives interior collar ownership from the actual unchanged triangle graph.
    allowed[np.unique(previous['triangles'][~collar_faces])] = False
    delta = target['world'].astype(float)-previous['world'].astype(float)
    changed = np.any(previous['world'].view(np.uint32) != target['world'].view(np.uint32), axis=1)
    forbidden = changed & ~allowed
    if forbidden.any():
        raise ValueError('Revision moved retained core/head/lower or collar endpoint vertices: '+repr(np.flatnonzero(forbidden).tolist()))
    per_collar = {}
    for label in [12, 13, 14, 15]:
        ids = np.unique(previous['triangles'][previous['face_region']==label])
        selected = ids[changed[ids]]
        per_collar[str(label)] = dict(changed_vertices=len(selected),
                                     max_delta_m=float(np.linalg.norm(delta[selected], axis=1).max()) if len(selected) else 0.)
    receipt = dict(status='PASS independent collar-only receipt; geometry/appearance ART not implied',
                   previous_snapshot=str(Path(previous_npz).resolve()), previous_sha256=sha(previous_npz),
                   incoming=str(incoming), incoming_sha256=digest,
                   metadata_sha256=hashlib.sha256(json_bytes).hexdigest(), snapshot=str(snapshot),
                   previous_guards=previous['guards'], current_guards=target['guards'],
                   changed_vertices=int(changed.sum()), changed_vertex_ids=np.flatnonzero(changed).tolist(),
                   allowed_interior_collar_vertices=int(allowed.sum()), forbidden_changed_vertices=0,
                   topology_UV_semantics_meshfaceid_held=True, source_camera_registration_held=True,
                   collar_endpoint_and_retained_vertices_held=True, per_collar=per_collar,
                   max_delta_m=float(np.linalg.norm(delta[changed], axis=1).max()) if changed.any() else 0.,
                   previous_maps_status='maps-B is pre-collar-revision fitting evidence; do not install on the new target',
                   producer_files_changed=False)
    write_json(out/(digest[:12]+'-receipt.json'), receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('previous_npz')
    parser.add_argument('incoming_npz')
    parser.add_argument('destination')
    parser.add_argument('--incoming-json')
    args = parser.parse_args()
    result = receive(args.previous_npz, args.incoming_npz, args.destination, incoming_json=args.incoming_json)
    print({key: value for key, value in result.items() if key != 'changed_vertex_ids'})
