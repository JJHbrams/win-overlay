"""Saved-artifact integrity only. Does not turn rejected geometry into ART PASS."""
from pathlib import Path
import ast, hashlib, json
from PIL import Image
P=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads((P/p).read_text())
checked=[]
def artifact(path,digest):
    path=Path(path); assert path.is_file(),str(path)
    assert sha(path)==digest,('stale hash',str(path)); checked.append(str(path))
b=read('actual-B-front4/records.json'); c=read('actual-C-views5/records.json')
assert len(b)==4 and len(c)==5
assert len(list((P/'actual-B-front4').glob('baseline-*.png')))==2
assert len(list((P/'actual-C-views5').glob('baseline-*.png')))==2
assert not (P/'actual-C-views5/baseline-front-hairON.png').exists()
assert b[0]['composition']==c[0]['composition']
for row in b+c:
    artifact(row['path'],row['sha256']); artifact(P/'apply_candidate.py',row['helper_sha256'])
    assert row['camera']['clip_start']>.09 and row['camera']['clip_end']==10
    assert row['camera']['resolution']==[512,512] and row['camera']['pixel_aspect']==[1,1]
    assert row['provisional_brow_overlay'] is False and row['native_saved'] is False
    assert Image.open(row['path']).size==(512,512)
    if row['fringe_payload_sha256']:
        artifact(P/('fringe-'+row['variant']+'.npz'),row['fringe_payload_sha256'])
for row in c:
    artifact(row['runtime_driver']['path'],row['runtime_driver']['sha256'])
    artifact(P/'render_front4.py',row['runtime_driver']['base_renderer_sha256'])
for path in ['actual-B-front4/source-paired-front.json','actual-C-views5/source-paired-C.json']:
    rows=read(path)
    for row in rows:
        artifact(row['board'],row['sha256']); artifact(row['reference']['path'],row['reference']['sha256'])
        assert row['baseline']['camera']==row['candidate']['camera']
        reg=row.get('source_registration',row.get('reference_registration'))
        assert isinstance(reg['uniform_scale'],(int,float)) and reg['uniform_scale']>0
        assert len(reg['translation_xy'])==2 and isinstance(reg['rotation_degrees'],(int,float))
        assert not any(k in reg for k in ('scale_x','scale_y','warp'))
guard=read('CPU-components-guard.json'); assert guard['status']=='PASS'
artifact(P/'apply_components.py',guard['implementation_sha256'])
artifact(P/'brow-contract.json',guard['contract_sha256'])
for variant in ['B','C']:
    cfg=read('candidate-'+variant+'.json'); artifact(P/('fringe-'+variant+'.npz'),cfg['payload_sha256'])
    report=read('CPU-guard-'+variant+'.json'); assert report['status']=='PASS'
    assert report['actual_reversed_Main_triangles']==0 and report['native_unchanged']
assert not list(P.rglob('*.blend')) and not list(P.rglob('*.blend1'))
for f in P.rglob('*.py'):ast.parse(f.read_text(encoding='utf-8'),filename=str(f))
report={'status':'PASS_saved_artifact_integrity_only','actual_B_frames':len(b),'actual_C_frames':len(c),
    'B_front_baseline_reused':True,'all_recorded_helper_payload_driver_image_source_hashes_match':True,
    'same_camera_fixture_pose_display_and_uniform_source_registration':True,'artifact_checks':len(checked),
    'API_guard':'fresh CPU PASS; equivalent actual evaluated arrays, active unknown keys held',
    'full_head_reference_gate':'UNVERIFIED: missing right_oblique C / nonfront isolated brow / actual pose / candidate native',
    'brow':'bounded provisional thickness improvement','B_fringe':'FAIL rejected','C_fringe':'FAIL unselected',
    'native_in_checkpoint':False,'GPU_used_by_this_check':False}
(P/'checkpoint-integrity.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,indent=2))
