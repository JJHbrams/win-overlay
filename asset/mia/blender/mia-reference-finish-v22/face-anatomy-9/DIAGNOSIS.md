# Structural diagnosis before editing

Current baseline is WIP8, not an approved anatomy base. User asked to study face construction before more patches. Actual live MCP inspection confirmed WIP8 is open and clean. No new candidate is selected.

## Observed, not inferred anatomy measurements

- F2 bare matte front and both obliques retain a narrow bright anterior plane beside the nose and a strong diagonal plane break below the orbit. The problem persists without makeup; pigment alone is not a sufficient explanation.
- Low oblique makes the diagonal ridge and the broad recessed/flat neighboring cheek read as separate shapes. The lower-cheek fill did not resolve the upper connection.
- Source front/profile/oblique suggest a simpler, softer connected middle face, with deliberate stylized eye and jaw proportions. Hair, drawn yaw and normalization prevent treating these boards as exact measurements.
- Fresh read-only reviewer independently observed the narrow central anterior plane, separation from mouth mass, and diagonal orbital/cheek transition. This is a visual diagnosis, not proof of a specific bone dimension.

## Previous method and testable hypothesis

`build_shape_f2.py` moved Y on a lower-face patch using height-dependent convex sections. Its upper influence faded out between Z1.520 and1.531, while explicit protected IDs remained fixed. That can leave the upper transition intact even after restoring central volume. The IDs' anatomical roles must be established from actual geometry; they must not be relabelled as the eyelid boundary without checking.

Hypothesis: a narrow, poorly connected orbital/malar/maxillary transition sits above a recently filled buccal patch. A broad Gaussian bump, global smoothing or a newly named anatomical mask cannot validate a remedy. Inspect actual cage, evaluated surface and neighborhoods first. Preserve lower-lid contact separately from arbitrary high-malar control-point coordinates.

## Grounding

