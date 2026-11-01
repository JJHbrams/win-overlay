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
