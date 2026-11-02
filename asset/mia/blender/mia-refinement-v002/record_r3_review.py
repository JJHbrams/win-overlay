"""Record completed bounded R3 evidence; never grant whole-character ART approval."""
from pathlib import Path
import argparse,hashlib,json,shutil
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--native',required=True);ap.add_argument('--sha256',required=True);ap.add_argument('--tag',required=True);a=ap.parse_args()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
native=Path(a.native).resolve()
digest=a.sha256
assert sha(native)==digest
review=P/'review'/a.tag
done=json.loads((review/'verification-completion.json').read_text())
fresh=json.loads(native.with_suffix('.fresh-reopen.json').read_text())
valid=json.loads((review/'paired-source/evidence-validation.json').read_text())
assert done['sha256']==digest and done['actual_frames']==101
assert fresh['technical_preservation_pass'] and not fresh['errors']
assert valid['evidence_valid'] and valid['art_acceptance']=='NOT_EVALUATED'
assert len(json.loads((review/'expression-panels/panels.json').read_text())['panels'])==16
live=json.loads((review/'live/live-review.json').read_text())
assert live['native_sha256']==digest and live['preset_total_range']['max']==16.
assert (P/'INDEPENDENT_R3B_REVIEW.md').exists()
statefile=P.parents[1]/'CURRENT_STATE.json';state=json.loads(statefile.read_text())
v=state['in_progress_v002']
if v.get('current_integrated_review',{}).get('sha256')!=digest:
    v['previous_integrated_review_R2']=v['current_integrated_review']
rel=lambda f:'blender/mia-refinement-v002/'+f.relative_to(P).as_posix()
current=dict(path=rel(native),sha256=digest,
    fresh_data=rel(native.with_suffix('.fresh-reopen.json')),
    actual_review=rel(review/'verification-completion.json'),
    source_review=rel(review/'paired-source/reference-review.json'),
    live_review=rel(review/'live/live-review.json'),
    independent_review='blender/mia-refinement-v002/INDEPENDENT_R3B_REVIEW.md',
    meaning='Bounded working integration only, not completed Mia. Six post-R2 corrections including aggregate-preset range fix,101actual frames with4mix/intermediate cases, fresh full authored-data/UI-bound fingerprint. CrownS excluded; old6hairUVs retained.')
v['current_integrated_review']=current
v['next_corrections']=[
 'Source facial nose bridge/tip graphic and lower-lip edge; D2 fatigue improvement does not complete source makeup/line hierarchy.',
 'Source eye/brow/upper-crease hierarchy and broader continuous identity remain open; calibrated nonfront proportions not proved.',
 'Supported-body inferior return/upper-pole-to-thorax transition, shoulder/clavicle and extremities remain open. No clothing promotion.',
 'Crown/nape coarse/folded/scuffed hair and source-coherent fine ink; rejected CrownS positiveUV had substantial anisotropy and bunched paint.',
 'Source07 hand gesture, arbitrary expression/head contacts, final garments/secondary motion/events/commonidle/loops/30fps bake remain gated.']
v['latest_findings']=v['next_corrections']
v['integration_preflight']='R3b saved and fresh-reopened with matching shared fingerprint helper. Actual original drivers preserved except declared Fun and HeadZ recipe changes; new keys/POINT/brow modifiers and aggregate UImax16 observed, all source scenes protected during component replay. Prior855d failed mixed-preset test; retained as a superseded trial, not selected.'
v['held_crown_S']='blender/mia-refinement-v002/art/crown-S/ROOT_REVIEW.md'
state['active_working_correction']={**current,'meaning':'R3b current WIP; exact prior457 remains frozen v0.0.1. Source/overall ART and final animation remain open.'}
state['selected_static_wip']=dict(path=current['path'],sha256=digest,selection_means='Current working review only; no whole source ART or animation approval.')
state['diagnostics']['current_live_evidence']=current['live_review']
state['diagnostics']['current_live_viewing_setup']=current['path']
state['stage_status']['face_head_art']='UNAPPROVED overall. BoundedEyeA/browcontact/closedsmile corrections; nose/lipgraphic and global source hierarchy remain open.'
state['stage_status']['body_art']='UNAPPROVED overall. G supported-body/lowerbody improvement inherited without R3body changes. Inferiorhook/upperpole transition, shoulder/clavicle and hands/feet remain open.'
state['stage_status']['hair_art']='UNAPPROVED overall. MN+L/O/P/R bounded improvement. S newUV/generatedfill held and not in R3; source fineink and crown/nape geometry/surface remain open.'
state['art_approved']=state['character_complete']=False
statefile.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=dict(native=str(native),sha256=digest,actual_frames=101,evidence_valid=True,art_approved=False,
    selected_for_working_review=True,not_a_finished_character=True,current_c_free_bytes=shutil.disk_usage('C:/').free,
    retained_v001_sha256='4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a',
    unselected_crown_S='art/crown-S/ROOT_REVIEW.md',remaining=v['next_corrections'])
(P/'R3B_WORKING_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('R3B_WORKING_REVIEW_RECORDED_NO_ART_PROMOTION',digest)
