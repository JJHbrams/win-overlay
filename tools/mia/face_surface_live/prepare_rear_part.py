"""Prepare explicit inherited rear-fin/loop face ownership and ONE rear assembly.

No Blender mutation. This is an unselected construction hypothesis for live
inspection, using the previously identity-verified intact exterior assembly.
"""
from pathlib import Path
import hashlib
import json
import math
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'.mia-cache/face-live/rear-part01'
SOURCE = ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-central-fill'


def main():
    assert not OUT.exists(), 'Never overwrite a recorded candidate'
    audit = np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz')
    q = audit['main_world']; faces = audit['main_triangles']
    donor = np.load(SOURCE/'identity-assembly.npz')
    donor_ids = donor['source_vertices']
    donor_faces = donor['source_faces']
    assert hashlib.sha256((SOURCE/'identity-assembly.npz').read_bytes()).hexdigest() == 'eebdf4084b1410199d74a99f621dc967c308263649294cae649dd50e2cc1e445'
    # Explicit central backing patch. Its artificial cut stays under the new
    # layered assembly; this is not called a naturally separated whole strand.
    cent = q[faces].mean(1)
    width = .060 + .012*np.clip((1.48-cent[:,2])/.14,0,1)
    fin = np.flatnonzero((abs(cent[:,0]) < width)&(cent[:,1] > .055)&
                         (cent[:,2] > 1.315)&(cent[:,2] < 1.535))
    old_loop = np.load(ROOT/'asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup/loop-mask.npz')['polygon_indices']
    hidden = np.union1d(fin, old_loop).astype(np.int32)
    # A full loose-side exterior assembly rotated into the rear. Its source
    # fibers, complete skins/backings and UVs remain intact; no stretched tips.
    a = math.radians(65)
    rotation = np.array([[math.cos(a),-math.sin(a),0],
                         [math.sin(a),math.cos(a),0],[0,0,1]],float)
    affine = np.diag([1.,.45,1.25]) @ rotation
    p = q[donor_ids].astype(float)
    transformed = p @ affine.T
    translation = np.array([-float(np.mean(transformed[:,0])),
                             .137-float(np.mean(transformed[:,1])),
                             1.535-float(transformed[:,2].max())])
    transformed += translation
    assert np.linalg.det(affine) > 0
    OUT.mkdir(parents=True)
    np.savez_compressed(OUT/'ownership.npz', donor_point_ids=donor_ids,
                        donor_face_ids=donor_faces, expected_donor_triangles=faces[donor_faces],
                        central_fin_faces=fin, inherited_loop_faces=old_loop,
                        hidden_faces=hidden, expected_hidden_triangles=faces[hidden],
                        candidate_world=transformed.astype(np.float32))
    report = dict(candidate='rear-part01', adopted=False, ART=False,
                  source_main_raw_sha256='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c',
                  donor_identity_proof=str(SOURCE/'identity-pixel-proof.json'),
                  donor_faces=len(donor_faces), donor_vertices=len(donor_ids),
                  hidden_faces=len(hidden), central_fin_patch_faces=len(fin), inherited_loop_faces=len(old_loop),
                  affine=affine.tolist(), translation=translation.tolist(),
                  transformed_bounds=[transformed.min(0).tolist(),transformed.max(0).tolist()],
                  coordinate_condition_number=float(np.linalg.cond(affine)),
                  raw_source_untouched=True, original_Main_to_be_hidden_not_modified=True,
                  representation='Separate intact exterior rear assembly; derived Main has explicit face deletion, original Main preserved.',
                  cut_limit='Fin region is an explicit geometric backing patch, not a claimed natural strand boundary. Need live selection review; hide cuts inside overlap only.',
                  visible_limits=['Live silhouette/root/depth/contact unverified.',
                                  'Affine compression can change silhouette and normals; identity proof does not accept fit.',
                                  'Source hair length/body ratio remains root-owned, not inferred from this recipe.',
                                  'No production weights, spring physics, texture finish or global hair ART acceptance.'])
    report['ownership_sha256'] = hashlib.sha256((OUT/'ownership.npz').read_bytes()).hexdigest()
    (OUT/'candidate.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__': main()
