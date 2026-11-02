"""Checkpoint actual current candidates without promoting the selected live model."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;statefile=P.parents[1]/'CURRENT_STATE.json'
s=json.loads(statefile.read_text(encoding='utf-8'));v=s['in_progress_v002']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v.setdefault('superseded_cleanup_candidates',v['current_candidates'])
v['current_candidates']={
 'face_D2':dict(replay='blender/mia-refinement-v002/parts/face-D2/portable_face_delta.py',producer_native_sha256='8b150df1eac3144aa496f5b57fea125c390eb19daa102fcd25f2afcdc44b1657',meaning='Independent source4 observes smoother muted fatigue; source lip bright edge/nose accents remain incomplete.',art_approved=False),
 'body_G':dict(replay='blender/mia-refinement-v002/parts/body-G/replay_current_scene.py',producer_native_sha256='e199c01b4c0a8fbc7942d5b667f8cdd0e1827d766d98cf28c99bd27ab12cf0da',meaning='109actual frames; independent source/gray continuity improvement; valid19poses0 continuous-skin crossings, mechanical straight-arm-20 invalid1055. Inferior attachment crease and extremity finish remain explicit.',art_approved=False),
 'hair_MN':dict(replay='blender/mia-refinement-v002/parts/hair-MN/apply_bundle_M.py',manifest_sha256=sha(P/'parts/hair-MN/bundle/manifest.json'),meaning='Bounded source pigment/root/tip improvement. Optional L binding needs actual integrated pose review. Crown O bounded shape correction in progress; jagged nape/source ink hierarchy remains open.',art_approved=False),
 'mouth_C':dict(replay='blender/mia-refinement-v002/parts/mouth-C/portable_mouth_delta.py',payload_sha256=sha(P/'parts/mouth-C/payload/mouth-rig-C.npz'),meaning='Closed crown arches and continuous collar; source grin/closure actual proof under review. Installs sparse43rd key on original42 baseline without old-scene replay.',art_approved=False),
 'source_controls_gaze':dict(replay='blender/mia-refinement-v002/expressions/expression_control_delta.py',meaning='16source-intent presets plus verified head axes and bounded surface-projected iris motion. CPU controls pass; actual integrated16 poses/gaze/head contacts remain required.',art_approved=False)}
v['latest_findings']=[x['meaning'] for x in v['current_candidates'].values()]
v['integration_preflight']='MouthC→BodyG→HairMN(L)→FaceD2→source controls/gaze completed owner/original-array/scene guards without a native save. Exact review file and fresh actual/source/live checks still required.'
v['gpu_coordination']='One local GPU batch at a time, root-owned queue. Latest producer mouth8 completed; root integrated suite next after stable crown/lip handoff. Check root/agent latest message before rendering.'
statefile.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CURRENT_CANDIDATES_RECORDED_NO_MODEL_PROMOTION')
