"""Freeze the user's v0.0.1 baseline without re-saving the packed Blender asset."""
from pathlib import Path
import hashlib, json

P = Path(__file__).resolve().parent
M = P.parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda p, value: p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
native = M / 'blender/mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend'
expected = '4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a'
assert sha(native) == expected
sp = M / 'CURRENT_STATE.json'
state = json.loads(sp.read_text(encoding='utf-8'))
assert state['active_working_correction']['sha256'] == expected
assert not state.get('in_progress_v002'), 'Phase start is single-use; do not overwrite later production state'

criteria = []
def ac(id, criterion, outcome, runtime, verification, evidence):
    criteria.append(dict(id=id, criterion=criterion, user_visible_outcome=outcome,
                         intended_runtime=runtime, verification=verification, evidence=evidence, critical=True))
ac('BASELINE', 'Freeze exact packed457 as v0.0.1; preserve all source and rejection history; version is not ART approval.',
   'The same prior model can be reopened and compared or restored.', 'Blender5.2.3 and Git',
   'Native SHA, existing packed dependency audit and a7d0170 Git tag; no duplicate/re-save.', 'versions/v0.0.1/manifest.json and mia/v0.0.1')
ac('FACE_MAPS', 'Source-specific fatigue, makeup, eyelid crease, nose and lip surface with meaningful reflection/roughness.',
   'Mia has the source tired impression rather than a generic red band or nose sticker.', 'Actual Blender toon shader, normal512 and closeup',
   'Source4, baseline/candidate, color-only, feature toggles and fixed/moved light; actual active UV/map ancestry; no geometry substitution.',
   'Exact packed native, portable material delta, imagegen provenance, reference-review.json, independently inspected PNGs')
ac('FACE_IDENTITY', 'Preserve and refine continuous orbit/cheek/chin, true red eye opening and iris; do not make cheeks gaunt.',
   'Identity and volume remain coherent from front, profile, both obliques, high/low and orbit.', 'Blender geometry and toon renders',
   'Actual geometry isolates plus source4 and orbit; no eye-chin normalization counted as proportion success.', 'Per-view named residuals and actual evaluated-surface evidence')
ac('BROWS_LASHES', 'Retain independent upper/lower lashes and source brows, tested Ewall returns and ClosedB; address named residuals.',
   'No gap, buried lash or broken brow in the tested expressions; source-like visible strokes.', 'Blender neutral/bilateral/unilateral/grazing512',
   'Half/full and unilateral intermediate poses, source neutral and closeups; no arbitrary lower enlargement.', 'Actual pose images, root/contact checks, source judgments')
ac('SUPPORTED_BODY', 'Anatomical thorax distinct from breast soft volume, fitted support from charcoal bra, underwear-textured base.',
   'Supported breast shape belongs to the ribcage, and bra/briefs follow actual anatomy.', 'Actual Blender evaluated body/shader',
   'Current baseline and candidate fullheight original-aspect source4 plus high/low/orbit, core-only/core+soft/supported sections and bounded arms; generated v06 limits stated.',
   'Current-native source package, explicit fit hypothesis, intersection/UV/material evidence and independent actual-render inspection')
ac('BODY_ANATOMY', 'Continuous neck/shoulder/axilla/abdomen/pelvis/limbs and missing anatomy corrected before final clothing.',
   'No inherited root fold or broken silhouette is concealed by paint or a garment.', 'Blender neutral and relevant bounded poses',
   'Named defect inventory, evaluated nonadjacent intersections and visual fullbody/torso/arm checks.', 'Before/after source and geometry images, exact changes and remaining untested poses')
ac('HAIR', 'Source-faithful bangs/waves/braid/gathered bun, roots/ear/nape/tips; purposeful UV/normals and connected fine dark paint.',
   'Detailed hair retains volume and source identity from all sides without broken clumps or transferred face scraps.', 'Blender source4/back/orbit512 and closeup',
   'Preserve adopted1216-fragment cleanup and realforelocks; separate shape/color/normals/light causes; binding and neck/shoulder contacts where changed.',
   'Portable guarded delta, actual source package, map provenance and named defect closure')
ac('EXPRESSIONS_16', 'Use all16 confirmed art panels to build source impressions and missing facial anatomy on stable topology/UV.',
   'Source expressions combine eye/lid/brow/mouth controls with appropriate gaze/head poses.', 'Blender facial deformation and head follow',
   'Panel-to-control inventory, endpoints/intermediates/combinations; distinguish hand gesture/gaze/pose from pure facial morph; actual mouth/eyes/lashes checked.',
   '16 actual panel comparisons, pose definitions, missing-model corrections, clipping and continuity evidence')
