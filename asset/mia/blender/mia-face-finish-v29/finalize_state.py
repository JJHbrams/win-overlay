"""Record the reviewed local checkpoint without granting overall Mia ART approval."""
from pathlib import Path
import hashlib
import json

P = Path(__file__).resolve().parent
mia = P.parents[1]
rel = 'blender/mia-face-finish-v29/surface-C/native/Mia_FaceFinish_v29_C.blend'
expected = 'd7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be'
assert hashlib.sha256((mia/rel).read_bytes()).hexdigest() == expected
assert json.loads((P/'final-review/source-boards/validation.json').read_text())['evidence_valid']
assert (P/'ACCEPTANCE_FINAL.md').exists()
path = mia/'CURRENT_STATE.json'
d = json.loads(path.read_text(encoding='utf-8-sig'))
d['status'] = 'v29_local_eye_lash_surface_checkpoint_overall_art_unapproved'
d['character_complete'] = False
d['art_approved'] = False
local = d['in_progress_v29']
local['status'] = 'Bounded AC1..8 supported by fresh independent actual review. Real canthus correction, separate G lashes, reversible legacy-card mask and applied C facial surface. Overall character likeness/garments/animation remain unapproved.'
local['surface'] = 'Applied C: original scene-lit diffuse retained; masked1254sRGB cosmetic art,2048Non-Color float controls, active actual-light specular and roughness.32 controlled probes and fresh source/critical/orbit/live reviewed. No4K detail or physical-energy-conservation claim.'
local['final_native'] = rel
local['final_native_sha256'] = expected
local['acceptance'] = 'blender/mia-face-finish-v29/ACCEPTANCE_FINAL.md'
local['source_review'] = 'blender/mia-face-finish-v29/final-review/source-boards/reference-review.json'
local['remaining_art'] = ['Global iris/lid/under-eye articulation and graphic nose accents differ from source.',
    'Coarse inherited hair strands/extraction/texture artifacts remain.',
    'Overall body surfaces/garments/final event and physics animation are not approved.']
checkpoint = {'path': rel, 'sha256': expected,
    'meaning': 'Current bounded canthus/lash/facial-surface working checkpoint; not full-character ART completion.',
    'face_review': local['source_review'],
    'body_review': 'blender/mia-orbit-thorax-review-v28/reviews/G2L-body/reference-review.json'}
d['active_working_correction'] = checkpoint
d['current_surface_wip'] = {'path': rel, 'sha256': expected, 'selection_means': checkpoint['meaning']}
d['current_face_candidate'] = {'path': rel, 'sha256': expected, 'selection_means': checkpoint['meaning'],
    'status': 'Local v29 contract supported; global source likeness remains open. Preserve G2L/C2/G stages, source correspondence, healthy cheek and exact BodyL.'}
d['diagnostics']['current_live_viewing_setup'] = rel
d['diagnostics']['v29_live_review'] = 'blender/mia-face-finish-v29/final-review/live-review.json'
d['stage_status']['face_head_art'] = 'Overall ART UNAPPROVED. Bounded v29 canthus/lash/surface contract supported by actual source4/critical/orbit/closure/light review. Residual iris/lid/under-eye graphic articulation, nose accents and inherited coarse hair differ from source; no full identity pass.'
d['stage_status']['uv_and_color'] = local['surface']
d['stage_status']['facial_deformation'] = 'G independent upper/lower lashes:42 endpoint controls and sampled quarter/half/three-quarter lower-tuft interpolation volumes positive; actual bilateral/unilateral closure and headfollow reviewed. All expression combinations, loops/events and physics remain unvalidated.'
d['immediate_next'] = ['Read v29 ACCEPTANCE_FINAL and FINAL_REVIEW plus current native SHA before changes.',
    'Preserve source-aspect/camera/light/pose review pipeline and accepted local canthus/lash/map structure; E float/F inversion/B lip-wipe are rejected paths.',
    'Next art refinement must address documented global iris/lid/under-eye/nose graphic residuals and inherited hair limitations using the corresponding source views. Do not reset accepted anatomy or use cosmetics to hide geometry.',
    'Whole body/garments and final event/30fps/physics approval remain separate; no automatic stage promotion.']
path.write_text(json.dumps(d, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print('V29_LOCAL_CHECKPOINT_RECORDED_OVERALL_ART_UNAPPROVED')
