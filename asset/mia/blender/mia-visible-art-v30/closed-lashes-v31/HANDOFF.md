# Closed-lash B — bounded full-closure cleanup

Independent actual-image review and the parent support B for the full-closure
hanging-sheet/outer-hook defect. This is not whole-lash, AC6, source-face or
character ART acceptance. Half closure still has a broad/abrupt grazing strip;
the full-front line is fine, its temporal endpoint and inherited U-root curve
are not calibrated from the nearly closed source02. Keep these limits open.

## Exact files and portable replay

- Candidate `Mia_LashPose_v31_B.blend`, SHA256
  `0dde1b1cf6da83ff6dea627890ab6d03342e0a968e762afe1d0986b3c89c188f`.
- Tested child output `Mia_LashPose_v31_B_IntegratedCleanHair.blend`, SHA256
  `d9a72995e3624ef6946f01e5ea699ea059760f367189aeec34de21a77abdd712`.
- Immutable replay input is the parent's CleanHair native, SHA256
  `9dd072af38d52130aa693c561545b2b70b98f22c3b69145fc2b7211cd1632505`.
- Baseline before cleanup: canonical `Mia_SourceLook_v31_Review.blend`, SHA256
  `c3557e9eaa2163ae0d6f712a8c51362c0a6abdab628bcabe3e9673511323813c`.

Use the four files below together in one folder:

| File | SHA256 |
|---|---|
| `replay_closed_delta.py` | `ea282179a943425446ab920d7deff53184df780e1ae7dea41f9f4361c6587424` |
| `audit_mesh_helpers.py` | `be7e0facb00f493c9aaa9de34c5baaeea0e8cc142d79b62c12b1126ce01ab5f0` |
| `closed-B-delta.json` | `a5abe53d78194b6c20f1224583c18c3dc9c03b8e539239d2157ce60eea4a6b04` |
| `closed-B-delta.npz` | `c3fb32e01552bcdacaac134bc43522a412ef85d9265bf3404a16333f1706430b` |

Command:

```text
Blender --background --python-exit-code 2 --python replay_closed_delta.py -- INPUT.blend OUTPUT.blend B
```

The helper writes exactly FOUR existing shape-key coordinate arrays:

- `V30_UpperLashes_-1`: bilateral `EYE_Close` and `EYE_Close_R`.
- `V30_UpperLashes_1`: bilateral `EYE_Close` and `EYE_Close_L`.

No new key, driver, material, UV, topology, weight, modifier, raw mesh/Basis or
neutral coordinate is introduced. Original42 upper keys remain. The helper
refuses changed upper baseline coordinates/data and changed protected skin,
master, E inner-wall/ocular geometry. Input material slots may differ and stay
exact input. Current hair cleanup is allowed because it is preserved, not
copied from the older standalone scene.

`Mia_LashPose_v31_B_IntegratedCleanHair.closed-B-replay.json` records ALL checks
true: every non-upper input mesh record, every upper non-coordinate field,
exact selected delta, all input material graphs/maps/images, scene/camera/
light/world/pose settings and unchanged input native. No canonical/live change
or commit occurred in this child.

## Cause and construction

The existing closed pose transports the temporal free wing using the short
rounded canthus tangent. The neutral outward extension folds medially and
roughly8–9mm anterior in the closed frame; one side also rises about6mm.
The result is both an upright front hook and a broad profile/grazing crescent.
This was lash geometry, not the repaired E wall/globe seam.

A remapped only the outer stations. Actual10-image review confirmed shorter
sideways tips but retained the broad central U-shaped sheet and blocky Half
band. A is rejected as the final fix; preserve its images and guard record.

B extends the CLOSED-only skin-normal/tangent remap through the attached fan,
retaining the nasal point and exact attached root centers. The long axis goes
outward/slightly down in character space and wraps on the actual socket
tangent, instead of inheriting the degenerate short-turn frame. Neutral fan
width variation supplies the design; closed cross-fringe width is reduced in
this bounded trial. Paired front/back thickness is preserved. Actual evaluated
skin-envelope contact translates paired sections together where needed, max
0.5021mm. No black fill, alpha concealment or lower-lash enlargement is used.

Only the closed endpoint and matching side endpoint arrays change. Default
source-red opening/source-green footprint, E inner walls/ocular surfaces,
healthy cheek/BodyL, brows, maps and all non-closed upper keys remain exact.
Parent's current cleaned hair survives the tested coordinate-only replay.

## Source and actual-image evidence

`SOURCE_REFERENCE.json` identifies the immutable expression sheet, original
panel02 crop and uniform6x eye crop. Panel02 is nearly closed, retaining an
ocular sliver, and has different yaw/pitch/roll and hair occlusion. Its smooth,
narrow run supports the finish direction; it does not establish exact full-
closure thickness, U curvature or 3D depth. No per-eye image warp is used.

- `first-proof-A/records.json`: before/A full closure front/profile/grazing,
  A Half in those3 views and actual neutral,10 images.
- `first-proof-B/records.json`: B full/Half front/profile/grazing plus neutral,
 7 images. Same camera/light recipe and explicit clipping0.1..10m.
- `unilateral-B-proof/records.json`:8 actual R/L0.5/1 front and affected-eye
  grazing images on the tested CleanHair child output. Same explicit clip range.
- `neutral-render-equality.json`: actual A/B neutral rendered RGB has0 changed
  pixels. Both candidates retain original raw/Basis/neutral coordinates. A
  comparison to the earlier parent neutral PNG differs by only15 pixels at
  max1 channel value, so do not call those separate render files byte-identical.

Independent reviewer actually opened every A/B and all8 unilateral images and
matched native hashes, cameras and controls. B removes most of the filled
closed central sheet, leaving a continuous narrow curve and short outward tip
in front/profile/grazing, including unilateral controls. No new background
slit, detached white surface or temporal white leak was seen. The opposite eye
remains visually stable in all four unilateral front views.

Still OPEN: blocky/broad grazing Half band; very fine full-front line weight;
R nasal fine spur; inherited U-root curvature; exact full temporal endpoint
style. Source02's near-closure does not justify automatic thickening. Parent
fresh reviewer also supports only the bounded full-closure defect fix.

## Fresh independent CPU evidence

`upper-audit/upper-B-guard.json` checks25 actual single-control states:
neutral plus global/R/L Close at0.125 increments through1.

- All preservation checks true; baseline and B hashes unchanged.
- Nonmanifold owners, nonpositive component volumes and collapsed faces:0.
- Minimum upper component volume15.44716mm³.
- Whole non-root nominal front Y-to-actual-skin clearance minimum+0.129879mm;
  buried samples below−0.01mm and missing-hit samples:0.
- Attached roots are reported separately, not hidden inside a positive-all
  claim. Between-vertex collision and arbitrary additive controls are not
  certified by these samples.

Remaining Blender probes/export/replay/render used `--python-exit-code 2`,
explicit completion markers and actual reports/hashes; process0 alone was not
treated as success.

## Lower-lash inspection and ownership

`lower-inspection/LOWER_FINDINGS.md` independently found all six neutral
blades unoccluded and opaque. Their excursion normal to the root contour is
only0.74–1.78px at512, so they merge with lower-line/fatigue paint. The active
route is constant opaque Emission, without image/alpha mixing or a missing
connection. Upper closure hides most lower blades. Lower geometry/materials
stay unchanged; no arbitrary lengthening, thickening or blackening is supported.

All actual files are confined to this new folder in the assigned isolated
worktree/branch. A setup inventory command accidentally created an EMPTY same-
named canonical folder; parent was immediately informed. No files/native/live
state were written there, and no deletion/revert was performed.