- Uldis Zarins, Anatomy for Sculptors, [Forming the Head: Simple to Complex](https://anatomy4sculptors.com/blog/forming-the-head-simple-to-complex/): public text inspected 2026-11-01. Distinguishes large head/face masses, primary transitions, and secondary undereye/cheek/chin forms. Its average proportions are not Mia's design target.
- Marco Bucci, [Planes and lighting demonstration](https://www.proko.com/lesson/painting-the-head-from-imagination-lighting-without-reference-with-marco-bucci): public lesson text inspected 2026-11-01, no video timestamps. Orbital planes lead into upper/front/side cheek planes, then jaw; mouth projects as its own related form. Light tests diagnose those orientations. This painting source does not prescribe Blender topology.

Neither video was watched in full. Course marketing and the failed Scott Eaton PDF fetch are not implementation evidence. Full source/approach notes are in Wiki `mia-reference-mcp-review`, heading `얼굴 큰형태 재조형 근거 — 2026-11-01`.

## Next concrete probe

Map the actual eyelid aperture, its adjacent rings, malar support and mouth/side-face boundaries. Check whether the suspected diagonal is a sharp geometric change, a bad protected junction, or insufficient carrier topology. Only then construct one primary connected midface correction and evaluate bare rotation before expanding to native materials and source-matched views. Keep all failed hypotheses and the original WIP8.

## Independent structural consultation

A one-time read-only sage inspected the actual matte front/low oblique and the former method. It recommends a separate low-density target surface for the whole middle face, not another lower-cheek bump. Form a broad anterior cheek, an outer malar turn and a gradual side-cheek recession; redistribute over-prominent ridge and deficient adjoining support together. The need for wholesale topology replacement is unproven. Local retopology is justified only if the current cage cannot express an actually reviewed target or topology pinching is demonstrated.

Confidence is medium: the observed form failure is clear; the contribution of fixed cage points versus topology must still be tested. This consultation is a design hypothesis, not art acceptance.

Producer A1 was rejected before selection: it used standalone F2 rather than the required integrated WIP8 and repeated a broad bump with inherited protected IDs. Its old source is preserved; it is not an improved current model.

## Whole-face trials after the user's proportion correction

The earlier exact jaw/eye-position locks were wrong for this request. The source's eye-to-chin-normalized board also conceals the very short-face dimension being judged. `eye-spacing-p2.png` instead displays unretouched source and actual raw renders using only pupil-distance scale, translation and roll. Approximate source eye-to-chin/IPD is 1.10 versus baseline 1.03; these manual points are not precise modeling prescriptions. Hair, pose and perspective remain uncertain.

- P1 lowered the mouth together with the chin and overshot. Not selected.
- P2 keeps the mouth closer to its former height and extends the lower face. The short V is partly eased, but the independent review still finds a heavy/flat lower face and poor cheek-to-jaw continuity. It is only a working trial.
- P3 changes the actual eye aperture neighborhood and eye/lash owners locally. Its name includes `midface`, but its own manifest confirms the middle face was unchanged. Root and independent review of the actual bare matte show diagonal ridges, small creases and a separate mouth/chin mass. It is not a resolved face.

Actual roots `eye-midface-p3/motion/` contain matte views; there is no `candidate/motion/` directory. Full blink was not demonstrated by the first P3 probe set. Recipe/manifest/small image evidence is archived in `unselected-v25`; the original natives are preserved in the producer worktree. No trial has replaced WIP8.

The earlier Workbench mask artifacts came from a wrong front-camera axis: skin local +Y is anterior, but its Z-180 world transform makes world -Y anterior. They are invalid viewpoints. Hidden archived-head overlap was an initial hypothesis and is withdrawn.

## Surface versus pigment

The prior `face-feedback-7/normal-diagnosis/FINDINGS.md` isolates earlier Face6/R8 normals and finds the diagonal on the unchanged surface even with ordinary diffuse shading and freshly recomputed normals. That is earlier-model evidence, not a new WIP8 measurement, but it rejects normal recalculation as the established fix. The old cage fans bridge dense eye loops to sparse cheek triangles; topology valence alone is not proof of failure.

The material worker directly inspected WIP8 packed pixels and consumed links: FatigueMask and FineLineMask are present. The missing visual hierarchy is a broad fatigue mass plus a separately readable lower fold/outer line, rather than merely making a uniform narrow band darker. Geometry and material trials stay separate until each is actually inspected.

## Retraction: P2 did not preserve the actual mouth anchor

The P2 producer's intent and the root's earlier explanation said the mouth was kept in place. The actual neutral mouth-boundary comparison contradicts that: WIP8 mean local Z is 1.494905576m, and Q7 (which inherits P2) is 3.999964mm lower on average. All identified rim vertices moved about -4mm. Eye boundary Z stayed unchanged. The height threshold was not the actual mouth boundary, and the root initially accepted the intended behavior rather than verifying the achieved anchor.

This is an implementation/verification error, not an artistic choice. Root explicitly corrected the user-facing statement. Q9 is to restore the actual mouth height with its surrounding muzzle/corners, preserve the useful chin extension, and inspect the resulting facial proportions in all source views. The warm-pigment span comparison suggests a wider visible middle cheek, but hair/shadow/neck contamination prevents treating it as an exact anatomical-width target.

## Connected surface and eye-curve observations

Q1–Q6b did not provide an acceptable face: control-cage fitting reduced a numeric residual while amplifying creases; a direct loft made a new boundary ledge. The original Q6 additionally had all new shape keys at value1 and is an invalid exploded-state test, not evidence of neutral form. Q6b corrected that error.

The bake-only control was compared to original P2 in neutral, half/full blink and local head yaw +/-15 degrees; evaluated positional differences stayed below .001mm and UV error was zero. This validates only those tested states, not a final rig. Q7 then edits the dense actual surface with a broad cubic fit; root and independent review find less fragmented front-cheek curvature without the Q6b ledge. Nose/mouth/chin and full source likeness remain unresolved. The portable replay and exact coordinate/UV/weight/driver/evaluated hashes are archived under `../parts/face-anatomy9-q7-working`.

E2 changes actual upper/lower aperture arcs rather than translating the same curved line or scaling the whole eye. Root and independent review find a clearer tired neutral gaze, with no new visible white leak in the inspected half/full blink. Outer wing thickness, lower-lid integration and whole likeness are still unresolved. It is a local eye improvement, not final face acceptance.
