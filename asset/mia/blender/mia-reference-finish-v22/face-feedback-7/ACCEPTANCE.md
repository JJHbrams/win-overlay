# Cheek–jaw and eye identity correction

User feedback: 볼-턱선이랑 눈매가 좀많이 다른데. WIP4 is not an accepted likeness. Its Face6 narrowed the lower cheek but protected the actual eyelid boundaries; that pass did not correct the eye shape.

Follow-up: basic eye contour and cheek/jaw outline must be corrected before adding makeup textures. Front, both obliques and profile are mandatory, not oblique-only. Compare neutral/matte geometry separately from existing pigment; no new makeup is credited as a shape correction. Existing pigment is retained for controlled before/after material views, not edited to conceal geometric mismatch.

Surface-continuity steering: user observes an abrupt malar/cheek bulge above the jaw from slightly low front and shallow-looking eyes/unnatural zygoma–cheek transitions in oblique. Do not fit isolated view silhouettes by alternating local tweaks. First inspect hair-off matte/wire surfaces through continuously sampled yaw at below-eye, eye-level and above-eye elevation. Treat orbit→zygoma→malar/buccal→jaw as one coherent volume, with a compatible eye carrier and face/headcap boundary. Source views constrain that volume afterward. Eye depth alone is not an established cause.

Immutable current integrated baseline: ../integration-wip-4/Mia_ReferenceFinish_v22.blend, SHA7377542702efb4b65b11011ad2bfee1321ef765730d834e518b042c4e2c02cee. Face producer baseline: f5d17264e07f492983e7e075d5a3213b2bd14a4adaead82072899e9b3e15d98a. Keep Body14 and Hair0d, except explicit face-owned headcap continuity. No garments/final rig work.

Independent planner actually inspected confirmed portrait/expression sheet, all four WIP4 face boards and three production cameras. Source visible cheek turn is higher and the subsequent jaw segment concise and directional; current WIP retains low broad cheek mass and a long uniform V read. Source upper lid/lash is articulated across the iris and tapers into a directional outer wing. Current eye reads as a comparatively level band with blunt termination. Do not smooth away intentional source straight jaw segments or lower the whole lid into a slit.

| ID | Critical user-visible outcome | Runtime and verification | Evidence |
|---|---|---|---|
| AC-FACE-01 | Source-like cheek turn, concise diagonal jaw segment and compact chin, visibly more than slight band narrowing | Neutral front and production camera, source/current/candidate, inspect contour and matte geometry separately | Actual front board, matte view, fixed camera/registration |
| AC-FACE-02 | Coherent both-oblique cheek/jaw volume; no new ledge, hollow, far-side collapse or headcap gap | Both oblique actual source-paired and matte views; hair-covered portions uncertain | Both boards, scope/native hash, seam review |
| AC-FACE-03 | Controlled chin/lower-lip/jaw profile without front-only deformation | Actual profile source/current/candidate; do not invent occluded depth | Profile board and uncertainty |
| AC-EYE-04 | Articulated upper-lid arc and thin directional lash wing with appropriate iris/sclera overlap | Front/both-oblique closeups in toon and neutral geometry; linked lid/orbit/lash rather than global eye scale | Actual eye boards, owner/geometry/material route |
| AC-EYE-05 | New lid/lash/iris relation survives minimal facial movement without intersections, detached roots or missing far eye | Neutral, half-blink and selected subtle-angle expression; active evaluated keys recorded | Actual captures and independent audit |
| AC-SURFACE-06 | Continuous orbit–zygoma–cheek–jaw surface through intermediate and low-front views, without a sudden cheek ledge or shallow floating eye appearance | Hair-off matte and wire, sampled full yaw turntable at low/level/high elevation; inspect underlying cage and actual evaluated surface | Turntable/contact sheet, camera records, topology/curvature diagnosis and actual independent visual review |

All six criteria are critical. Evidence validity is not art approval. No global head scaling, iris enlargement or whole-eye narrowing based on the withdrawn source129/133 vsmodel109/112 measurements. Eye-to-chin normalization cannot validate that normalized distance. Source pupil slope/gaze/roll differs; judge local lid relationships in their own eye frame, not raw image-horizontal angle.

Execution: one face producer edits a new candidate; root owns integration/live Blender. Cheek/jaw volume is checked across views before eye changes. Eye edits coordinate skin rim, orbital transition, carrier contact and lash Basis/follower. Existing47key names/deltas alone do not certify valid expressions. Source files remain immutable; preserve failed candidates.

Required delivery: source|WIP baseline|candidate front/profile/both oblique, relevant expression panel, neutral/color-only/UV diagnostics, exact recipe, ownership/below-cap protection, reference-review package and validator result. Fresh independent actual-image review must judge these IDs before root promotion. If any critical criterion remains FAIL/UNVERIFIED, report partial and preserve the missing work explicitly.
