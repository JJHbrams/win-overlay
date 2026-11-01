# v29 medial-canthus geometry, lashes and facial surface

User request: correct actual medial-canthus modeling first, then source-based independent upper/lower lash meshes and active texture/diffuse/specular controls for makeup, dark circles, double-lid fold and facial shading. Separating source decoration from underlying anatomy does **not** authorize skipping the requested modeling.

Baseline: `../mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend`, SHA256 `f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2`. Preserve it. Body L, supported cheek, curved ocular seating and G2 inward lid return survive. Current baseline is a working checkpoint, not whole-character ART approval.

Read `asset/mia/AGENTS.md`, WORKING_PROTOCOL, CURRENT_STATE, REFERENCE_INDEX and REFERENCE_REVIEW_GATE after handoff. Source art is immutable. Crop plus uniform SRT only. Source black lash/eyeliner/makeup outlines are not literal skin-boundary targets. Covered anatomical positions remain inferred design choices, but anatomy continuity and visible opening constrain a real, bounded correction.

## Execution gates

1. Audit actual f0dead owners/material-output ancestry and correct medial skin/free-margin union/recess. Show clean real before/after front/oblique/profile and closure before appearance layers.
2. Add/refine separately owned upper/lower lashes and verify root contact, taper and thickness. Eyeliner, brow and makeup are different layers.
3. Author maps against the actual UV and connect them to working color, diffuse/shadow, specular and roughness routes. Pigment must remain distinct from light/cast shadow.
4. Fresh reopen, source4/critical/orbit/deformation review, independent criterion audit and canonical integration/commit/push.

## Acceptance contract

| ID | Criterion | User-visible outcome | Intended runtime | Verification and evidence | Critical |
|---|---|---|---|---|---|
| AC1 | Correct medial-canthus skin/free-margin geometry first | Rounded upper/lower union and medial recess with controlled tangents | Actual saved-native clean neutral front/profile/both obliques/low diagonal | Indexed actual patch/bounds, clean before/after and layer-separated source comparison; do not substitute eyeliner extension | Yes |
| AC2 | Preserve coordinated lid/wall/ocular deformation | No split corner, detached return, exposed carrier or failed closure | Bilateral0/.5/1, unilateralL/R, head-follow±12 |42-key/driver audit, evaluated contact and actual images; counts alone insufficient | Yes |
| AC3 | Independent upper/lower lash geometry | Source-informed taper/tufts/thickness following the lids | Neutral/half/full/unilateral, profile/low oblique | Ownership separated from ink/brow, actual isolates/root contact and closures | Yes |
| AC4 | Apply makeup/fatigue/fold/pigment/shading maps | Source-like appearance aligned to the surface, without painted geometry substitutes | Saved-native production/color-only/diffuse-only | Packed maps, actual UV/color-space/active-output ancestry, enabled/neutral-map render pairs and seam review | Yes |
| AC5 | Active diffuse/specular/roughness controls | Soft face light and restrained moving highlights | Fixed/moved-light renderer probes | Active branch/socket audit plus diffuse/spec isolates and roughness response; unused nodes/maps do not count | Yes |
| AC6 | Source-based final layer review without aspect distortion | Opening, lashes and paint each support the intended look | Front/profile/both obliques/high/low/diagonal/full orbit | Strict source4 boards plus geometry/color/production diagnostics and actual rotating sequence; pose/occlusion uncertainty recorded | Yes |
| AC7 | Preserve Body L and unrelated geometry | Useful torso/cheek/hair and bounded body behavior remain | Integrated saved native/live | Protected coordinates/UV/named weights/keys/owners, local topology remapping if used, minimal arm/head probes | Yes |
| AC8 | Reproducible independent acceptance | One native contains the reviewed geometry/lashes/materials | Fresh reopened final native | Packed dependencies, active outputs/render settings, strict validator plus independent ACCEPTANCE_AUDIT per AC | Yes |

Actual f0dead audit supersedes stale v18 lighting notes: face already uses scene-light Diffuse→ShaderToRGB→ramp multiplied by packed scene-linear2048 pigment→Emission. It has no active specular/roughness texture route. Preserve the working diffuse pipeline and matching head/neck/body routing; extend it rather than claiming an already-existing feature is new. Scalar control maps are Non-Color; the existing linear-pigment convention must be explicit.

Root owns canonical integration, state/docs, live MCP and Git. Eye/lash producer owns NEW `mia-eye-lash-v29` only in `mia-final-face-v12`, branch `codex/mia-eye-lash-v29`. Surface producer owns NEW `mia-face-surface-v29` only in `mia-reference-recovery`, branch `codex/mia-face-surface-v29`. Both inherit the main model/settings. They are not alone and may not revert others. A read-only plan is approved by root; independent acceptance must not be the implementer's self-report. Only one GPU batch runs at a time.
