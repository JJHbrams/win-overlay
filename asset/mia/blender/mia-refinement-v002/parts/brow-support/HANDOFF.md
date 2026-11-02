# R3 brow contact support — preferred bounded component

The actual R2 P05/P15 tick/notch is caused by **combined-pose skin contact loss**, not a demonstrated source-angle/centerline distortion or an alpha/normal paint defect. Original morphs were each independently seated to the skin, but Angry combined with Eye Close or Eye Angry loses that clearance. The mouth components do not cause the loss. Actual exact pixel rays find skin ahead of >.9-opacity brow on298/1332 P05 and143/1131 P15 subrays. The original active ink output is UV edge coverage→Transparent/Emission; normals/lights do not create its color.

Preferred solution: add one final conventional `SHRINKWRAP` modifier to each `V31_SourceBrow_-1/1`, after existing artistic morphs and HeadFollow. Settings are PROJECT, object-localY, both directions, OUTSIDE,0.1mm offset,2mm project limit. The OUTSIDE operation leaves clear vertices in place and repairs contact only where needed. It supports changing evaluated facial surfaces without adding expression special cases. Original42 arrays, all original morph drivers/values, rawcache, UV, named weights, material/maps and existing modifier prefix remain unchanged. No new expression key/control is installed.

## Portable integration

Copy these **3runtime files together**, then import `replay_brow_support.py` and call `apply()` on the current scene. It opens/saves no scene, preflights original42/raw/topology/UV by name/hash and accepts unrelated new face/eye keys. Root order is **Eye v003 first → Brow support**. `apply()` is idempotent; `remove()` removes only these two named support modifiers. Root owns final native/integration/Git/live work.

- `replay_brow_support.py`
- `brow-support-metadata.json`
- `brow_support_guard.py`

Call `brow_support_guard.check_current_pose()` after evaluating each proposed pose. It reports actual signed skin gaps,2mm projection misses with rawvertex IDs, required-contact misses and projection-axis alignment. Axis poses outside the bounded validated range are explicitly flagged. A clear missed projection is retained as a warning, not silently counted as a successful projection. Never infer all-head-angle or all-animation support.

## Actual evidence and limits

Exact read-only input is canonical `Mia_v0.0.2_Review_R2.blend`, SHA `eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82`. No new native snapshot was saved. `fresh-support-replay-guard.json` verifies201 mesh owners' original arrays/keys/UV/weights/materialslots/drivers and pose/visibility, extra unrelated face-key compatibility, idempotence and **bit-exact evaluated neutral brows**.

`project-support-full.json` measures70 bounded CPU poses: pure/intermediate Angry, bilateral/unilateral Eye Close/Eye Angry half/full cross-combinations, all16 source presets, and head yaw±22°, pitch±12°, roll±18°. All actual triangulated sampled surfaces have0negative gaps; range0.0333..0.4063mm. The maximum in the frozen portrait's observable brow runs is0.4063mm. There are3projection misses at yaw−22°, all already clear,0required-contact misses,0wrong-side hits. Two additional±90° diagnostics are **outside the accepted axis range**; they show up to1.201mm rest-plane drift despite positive sampled gaps. They are not animation acceptance.

Evaluated source-plane XZ is **not bit-exact**: the modifier's physical offset contributes up to0.054mm at the frontal pure/full tests and0.204mm under bounded turned-head stress. At P05/P15 it is about0.031mm. Original source XZ/width arrays remain exact. In the source512 projection, P05 maximum move≤0.081px and width difference≤0.062px; P15≤0.072px/≤0.043px. Across70bounded cases the maximum projected move is0.125px and width difference0.072px. This is a measured small deviation, not a source-dimensional calibration.

Three actual EEVEE images in `renders-support/` were rendered and inspected: P01neutral, P05 and P15. Exact existing R2 camera/pose/frame/material mode and source fixture3areas60/15/8 were reconstructed; all native archived lights were hidden. **Actual post-mutation light states are asserted and persisted before each frame** in the pre-render JSONs and `render-records.json`. Cameras are ORTHO512, pixelaspect1, clip0.1/10m. GPU released; no further renders requested.

Actual P05/P15 strokes are continuous after support, with the angry tilt and broad ink retained. `P05-source-before-after.png` and `P15-source-before-after.png` were actually viewed, as were both full candidate images and the original R2/source boards. The source panels retain original384x256 aspect; baseline/candidate use the same uniform display scale, with no per-feature warp. Hair-obscured full ends remain inferred. Clean uniform ink/source micro-linework and whole face/eye/hair identity remain open. `bounded-source-review.json` is **two-pose component evidence only**, not the required whole-face front/profile/left/right ART gate; root's integrated review must retain that gate.

**Strict neutral RGB invariance FAIL:** the actual P01 render differs at15scattered pixels by at most1/255, although neutral geometry and original data are exact. This is recorded in `actual-image-comparison.json`; no untested cause is asserted. P05 has10off-brow-ROI differing pixels, P15 has23, each at most1/255. Larger changes are confined to the broad brow ROI. Do not relabel these images bit-exact or claim full ART/animation readiness.

Exact pixel-order proof after the preferred modifier is `pixel-order-support.json`: P05 has0skin-before-brow out of1318opaque subrays, P15 has0/1126. Small denominator changes reflect the measured subpixel offset.

## Unselected alternative and retained failures

The seven extra interaction-key proposal (`replay_brow_contact.py`, metadata and `brow-contact-delta.npz`) is **UNSELECTED rollback/research only**. It passed50CPU states and exact neutral/original-data guards, but has more special cases and larger maximum clearance0.733mm. Do not install it with the preferred modifier. Two earlier CPU station-support assertions failed because required full-combination tail constraints reached the proposed zero boundary; they created no scene/native candidate. No broad centerline smoothing or Angry reduction was performed.

The conventional projection method follows the [official Blender Shrinkwrap manual](https://docs.blender.org/UATEST/manual/en/4.5/modeling/modifiers/deform/shrinkwrap.html); actual5.2.3 RNA settings and behavior were measured here. This link explains the method, not the observed acceptance results.
