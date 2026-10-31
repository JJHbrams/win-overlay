# Face6 continuous-surface diagnosis — read only

Source: `C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22/finish-6/continuous-candidate/Mia_FaceFinish6_v22.blend`

SHA256: `f5d17264e07f492983e7e075d5a3213b2bd14a4adaead82072899e9b3e15d98a`. The script verified the source hash after rendering. No native was saved. This diagnoses Face6, not the new Face7 r1 candidate, and is not an art approval.

## Actual visual finding

The cheek problem survives hair/paint/ink removal and is visible over continuous rotation, not just one registered front or profile. At elevation −10 and yaw ±15–45, the broad anterior cheek gathers abruptly toward the lower cheek and long jaw edge. At yaw 60–90 the lateral cheek remains a broad, shallowly changing wall. The lower-lid region turns into this wall over a short interval rather than distributing the change through the orbital rim, malar apex, buccal surface and jaw. A forehead/temple face-cap patch boundary is also visible in several elevations. It is a separate join issue; this report does not establish whether position, tangent, or both need correction there.

The two yaw contact sheets were visually inspected, as were the full-size low-front 0/30 matte and 30/60 cage-wire images. Fixed world lights mean opposite sides have different illumination; brightness differences alone are not evidence of asymmetric geometry.

## Measured support and limits

- Actual neutral cage: 728 vertices, 1,342 triangular polygons; armature followed by level-2 Catmull–Clark. The wire is the armature-evaluated control cage, not the subdivided tessellation. Some cage edges are occluded by the evaluated surface.
- Under-eye/upper-malar poles 56 and 249 have valence 8 at local approximately `(−.03831,.06124,1.52370)` and `(.03886,.06099,1.52374)`, with connected edges up to 13.64/13.72 mm. Outer-canthus/temple poles 43 and 232 have valence 8, with edges up to 22.16/22.37 mm. These fans bridge dense eyelid sampling and much sparser cheek/temple sampling. High valence alone is not proof of a defect, but the visible pinching/planar transition occurs in the same region.
- Evaluated vertical sections at local X ±35 mm retain nearly forward depth through much of Z 1.51–1.532, then turn back toward the lower rim at Z 1.532–1.534. Adjacent 1 mm samples rotate geometric triangle normals by approximately 16.7°/16.1° at that turn. These are triangulated geometric normals, not custom shading normals or a fitted smooth-curvature estimate. A lid necessarily turns; the measurement locates concentrated curvature, not a literal mesh discontinuity or an automatic failure threshold.
- X ±45/55 mm sections turn away progressively earlier/lower. The resulting cross-surface change is much more informative than one fixed frontal width. The plots exclude back-cap hits through eye apertures and connect skin hits only. Gaps at apertures are intentional missing skin, not cracks.
- The evaluated surfaces are connected within the sampled facial region. Calling this a topological break would be inaccurate. The actionable defect is the distribution of curvature and broad planes, amplified by irregular cage fans and the long lower jaw transition.
- Existing Face6 recipe protects the eye/oral boundaries plus two cage rings while applying an X-only lower-cheek field. This constrains the available transition: the fixed upper region and changed lower/lateral region must be joined by the remaining narrow band. This is a mechanism consistent with the observed shape, not a proof that Face6 created every inherited defect.

## Eye-depth relationship

The existing `MIA_V14_EyeSurface` is a static open curved carrier with separate sclera/iris regions, not a complete spherical eyeball/socket. The current matte diagnosis keeps its existing material while removing skin paint and lash/wing ink. It therefore exposes the shallow rim-to-eye interface without attributing the entire appearance to iris color. Moving the carrier can change sclera exposure and rim contact, but cannot change the measured skin cheek wall. Do not infer a new eye-depth correction solely from this diagnostic. Earlier aperture-width claim remains withdrawn; no blanket aperture/iris enlargement is supported here.

## Actionable correction guidance

Use one coordinated surface guide across lower rim → malar apex → buccal → jaw and laterally toward temple/preauricular skin. Redistribute tangents and curvature across the existing cage, rather than adding another small radial X taper or pushing one cheek peak forward. Do not freeze all surrounding rings if that forces the transition into a narrow band. Preserve source identity landmarks while evaluating the transition in intermediate angles, not only front/profile targets. If the existing irregular fans cannot express the guide without a ridge, report that local topology limitation instead of increasing subdivision indiscriminately. Any face/cap boundary correction needs both owners' matched evaluated positions/tangents and the established ownership mask; the present diagnosis does not authorize model edits.

Judge the correction in low-front 0/±30, neutral ±45/±60 and both profiles using the same matte rig. The expected improvement is a continuous cheek-to-jaw turn without a new bulge, rim pinch, eye clipping or longer planar jaw. Width reduction and a lower sampled normal angle are insufficient by themselves. Preserve source-based likeness comparisons as a separate gate.

## Evidence

- `continuous-positive-yaw.png`, `continuous-negative-yaw.png`: all 39 matte views (yaw 0, ±15/30/45/60/75/90; elevation −10/0/+10).
- `wire_yaw+30_elev-10.png`, `wire_yaw+60_elev+00.png`: decisive actual cage views; 16 wire renders are retained.
- `evaluated-vertical-sections.png`, `actual-sections-and-cage.json`: measured front-surface sections, geometric normals and full cage adjacency.
- `render-records.json`: 55 fresh render paths/hashes/camera matrices; orthographic scale .29, 700², roll 0, target Z 1.55. Frame 1 neutral, actual fixed root scene lights, Standard/None exposure 0 gamma 1. Skin/body replaced in memory with neutral diffuse material; hair and facial ink ribbons hidden. Native untouched.
- `inspect_continuous_surface.executed.py`: unchanged historical executed script. `inspect_continuous_surface.py` is the portable equivalent with optional `--source`, `--output-dir`, and `--validate-only`; the canonical archived native is its default source, and a new `rerun` directory is its default destination. Nonempty output directories are rejected. Rendering imports byte-identical frozen helpers from local `dependencies/`, using only `rig`/`constant` function definitions from `shape_evidence.py`; the helpers' unused historical source/reference constants are not used by this diagnostic. `compose_diagnosis.py` only arranges actual pixels and plots measured coordinates.
- `yaw-ping-pong-low.gif`, `yaw-ping-pong-level.gif`, `yaw-ping-pong-high.gif`: existing matte renders in labelled −90→90→−90 sequence at 15-degree samples, no interpolation. GIF palette quantization makes the lossless PNGs primary evidence. `delivery-manifest.json` records helper/source provenance and verifies all 55 original render hashes remain unchanged.

Portable command (choose a new empty output directory):

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python './inspect_continuous_surface.py' -- --output-dir './rerun'
```

Run from this package directory or use an absolute script path. `--source` can select another native for a separate diagnostic; it does not overwrite that native. `--validate-only` was tested successfully with the canonical archived Face6 and frozen helper files without rerendering the original evidence.

No geometry, UV, key, weight, native, producer recipe, live GUI, or Git changes were made. Findings and first images were sent directly to the correction producer before the full report.
