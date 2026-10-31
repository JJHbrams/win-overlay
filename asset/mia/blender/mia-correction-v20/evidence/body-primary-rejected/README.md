# Primary breast form rebuild — REJECTED / NOT SELECTED

**Final decision: corrected candidate is REJECTED, including WIP integration. Keep existing body8e262 in the canonical integration.** Independent shape review, relayed by root, found a broad upper shelf and lower crescent seam in front, pinched lower attachment in profile, and isolated outer egg/uneven axilla flow in three-quarter. The upper ramp and rounder profile are local progress, but overall reference fit did not improve. The mirror bug is fixed; that technical result is not a shape PASS. No further sculpt in this bounded attempt.

Review `corrected-candidate/review/close_front.png`, `close_profile.png`, and `close_three_quarter.png` first. The corrected form has a longer upper transition and a rounder weighted lower pole than the source and the rejected conical first attempt. The dense central patch artifact is repaired. A strong outer attachment/vertical shadow and some independent mass reading remain, so this is not an art PASS or an instruction to integrate.

## Frozen outputs

Corrected native: `corrected-candidate/Mia_BodyPrimary_v21_corrected.blend`
SHA256: `e174330f0aaf0fae769175baed3f1305c9ed313f03f3f99444a9fb34af9d70ac`
Exact recipe: `repair_primary_mapping_curvature.py`
Source: canonical `mia-correction-v20/integrated/Mia_Corrected_v20.blend`
Source SHA256: `aa02b736452bc876abf6f81a09b94bad71eb15c5ced35834b6fde17b90f8b5a6`

`candidate/Mia_BodyPrimary_v21_candidate.blend`, SHA `bd1292321160d250397bd4f30502e6b2c8b5f01bc6d8bf8060cf35c9df9f166f`, is rejected and retained unchanged. It contains the mirror-mapping defect and conical primary form. Earlier sibling v21 and r2 candidates are also immutable and are not reselected by this work.

## Reference and form interpretation

Directly viewed the user-selected front (`references/body-foundation/anchors/mia-body-front-user-selected-20261031.png`) and v06 body turnaround front/profile. The selected front sets a fuller lower chest silhouette; the profile guides the long upper plane and supported lower volume. These are illustrated, clothed, noncalibrated views. Bra support/edge conceal the skin root and underfold. Arm abduction, pelvis tilt, camera perspective, and uncertain illustrated three-quarter yaw prevent exact anatomical measurements. The v06 sheet is a generated candidate, not approved bare anatomy. No illustrated clothing seam was copied as a skin groove.

The whole existing breast control net was rebuilt, including the previously locked principal row and center. Sixteen actual radial spokes across eight rows and the dense center patch were mapped explicitly. Upper chest rows extend the transition toward the clavicle/pectoral region; lower mass shifts downward. This is a continuous-body candidate; no permanent body hole, separate breast exchange system, clothing morph or mask implementation was created. Existing topology/UV/weights were sufficient for this candidate and remain unchanged.

## Failure and bounded repair

The first primary attempt was rejected because the apex-to-first-row depth retreated too quickly, producing a conical profile. It also revealed a technical mirror bug: nearest matching around world X0 assigned three left central-patch IDs more than once. The actual symmetry plane is slightly offset. Coarse spoke adjacency alone did not detect this dense-patch error.

The authorized repair derives the observed symmetry plane from well-separated source ring pairs, requires one-to-one targets, and verifies every owned internal edge on the opposite side, including the central patch. `mirror-mapping-verification.json` records old collisions, new IDs and every checked edge. The corrected native has no repeated mirror target. This repair was applied from the immutable aa02 source, not destructively on the rejected native.

For the form correction, the central vertical depth slope is flattened at the forward peak. The lower-sector depth curves retain rounded quarter-ellipse curvature before returning locally to the fold. Upper chest endpoints remain those of the primary attempt. The dense patch is reconstructed with a compatible tangent plane and quadratic residual to its actual boundary. No global smoothing or Gaussian offset field is used. The post-repair actual close profile visibly has a round lower pole; the independent remaining side-root issue is not hidden by the technical fix.

## Evidence and protection

- `corrected-candidate/primary-control-map.json`: source/target row positions, observed mirror plane, all ring/spoke IDs, dense-patch IDs, per-sector depth controls and mirror mapping. The stored Hermite controls describe the upper/base curve; `lower_curve` and the exact recipe specify the lower-sector quarter-ellipse blend.
- `corrected-candidate/vertex-delta.json`: all308 changed body vertex IDs with source coordinates and local/world deltas.
- `corrected-sections-and-cage.png`: actual source vs corrected evaluated sagittal section and cage layout; unchanged pelvis section shown as a control. No inferred anatomy target or image warp.
- `corrected-candidate/sections.json`: actual control/evaluated triangle intersections.
- `corrected-candidate/protected-owner-audit.json`: independently reopened source/final comparison. Topology, UV, weights, groups, modifiers, protected body Z>=1.46, other mesh control/evaluated geometry, object transforms, pose, material content and packed images remain exact. All source material/image datablocks retained; explicitly authorized fake-user lifetime flags are recorded separately.
- Source before close views: unchanged `../../mia-body-surface-v20-r2/before/close_*.png`.
- `candidate/review/`: actual rejected initial primary views, including 4 whole-body views. They must not be presented as corrected-candidate views.

Corrected final review is the requested three close views only: 1024 square, ortho0.70,targetZ1.12,yaw0/90/45, zero elevation, frame1, unchanged saved pose, canonical neutral diffuse diagnostic rig and camera-relative lights. All conditions are in `corrected-candidate/review/review-evidence.json`. Diagnostic shader/light changes were never saved in the native. `frozen-artifacts.json` records final hashes and source immutability.

The artist construction principle previously checked is the public Lesson Notes of Stan Prokopenko's official [Form & Motion lesson](https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/); no new research, premium access, private human reference, image generation or paint occurred in this bounded repair. Anatomical form follows artist interpretation of the existing character reference, not a fixed numerical template.
