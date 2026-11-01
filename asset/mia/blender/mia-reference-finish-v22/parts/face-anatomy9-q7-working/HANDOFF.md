# Connected surface handoff — partial gain, no art approval

Preferred producer candidate: `Mia_ConnectedLoft_Q7_SurfaceFit.blend` (hash in surfacefit-q7-audit.json). Parent/root must decide integration. Current live WIP8 and all immutable natives were untouched.

Q7 is P2 proportion plus a dense-surface correction. The corrected surface reduces anterior cheek ripples without the new lower-cheek ledge of the failed explicit loft. It does NOT complete source likeness. Front cheek-to-jaw angular transition, inner-nose/mouth-side vertical grooves, profile mouth/chin wedge, eyelid identity and makeup remain open. No eye-shape or material edits were added here.

## Exact reproduction

1. `build_dense_q6b.py` reads immutable P2. Disable Armature temporarily, bake only Subsurf separately for all 47 keys into the identical 16,338-vertex evaluated topology, restore Armature, retain UVMap and interpolated groups, retarget four lash follower driver IDs. New shape keys are explicitly set to zero. This script contains the failed Q6b loft; `check_bake.py` subtracts its recorded dense-q6b-deltas.npz exactly to save `Mia_Q6b_BakeOnly_Control.blend`.
2. `build_surfacefit_q7.py` reads bake-only control, fits a robust cubic anterior-sheet target to actual surface samples, applies normal/anatomical transition masks, and writes identical per-vertex deltas into all 47 keys. `surfacefit-q7-deltas.npz` contains basis and exact delta, suitable for root's reviewed combination with eye work on the same bake-only topology. Max displacement 1.381241 mm.
3. `render_matte_motion.py --source ... --output-dir ...` creates actual neutral front/profile/bilateral oblique, low 0/+30/-30, half/full blink 0/+30/-30, subtle sorrow 0/+25. Camera is ORTHO. Native four-view comparison uses canonical render_face_comparison.py and compose_integrated_review.py, output `review-q7`.

## Evidence and limits

`bake-equivalence.json`: source P2 versus unchanged bake-only, neutral/half/full/actual head-bone local-Y +15/-15 degrees. Maximum vertex error 0.000596 mm; UV error exactly zero. `matte-bakeonly` and `matte-p2-baseline` provide actual render pairs. This is a limited pose test, not final rig approval.

`q7-technical-audit.json`: all key names retained; identical per-key correction residual 0.000003726 mm; UV/topology/group names unchanged relative to bake-only; coordinates of all 165 other meshes unchanged. The skin topology is dense relative to P2, so legacy cage indices must not be used.

`review-q7/face/reference-review.json`: source/WIP8/Q7 actual paired four-view records with hashes and frozen uniform SRT. These legacy normalization transforms cannot independently validate the dimensions used to establish normalization. See root eye-spacing-normalized proportion evidence separately. `matte-q7` contains 15 actual geometry/motion renders. Full blink front visually closes without obvious white-eye leak; unrestricted expression/rig acceptance remains open.

## Rejected/alternate trials

Q1/Q2/Q3: cage-target lofts; Q2 limited support gain but residual ripple. Q3 wider mask did not resolve it.
Q4/Q5: inverse subdivision fitting; lower numeric target error did not imply good form. Q4 introduced severe ridges, Q5 insufficient.
Q6: invalid save because newly created keys defaulted to value 1; all-expression explosion. Explicitly rejected. Q6b fixed execution, but its arbitrary loft produced lower/lateral ledges and up to 19.5 mm displacement; rejected art.
Q7: preferred partial result above.
Q8: boundary-tangent-constrained alternative, `Mia_ConnectedSurface_Q8_BoundaryFair.blend`. Projected cotangent bi-Laplacian minimum bending with two fixed collars and six front-volume anchors; 2328 patch vertices, 1536 free, max 2.217 mm. `matte-q8` shows no new ledge but retains more original diagonal than Q7. Not selected by producer. Exact solve/apply scripts and delta NPZ are preserved.

The decisive limitation is still whole shape construction: local surface continuity can improve while face outline, nose-mouth-chin relation and eye identity remain wrong. Neither successful baking, a smooth target, numeric residual nor evidence-valid package establishes art acceptance.
