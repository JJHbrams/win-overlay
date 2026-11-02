# Brow visibility: source and exact 4dc1

The brows exist. HairOFF shows both independent V31 strokes; hairON conceals almost all of them. A tiny medial fragment survives in the forehead gap. The long brown line immediately above the heavy upper lash is the upper crease, not a replacement brow.

Evidence uses the exact R3b native SHA `4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`. All 32 expression hairON/OFF PNG hashes and the front pair were checked. No model, native, live session or renderer was opened for this analysis. Crop scales are uniform; the layouts do not claim source-pose/proportion registration.

- `portrait-actual-brow-crease-lash-annotated.png`: unmarked pixels above, semantic traces below. Cyan=brow, amber=crease, green=upper lash/liner.
- `source16-eye-band-native-crops.png`: all source expression eye bands, using one fixed crop and scale.
- `actual-source16-brow-hairON-OFF-page1.png` and `page2.png`: all 16 actual paired upper-face crops.
- `layout-evidence.json`: paths, hashes, crop coordinates, trace uncertainty and a conservative color-agreement proxy.

The manually checked front brow windows have 647/662 dark hairOFF pixels. Only 35/26 agree within two RGB levels after hair is shown. This is an appearance proxy, not a physical ownership mask or exact visible-area percentage. The actual images show the remaining tiny fragment and the occluding bangs directly.

## Source fragments and uncertainty

The portrait has separated brow-level dark strokes, fine warm upper creases and substantially heavier lash/liner. Brow-level strokes continue across some hair-colored thin locks. This supports a deliberate partial over-hair brow read in the illustration; it does not prove the source creator used a specific transparency/rendering technique.

For production, use the conservative already-recorded V31 observed portrait runs: screen-left X410..455 and screen-right X520..551 in the original1024 image. The rest of the full modeled brow is a bounded continuation or ambiguous hair overlap. Candidate parameter windows come from those source runs along the original brow construction curve, not a generic full-width forehead strip.

| Source panels | Observable reading | Inferred or covered |
|---|---|---|
| Portrait, 01/03/08/13/16 | Low brow fragments remain distinct above the crease; the screen-right medial segment is particularly readable. | Full outer tails and the central forelock-covered continuation. |
| 02 | Brow fragments remain above the near-closed eye. The low dark closed-eye line is lash/lid, not brow. | Full covered brow contour and exact closed-lid anatomy. |
| 04/06 | Oblique poses still retain a readable medial brow/short continuation across fine fringe. | Far-side tail, depth and hair-hidden joins. |
| 05/07/11/14/15 | Tension/weary brow inclination changes separately from the crease and lash. Fine crossing locks do not erase every brow cue. | Exact complete width beneath thick locks. |
| 09/12 | Raised/concerned inner segments stay readable at brow elevation, including across hair-colored regions. | A fully exposed complete arch is not justified. |
| 10 | Short lower brow fragments still contribute to the grin. | Complete tails and covered central spans. |

Current hairOFF brow shape is not declared a complete source match. This task concerns preserving its expression signal under the accepted fringe. It does not reopen the accepted facial sculpt, lower-lid task or upper-fold registration.

## Chosen bounded candidate method

Use separate hair-surface ink geometry projected from the **actual evaluated, deforming V31 brow objects**, only onto an explicit foreground-fringe owner list. Keep original brows on the skin and leave all original fringe coordinates/materials/UVs intact. Reject projection misses, hair gaps, cross-owner bridges and large surface-depth jumps. Allow only source-supported partial parameter spans, with tapered ends and an independent strength control.

Projection is in a head-following frame, not the current review camera. A frontal-angle fade must suppress the display toward profile/back views. It must never show a brow through the skull, braid, bun, rear hair or hands. The overlay is real evaluated 3D geometry with a small new material, so the same scene supplies live EEVEE and sprite renders. There is no manual PNG draw-over or hidden whole-material replay.

Small natural bang gaps remain a secondary option only at separations already supported by source. Gaps alone would need substantial removal to reveal the entire existing brow, which would change the accepted fringe silhouette. Moving the physical brow in front of the bangs would produce a floating depth error. Making all hair translucent would reveal unrelated face regions. None is the selected first candidate.

The underlying rendering idea is established, but engine-specific. lilToon's creator describes eyebrow-only stencil masks plus a controlled overlaid hair layer in Unity; those instructions are not a Blender API recipe. [Creator's primary description](https://qiita.com/lilxyzw/items/3684d8f252ab1894773a). A current tool creator likewise limits through-hair visibility to selected face regions and explicitly targets Unity/VRChat. [Creator documentation](https://goorm.me/en/docs/see-through-hair). No package is being installed.

Blender's current EEVEE pass documentation notes that ShaderToRGB works correctly in Combined, so a generic separated diffuse-pass composite cannot be presumed equivalent to this scene's toon output. [Blender manual](https://docs.staging.blender.org/manual/en/latest/render/layers/passes.html). A compositor-only result would also need separate live-view handling. This is why the first candidate uses bounded scene geometry rather than an offline-only overlay.

CPU audit will establish exact fringe owners, projection distances, parameter direction, deformation/head-follow behavior and original-data guards. Root then allocates four actual before/after front/oblique frames. Until those are inspected, the method is a candidate, not a visibility or source-ART pass.

Actual A status: the first four-frame proof was RGB bit-exact before/after and **failed visibility**. The recreated wrapper context found the new material's angle gate used +Y, while Blender Geometry.Incoming points toward the viewer (front is head-local−Y). Every old alpha was0. All front geometry samples were ahead of Main; the actors/materials existed. This is a producer gate error, not missing source brows or a compiler claim. [Blender5.2 primary documentation](https://docs.blender.org/manual/en/5.2/render/shader_nodes/input/geometry.html). The failed helper/proof is retained. Only the gate polarity is being corrected on CPU; no additional render or ART improvement is claimed until root allocates it.

Source braid-form refinement remains deferred until the face/body order is satisfied. It is retained in scope and is not part of this front-fringe display task. Rear-hair/UV/color work remains with the hair worker.
