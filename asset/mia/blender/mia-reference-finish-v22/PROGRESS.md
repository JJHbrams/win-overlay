# Current v22 handoff — WIP5 / eye correction active

## Read first

Read `asset/mia/WORKING_PROTOCOL.md`, `CURRENT_STATE.json`, `REFERENCE_INDEX.md`, `REFERENCE_REVIEW_GATE.md` and `face-feedback-7/ACCEPTANCE.md`. This is active source-faithful modeling, not heartbeat research. First correct one continuous anatomical volume; source views are crosschecks, not independent silhouette targets. Geometry before new makeup; body/hair/garment/final-animation changes remain deferred during the active face feedback.

## Actual current state

Live/editor is `integration-wip-5/Mia_ReferenceFinish_v22.blend`, SHA256 `2e52b717f471f93b1d248ff70ac5f9dbadd1f32adc111a79062487d9d9452e8a`. Inputs Face7 R19 `5677073262e4` + unchanged Body14 `98f34b4362b4` + Hair0d `0d7874821981`. See WIP5 README and `independent-wip5-review.md`. Native is a local surface WIP, NOT finished character art.

R19 smooths the connected lower-orbit/malar/buccal surface and restores original ears after R18 introduced an ear-base notch. Independent review inspected low/level/high paired contact sheets and all four source views. No new blocker was found in that inspection. Low broad cheek turn, long jaw, source-eye style, UV/paint finish and full expressions remain FAIL/open.

Actual evidence:55 front-hemisphere matte/wire renders (yaw−90…+90, three elevations; not full360),9 paired boards,4 producer source comparisons,4 fresh WIP4|WIP5 integrated source face comparisons and5 actual MCP navigation captures. Same source registrations, camera/light/display and immutable native/source hashes. Unchanged body/hair retain earlier WIP4 review plus integration ownership guards; do not claim they received a new full art pass.

## Current producer / next action

Single geometry owner: `mia_surface_fit_astra`, producer `C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/finish-7/`. Root owns canonical integration/live MCP/Git. Do not restart old coder or create a competing geometry owner.

R21 is a separate52-vertex cheek trial from R19, NOT selected. Root replayed the declared semantic delta through actual MCP, verified exact candidate Basis and evaluated movement2.8755mm, captured four same-angle before/after views, then restored exact coordinates/keys/UV/material slots and native hash. Live is back to WIP5, dirtyfalse. Evidence `face-feedback-7/live-r21-delta-evaluated/`; reusable bounded replay `review_live_face_delta.py`. A valid edit/rollback is not proof of useful artistic gain.

R22 is an eye-only derivative from R19: coordinated upper-rim arc, skin support and four lash/wing owners; no carrier/iris scale/depth change. Independent actual-image review finds neutral arc/wing a local gain, but inherited Close0.5 overcloses and full source-eye identity is unfinished. Producer is correcting the blink target/followers. Next inspect actual neutral/partial/full closure and subtle expressions, then source4 before integrating any new candidate. No makeup yet.

## Avoid repeating rejected work

`face-feedback-7/TRIAL_LOG.md` records R1–R20. R15 was almost baseline-equivalent despite low fitting residuals; R17 introduced angular concave panels. R18 final-position fairness reduced these but changed ear vertices; R19 fixes that. R20 convex-target solve added little visible gain and is not selected. Do not resume general solver development before an actual target shape is visually useful. Use small semantic/cage edits, immediate actual views, source checks and rollback; expand the sweep only after a useful local stage.

Normal diagnosis excludes stale custom/sharp/WeightedNormal as the cheek problem. Valence8 or geometric-normal changes alone do not prove retopology is necessary.47 preserved keys do not prove deformation quality. Source eye-aperture129/133 vsmodel109/112 comparison was withdrawn (mixed lash endpoints/hair/bright opening); no global iris enlargement follows.

## Unchanged broader limits

Body14 still has lower/outer ovoid rims, lateral attachment, pelvis/groin/neck and UV distortion to refine. Hair0d uses limited512px/view paint, not full4K newly resolved detail. Hair3a8 folded-fin and d195 pinched-island repairs were rejected. Preserve separate body/head/hair/clothes owners. No final garments/rig/event animations until the relevant static/deformation gates.

Historical notes are in `PROGRESS-history-through-wip4.md`, `PROGRESS-history-through-wip3.md` and `PROGRESS-history-before-wip4.md`. Their live/pending status is historical; do not overwrite this state with it.