ac('INTEGRATION', 'One exact packed native integrates selected deltas, matching default/live/source review and protected owners.',
   'The file opened by the user is the model actually reviewed.', 'Fresh Blender reopen and live MCP',
   'Guard actual geometry/UV/keys/weights/materials/maps/cameras/lights, run source-review validator and independent visual audit.', 'Final native hash, exact source/live evidence and criterion audit')
ac('RETAINED_DOWNSTREAM', 'Existing independent garments, final rig, limited secondary motion, event mapping, loops/common idle/30fps remain required behind stage gates.',
   'Current refinement does not silently erase the intended animated Mia.', 'Future Blender sprite bake and overlay runtime',
   'No promotion based on static/key/hash tests. Preserve later clip transitions, idle calibration, preroll/cache/bake/loop and runtime acceptance.',
   'Prior contracts retained; current static phase must explicitly report downstream unresolved')
write(P/'ACCEPTANCE.json', dict(schema_version=1, phase='v0.0.2 refinement', request_date='2026-11-02',
      acceptance_criteria=criteria, scope_deltas=[], art_approved=False))

sources = []
for rel in ['references/received/mia-face-reaffirmed-20261031.png', 'references/mia-expression-style-confirmed-20261031.png',
            'references/mia-clean-master-v22.png', 'references/body-foundation/anchors/mia-body-front-user-selected-20261031.png',
            'references/body-foundation/v06/mia-body-turnaround-v06.png']:
    f=M/rel; sources.append(dict(path=rel, sha256=sha(f)))
version = M/'versions/v0.0.1'; version.mkdir(parents=True, exist_ok=True)
write(version/'manifest.json', dict(version='0.0.1', kind='user-named working baseline',
      commit='a7d0170a955f3e38cb7f1bf3b0a269dee10a5586', tag='mia/v0.0.1',
      native=dict(path=str(native.relative_to(M)).replace('\\','/'), sha256=expected),
      source_references=sources, art_approved=False, character_complete=False,
      prior_scoped_review='blender/mia-visible-art-v30/FINAL_SCOPED_REVIEW.md',
      source_package='blender/mia-visible-art-v30/reviews/v31-brows-lashes-source4/paired/reference-review.json',
      limitations='Version freezes the existing reviewed component WIP. Face identity/maps, hair, body, final expressions and downstream animation remain open.'))
state['updated']='2026-11-02'
state['status']='v002_refinement_active_v001_frozen_overall_art_open'
state['version_baseline']='versions/v0.0.1/manifest.json'
state['in_progress_v002']=dict(status='active', contract='blender/mia-refinement-v002/ACCEPTANCE.json',
    baseline_native=state['active_working_correction']['path'], baseline_sha256=expected,
    baseline_version='0.0.1', baseline_tag='mia/v0.0.1', art_approved=False,
    owners=dict(root='codex/mia-v002-refinement', face='codex/mia-v002-face', body='codex/mia-v002-body', hair='codex/mia-v002-hair'),
    latest_findings=['Current body has no active bra/brief material; BodyL was bounded unapproved nude inference.',
      'Inherited bilateral axillary crossings discovered beyond old Z1.340 test limit; repair pending.',
      'Face paint A is a single imagegen candidate; actual source/light renders pending, not accepted.'],
    required_order='Face surface comparison; parallel bounded body/hair audits and fixes; expression design inventory now, final expression production after relevant topology/UV stability; exact integration/review.',
    body_target='Fixed anatomical thorax with coherent breast soft mass and source charcoal underwear support/fit; texture alone cannot fake support.',
    source_registration='Original aspect, uniformSRT only. Front frozenIPD and zeroextraRoll; oldnonfront normalized proportions/roll excluded.',
    downstream='Independent garments/finalphysics/events/commonidle/30fps remain pending behind static/deformation gates.')
state['character_complete']=False; state['art_approved']=False
state['immediate_next']=['Read v002 acceptance and exact v0.0.1 manifest after compaction; do not rerun archived v31 recorders.',
    'Inspect actual face paint A source4/color/toggle/light evidence before selecting; preserve fixed baseline.',
    'Repair and visually review supported body and inherited axillary fold with intactaspect fullheight references.',
    'Refine current cleaned hair by guarded portable deltas; preserve source detail and diagnose normals/UV separately.',
    'Build16expression panel/control inventory and actual missing anatomy; implement after dependent topology/UV stabilizes.',
    'Integrate only selected deltas and freshreopen/source/live/independent review; commit+push meaningful checkpoints without overallARTclaim.']
write(sp,state)
print('V002_PHASE_RECORDED', expected)
