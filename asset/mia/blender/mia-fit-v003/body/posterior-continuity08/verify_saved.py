"""Saved evidence integrity; geometry remains an actual appearance FAIL."""
from pathlib import Path
import ast,hashlib,json,re
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8'))
build=read(P/'build-report.json');cpu=read(P/'CPU-audit.json');prep=read(P/'render-preparation.json');rows=read(P/'actual8/render-records.json');boards=read(P/'review-records.json')
assert len(rows)==8 and len({(r['mode'],r['view']) for r in rows})==8
assert len(list((P/'actual8').glob('*.png')))==8 and prep['render_called'] is False
assert sha(P/'posterior08.npz')==build['candidate_sha256']==cpu['candidate_sha256']
data=np.load(P/'posterior08.npz');vh=hashlib.sha256(data['world'].tobytes()).hexdigest()
for r in rows:
    assert sha(r['path'])==r['sha256'] and Image.open(r['path']).size==(640,640)
    assert sha(r['baseline_E_render']['path'])==r['baseline_E_render']['sha256']
    assert r['payload_sha256']==build['candidate_sha256']
    assert r['actual_private_vertex_sha256']==r['actual_evaluated_private_vertex_sha256']==vh
    assert r['renderer_sha256']==sha(P/'render_actual8.py') and r['head_scale_changed'] is False and r['native_saved'] is False
    assert r['original47_and_Face690_exact'] and r['entire_evaluated_original_context_exact']
    assert r['camera']['clip_end']==10 and r['camera']['resolution']==[640,640]
for b in boards['boards']:
    assert sha(b['board'])==b['board_sha256']
    if 'source' in b:assert sha(b['source']['path'])==b['source']['sha256'] and Image.open(b['source']['path']).size==tuple(b['source']['original_size'])
protected=read(P/'protected-input-hashes.json')
for path,h in protected.items():assert sha(path)==h,path
assert not list(P.rglob('*.blend')) and not list(P.rglob('*.blend1'))
log=(P/'actual8.log').read_text(encoding='utf-8');assert 'POSTERIOR08_ACTUAL8_DONE_GPU_RELEASE' in log
assert not re.search(r'traceback|compile error|shader.*failed|error:',log,re.I)
for script in P.glob('*.py'):ast.parse(script.read_text(encoding='utf-8'),filename=str(script))
report=dict(status='PASS_saved_evidence_integrity_ONLY',actual_frames=8,extra_frames=0,boards=len(boards['boards']),
    candidate_and_actual_vertex_hashes_match=True,original47_Face690_context_pose_preserved=True,protected_input_files=len(protected),
    native_saved=False,GPU_used_by_this_check=False,FORM='FAIL producer actual: new bead/dimple above posterior V; unselected',
    lower_opening_limit='Y0 reference open; posteriorY.020/Z1.260 old8.8755mm interval closes, explicitly not all openings held',
    full_body_ART='UNVERIFIED; no production or animation promotion')
(P/'saved-evidence-check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,indent=2))
