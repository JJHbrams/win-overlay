# Static source-style finish — active contract

User request (2026-11-01): combine investigated production knowledge and finish the source-faithful model, including texture maps. This continues face/head/body/hair production. Garments and full event animation remain downstream of the relevant anatomy/static gates; this contract does not silently certify them.

Baseline: integration-wip-7-review/Mia_ReferenceFinish_v22.blend, SHA256 `9eab316b9a526eef99db33b8a552d58e7474305cf8377a5a43821711c1a1a140`. R28 face + Body14 + Hair0d are REVIEW ONLY. R19/WIP5/WIP6 surface acceptance stays revoked. Keep the original and rejected files. The R23 limited eye correction is separately retainable, not approval of all expressions.

Read `asset/mia/{AGENTS.md,WORKING_PROTOCOL.md,CURRENT_STATE.json,REFERENCE_INDEX.md,REFERENCE_REVIEW_GATE.md}`. Source matching is not replaced by model-before/after, hash validation, or a successful tool call. Source cameras and uncertainty remain fixed; uniform SRT only.

## Acceptance criteria

| ID | Criterion / user-visible outcome | Intended runtime | Verification / evidence | Critical |
|---|---|---|---|---|
| AC1 | High outer-cheek turn and short anterior cheek support keep the source character; no flattened or generically spherical cheek. | Actual Blender neutral model | Low-front and low ±30 targeted matte/wire, adjacent-angle guards, then source front/profile/both-oblique paired boards. | yes |
| AC2 | Connected nose/cheek/jaw planes and compact lower face; no orbital shelf, trench, needle chin, ear/neck seam or view-dependent collapse. | Same actual mesh across cameras | Matte/wire plus source4, unchanged camera/pose/light. Observe silhouette and internal planes separately. | yes |
| AC3 | Source tired eye aperture, iris/lash placement and stable limited blink. | Blender face deformation | Neutral/half/full blink in front/±30 and useful ±60 guards; source expressions, actual contact/visibility evidence. No all-expression claim. | yes |
| AC4 | Body Foundation proportions and continuous neck/thorax/bust/waist/pelvis/legs without attached-sphere rims. | Independent body mesh | Source front/profile/back/oblique plus useful low/high and torso/arm guard; actual wire/matte and source uncertainty. | yes |
| AC5 | Independent Pixal-derived hair preserves detail and source silhouette, repairs rear gathering and extraction boundaries, and avoids visible head/neck penetrations. | Static Blender hair layers prepared for later local rigging | Layer/owner inventory; front/profile/back/oblique source comparisons; targeted contact and hair-off checks. No final physics/rig claim. | yes |
| AC6 | UV and consumed pigment/shadow/reflectance channels visibly support source color, line and fatigue expression without masking geometry failures. | Actual connected Blender materials | UV checker/layout, close-up, color-only and final-look paired source views, light-direction probe, map/color-space/node-route inventory. A 4K file alone is not new detail; maps without a meaningful shader use are not required. | yes |

## Execution and ownership

- Face/head/eyes/cap above world Z1.46: existing face producer worktree, new finish-8 directory. Body: recovery/body-volume worktree, new body-finish-v23. Hair: head-hair-fit-v16 worktree, new hair-finish-v23. Root alone owns canonical integration, live MCP, state and Git publication.
- Start with actual visible target and linked 3D form. One targeted comparison plus neighbor guards first; expand to final source4/UV/deformation only for a useful candidate. Do not repeat low-gain smoothing or render-count inflation.
- Shape and early color tests may inform each other; makeup is not acceptance of a faulty silhouette. Preserve source natives while allowing documented local topology/UV/key transfer when needed.
- New final map bytes, UV paths and render results must be archived reproducibly. Generated paint plates are inputs, never actual model evidence. No private real-person reference, external uploads, or new monitoring automation.
- Independent visual review must explicitly say PASS/FAIL/UNVERIFIED per criterion. Source-review validator checks integrity only. Partial improvement can be checkpointed but is not completion.

## Starting state

Live MCP confirmed WIP7 path, dirty=false, Blender5.2.3/protocol15. Source front/left-oblique comparison boards directly inspected. Face is still too pointed/long below the mouth; hair extraction edges and low-detail paint remain apparent. Body14 attachment/UV defects remain open. No new candidate has passed this contract yet.
