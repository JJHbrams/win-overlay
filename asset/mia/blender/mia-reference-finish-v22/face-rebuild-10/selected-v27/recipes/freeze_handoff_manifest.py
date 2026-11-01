from pathlib import Path
import hashlib,json
O=Path(__file__).parent
folders=['face-shared-final','final-source-frozen','final-diagnostics-frozen','final-rig-body-proof-matched','replay-package','replay-verification-final']
scripts=['HANDOFF.md','build_shared_head.py','shared-boundary-map.json','finish_shared_integration.py','seat_shared_head-final.py','final_eye_proportions_r2.py','refine_ribbon_r3.py','paint_actual_uv_r3.py','render_diagnostics_frozen.py','render_rig_body_proof.py','audit_shared_correspondence-final.py','inspect_join_weights-final.py','audit_frozen_package.py','export_replay_package.py','freeze_handoff_manifest.py']
files={O/p for p in scripts}
for folder in folders:
 for p in (O/folder).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts or p.suffix in {'.pyc','.blend1'}:continue
  if p.suffix=='.blend' and p not in {O/'face-shared-final/Mia_Foundation_v27.blend',O/'replay-package/face-owners.blend'}:continue
  files.add(p)
records=[{'path':p.relative_to(O).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
native=next(r for r in records if r['path']=='face-shared-final/Mia_Foundation_v27.blend');assert native['sha256']=='e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4'
(O/'FROZEN_EVIDENCE_SHA256.json').write_text(json.dumps({'native_sha256':native['sha256'],'files':records,'excluded':'Failed/intermediate natives, duplicate replay natives, .blend1 backups, unselected review variants. Manifest itself excluded from its own hash list.'},indent=2));print('FROZEN_FILES',len(records))
