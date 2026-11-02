"""Consolidate actual cleanup receipts and link reviewed R2 without an ART PASS."""
from pathlib import Path
import argparse,hashlib,json,shutil
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--cleanup-only',action='store_true');a=ap.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
first=json.loads((P/'storage/cleanup-result.json').read_text())
last=json.loads((P/'storage/body-six-native-retirement.json').read_text())
removed=first['files']+last['deleted_files']
extra_path=P/'storage/post-R3b-native-retirement.json'
extra=json.loads(extra_path.read_text(encoding='utf-8-sig')) if extra_path.exists() else None
if extra:removed+=extra['deleted_files']
assert len(removed)==(343 if extra else 341) and all(not Path(r['path']).exists() for r in removed)
protected=[
 P.parent/'mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend',
 P/'integrated/Mia_v0.0.2_Review_R2.blend',
 Path('C:/Users/antio/.codex/worktrees/mia-v002-body/win-overlay/asset/mia/blender/mia-body-underwear-v002/support-G/Mia_BodyUnderwear_v002_G.blend'),
 Path('D:/ai/Mia3DWork/model-v02/hair-surface-stage/Mia_HairSurface_v06.blend')]
expected=['4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a','eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82','e199c01b4c0a8fbc7942d5b667f8cdd0e1827d766d98cf28c99bd27ab12cf0da','9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6']
if extra:
 protected.append(P/'integrated/Mia_v0.0.2_Review_R3b.blend')
 expected.append('4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1')
checks=[]
for file,digest in zip(protected,expected):
 assert sha(file)==digest,str(file)
 checks.append(dict(path=str(file),sha256=digest))
report=dict(status='COMPLETE',deleted_count=len(removed),deleted_bytes=int(first['deleted_bytes']+last['deleted_bytes']+(extra['deleted_bytes'] if extra else 0)),
    removed_paths_rechecked_absent=True,protected_current_hashes=checks,c_free_now_bytes=shutil.disk_usage('C:/').free,
    scope='Exact superseded untracked full-scene/backups only; original art, v001, current native, portable deltas/maps/proofs and Git history retained. No claim that all historical first-cleanup candidates remain current.',
    receipts=['cleanup-result.json','body-six-native-retirement.json']+(['post-R3b-native-retirement.json'] if extra else []))
(P/'storage/cleanup-consolidated.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if a.cleanup_only:
 print('CLEANUP_ONLY_RECORDED',report['deleted_count'],report['deleted_bytes'],report['c_free_now_bytes']);raise SystemExit(0)
statefile=P.parent.parent/'CURRENT_STATE.json';state=json.loads(statefile.read_text())
assert state['in_progress_v002'].get('current_integrated_review',{}).get('sha256') in [None,expected[1]],'Archived R2 state writer cannot replace a later selected working review; use --cleanup-only.'
state['in_progress_v002']['current_integrated_review']=dict(path='blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R2.blend',sha256=expected[1],
    fresh_data='blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R2.fresh-reopen.json',
    actual_review='blender/mia-refinement-v002/review/integrated-R2-eed4/verification-completion.json',
    source_review='blender/mia-refinement-v002/review/integrated-R2-eed4/paired-source/reference-review.json',
    meaning='Current reviewed integration WIP,97 actual frames; D2/G/MN+L/O/P/C clean palette. Bounded improvements only; overall ART remains open.')
state['in_progress_v002']['next_corrections']=['EyeA surprise and small-mouth dental display','Brow final support after EyeA, strict neutral15pixels<=1LSB retained','HairR cleaner Side_Nape base','Existing smile8/16 calibration','Provisional source-roll calibration requires actual16 review','CrownS hybrid UV+authored missing-pigment candidate, not adopted']
state['in_progress_v002']['storage_cleanup']='blender/mia-refinement-v002/storage/cleanup-consolidated.json'
state['art_approved']=state['character_complete']=False
statefile.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
print('CLEANUP_CURRENT_R2_RECORDED',report['deleted_count'],report['deleted_bytes'],report['c_free_now_bytes'])
