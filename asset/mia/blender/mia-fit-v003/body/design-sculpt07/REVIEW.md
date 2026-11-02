# NEW design-sculpt07-A — first actual look FAIL / UNSELECTED

2026-11-03. Fresh private upper-body design volume. **This is not an accepted anatomy base, retopology result, new selected native, or completed body correction.** Original R3b remains selected and unchanged. No native scene was copied or saved; no live application, push, installation, UV/key/weight migration, or animation was performed.

The worker directly inspected all four actual images and all four source/baseline/candidate boards. The initial fresh volume is **ART FAIL**. Source binding and a closed connected surface did not produce a convincing anatomical design.

## Actual judgment

| View | Judgment from the actual comparison | Remaining issue |
|---|---|---|
| Front, yaw0/pitch0 | FAIL | Pointed upper breast emergence, long teardrop silhouette, and visible separate-looking deltoid/fan masses. The source has a broader rounded supported mass and smoother shoulder/root transition. Lower return still has an unnatural small tip/ridge. |
| Profile, yaw85/pitch0 | FAIL | Forward profile is rounder than rejected06, but this is not sufficient: upper root slope, shoulder cap and lower return remain wrong. v06 source is an illustrated near-profile, not a calibrated85° view. |
| Reaffirmed F2, yaw40/pitch−8 | FAIL | The pointed top and artificial pectoral/deltoid lobes persist. Private context displays cut gaps at forearms and abdomen; these are context-mask defects, not source anatomy or final seams. |
| Rear oblique, yaw140/pitch−10 | FAIL / posterior source correspondence UNVERIFIED | Deltoid/posterior-wall lobes remain visibly separate-looking despite one connected mesh. v06 back is covered by hair and is context only; it does not calibrate this rear-oblique view. |

Actual evidence: `source-front.png`, `source-profile.png`, `source-F2lowoblique.png`, `source-rearoblique.png`; a compact actual-only contact sheet is `actual-four-contact-sheet.png`. The center column is explicitly rejected06, not the current unmodified native body. Four new actual frames only were taken under the root's GPU token; the token was released after completion. Render log has zero case-insensitive matches for `error|compile|failed|traceback` and ends with successful completion / Blender quit. Process exit was0.

## Construction and source use

`freeze_parameters.py` reads the actual observed `section_support_bands` and `anterior_fold_bands` before writing any geometry parameters. The frozen JSON embeds the priors and original source SHA256 values. Measured E2 maximum halfwidth derives the bilateral breast center and radial allowance; v06 world-Z/profile bands derive the continuous front profile with explicitly declared8/8/7/14mm anterior allowances. These allowances are manual design hypotheses, not recovered naked anatomy. `inferred_lateral_x`, `chosen_lateral_y` and inferred fold coordinates are explicitly excluded as hard targets. The actual support maximizer is allowed to move.

`field.py` builds a new approximate implicit field from a curved tapered thorax/neck, positive breast pair, shoulder/upper-arm and broad buried anterior/posterior volumes. It never reads old01/05/06 vertex coordinates, compressed control rows, cage patches, UVs, keys or weights. The radial profiles are fresh continuous Hermite functions of the observed priors, not copied failed rows. Smooth union is local:3mm interbreast,16mm breast/thorax,10–16mm arm/root components. No collider subtraction, drilled hole or flat axillary membrane is used. Air is left by placement.

The mesher is Blender5.2.3 native `Volume Cube → Volume to Mesh` at threshold0.5, density `max(0,0.5−field/0.012)`, background0. The radial/ellipsoid field is **not an exact SDF**. Grid resolution225×120×175 =4,725,000 points; actual cell steps2.983–2.991mm. CPU analytic/native-node field probes agree exactly at the eight sampled positions. Meshing took3.24s and produced74,366 vertices /148,728 triangles in a1.16MB NPZ. No package was installed.

The field is an implementation hypothesis justified by the design-before-retopology order, not a claim that the cited tutorials used implicit/voxel construction.

## Technical evidence and its limits

`cpu-audit.json` measures one connected closed manifold, no boundary/nonmanifold edges or zero-area triangles, Euler characteristic2, positive signed volume. Six declared axillary corridor probes lie outside the positive volume; these samples do not establish final anatomical quality or a complete tunnel/collision proof.

| v06 Z | Broad-ROI F2 support residual | Semantic breast-only residual | v06 front-profile residual |
|---|---:|---:|---:|
|1.308924|+19.24mm, outside14mm band|−3.28mm|−7.96mm|
|1.284927|−10.97mm|−10.97mm|−7.98mm|
|1.257238|−12.57mm|−12.57mm|−6.88mm|
|1.220319|−12.54mm|−12.54mm|−13.94mm|

The broad ROI is exactly declared `|X|<180mm,Y<−50mm` and retained even where its upper support maximizer is arm/anterior fan. The separate semantic diagnostic uses actual mesh intersections where the breast primitive field is within2mm of the nearest other primitive. It does not replace or erase the broad-ROI FAIL. Cup/cloth width is not total upper-torso width; the broad ROI upper width is contaminated and must not be called an E2 cup-width success. Narrow source-support residuals do not approve the pointed volume seen in the actual images.

`preservation.json` contains all47 raw key hashes and the last690 raw face-control hashes before/after. Original owner arrays remain exact. The private ORIGINAL context retains the entire original raw mesh, keys and modifiers; only its private per-face material indices change for the transparent ROI mask. Its **entire80,771-vertex evaluated coordinate array** is bit-exact to the original at frame1, measured with equal topology and evaluation, not assumed from an evaluated prefix. Source native SHA256 remains `4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`. These are preservation checks, not acceptance of the new design or context seams.

The four actual camera dictionaries are bit-exact to the inherited06 fixtures. Actual active light energy/size/shadow match, light matrices differ by less than1e−7 from the inherited fixture. Actual camera clipping0.1..10m, orthographic scale, pixel aspect, frame, original rig pose/master keys, physical-gray material inputs, lights, world and color management are recorded before each shot. Hair is hidden using the existing ownership helper. No mesh origin or rig coordinate was moved.

## Why the initial construction failed / bounded next hypothesis

Producer inference from the actual frames: the constant anterior breast center and shrinking radial cap expose a small upper cap before a broad buried root exists, creating the pointed cone. The same construction leaves the inferior cap barely exposed as a tip. A smooth union does not automatically bury volumes; shoulder/fan/posterior ellipsoids were too exposed and read as separate muscle balls. This inference requires another actual source comparison before it can be called a solved cause.

A possible next design would vary anterior center/depth and width independently so upper/lower ends disappear inside the curved thorax while the exposed mass stays broadly round, and bury the shoulder/connection volumes more deeply. It should also use a tighter context mask that preserves forearm/abdomen continuity. **That next hypothesis is not implemented here.** No retopology or migration should begin from this failed volume.

## Evidence-gate and activity status

Source boards exist with original aspect / frozen wholeheight uniform registration; E2/F2 use one global metres-per-pixel. Back-oblique source calibration and candidate native save are deliberately absent in this first bounded static experiment. It is not a complete mandatory front/profile/back/oblique selected-native review package, and is not eligible for promotion. A validator success is not claimed. Root must review the actual boards and decide the next bounded design iteration.

Engram knowledge/activity MCP tools were unavailable in this delegated session. This repository record is the activity record; no Wiki or Engram sync is claimed. Work occurred only on branch `codex/mia-v003-design-sculpt` in the assigned worktree and only under this directory.
