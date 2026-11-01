"""Preserve technical history while recording the user's explicit appearance rejection."""
from pathlib import Path
import json

P=Path(__file__).resolve().parent
path=P.parents[1]/'CURRENT_STATE.json'
d=json.loads(path.read_text(encoding='utf-8-sig'))
d['status']='v30_source_appearance_reopened_work_in_progress'
d['character_complete']=False
d['art_approved']=False
d['active_contract']='blender/mia-visible-art-v30/ACCEPTANCE.md'
d['active_progress']='blender/mia-visible-art-v30/PROGRESS.md'
d['in_progress_v30']={'baseline_native':d['active_working_correction']['path'],
 'baseline_sha256':'d7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be',
 'user_annotation':'references/received/mia-eye-lash-user-markup-20261102.png',
 'user_annotation_sha256':'3dd3d4bcbf3539e7ed40c9517b63485bb3a244c62f23e59d7cdbeebf4e3e0974',
 'status':'All source-look criteria reopened. Actual assets exist, but v29 projected canthus/lashes/pigment contributions were too small/generic and retained wrong visible geometry/decoration. User rejects current appearance.',
 'critical_remaining':['Source red opening and actual medial/upper/lower geometry','Source-scale iris/eye/face identity without misleading normalization','Source green independent lash silhouette at512preview','Crisp source-specific makeup/fatigue/fold/nose pigment and toon planes','Dark fine hair shape/strand/root-ear-nape-bun-tip finishing','Continuous volume and deformation while preserving healthy cheek/BodyL','Actual integrated source-look audit with no named face/hair residual waived'],
 'front_registration_correction':'Source camera already has about6.6degree roll; old2D +5.314degree SRT flattened model against still-tilted source. Newfront displayrotation0 and IPDscalar/translation; do not warp anatomy to old wrong display.',
 'scope':'Face/head/eyes/lashes and face/hair source-look completion. Garments/final animation remain behind existing anatomy gate.'}
d['in_progress_v29']['status']='Technical/anti-regression checkpoint retained; USER REJECTS source appearance. Its bounded PASS is not completion evidence for current v30 source-look contract.'
d['active_working_correction']['meaning']='Retained C rollback baseline only; current appearance rejected by user. Active v30 production must resolve source-visible eye/lash/paint/hair residuals.'
d['current_face_candidate']['status']='C preserved as rejected-appearance rollback baseline; no v30 final candidate accepted yet.'
d['current_surface_wip']['selection_means']=d['active_working_correction']['meaning']
d['stage_status']['face_head_art']='FAIL source appearance by user. V29 canthus projection~1.6px, subpixel lowerlashes/old dominantink and weak genericpaint do not meet source red/green shapes. V30 source-look gates reopened; technical preservation evidence retained.'
d['stage_status']['hair_art']='FAIL source appearance: coarse washedout72percent ash fallback/disablededgeink, limitedrebakedpaintcoverage and root/ear/nape/bun/tip finishing remain. V30 hair producer working; no appearance PASS.'
d['latest_user_feedback']['v30_continue_until_resolved']='미결과제 해결될때까지 진행하고 이번 작업은 최종비교안에 눈머리 그대로고, 속눈썹 메시도 없고, 텍스쳐맵도 적용이 안된거같은데 뭘보고한거지?'
d['latest_user_feedback']['v30_user_annotation']='원화에서 내가 빨갛게 처리한부분이 실제 눈매, 초록색이 속눈썹이야. 수정안의 주황색라인/노란색 라인과 비교하고, 화장도 다름을 고칠 것.'
d['immediate_next']=['Read v30 contract/progress and user annotation; all critical source-look criteria remain open.',
 'Freeze corrected source framing and separate red opening/green lash targets; remove double-roll comparison error before source fitting.',
 'Implement substantial coordinated source-contour geometry, source-sized independent lashes and iris/face articulation without losing continuous orbital/cheek volume.',
 'Apply source-specific crisp makeup/fatigue/fold/nose graphics and finish dark fine hair geometry/UV/material details; default512visual result is required, not just map connectivity.',
 'Integrate one immutable native, actual source4/high-low/orbit/deformation/live review and fresh appearance audit. Continue while any named face/hair residual remains unresolved.']
path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('USER_SOURCE_APPEARANCE_REJECTION_AND_V30_CONTRACT_RECORDED')
