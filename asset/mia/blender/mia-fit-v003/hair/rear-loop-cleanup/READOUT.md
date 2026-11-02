# Unsupported lower rear U-loop: bounded cleanup

The actual R3b + selected A+B Crown-pigment baseline had a large suspended U-shaped bridge across the lower rear hair. The v22 back/profile source has overlapping descending waves and individual turned ends, without that broad bridge. This delta hides the unsupported logical U family. It does not finish the rear hairstyle.

## Exact scope and failed first attempt

The first six complete disconnected skins (773 triangles) were insufficient. CPU first-hit comparison after hiding them exposed the same U on its backing and several smaller return skins. This candidate was rejected before spending GPU renders. Its original payload, manifest and technical guard are retained as `*-six-only-REJECTED.*`; a passing preservation test did not make it a useful shape correction.

The final family contains **1,781 triangles**: 27 complete globally connected natural-boundary skin components, plus the **438-triangle backing branch** inside Main component488. The branch containing raw source99704 remains separate while following its two roots upward, then first joins the large hair surface at Z1.45416164. Four explicit physical attachment edges mark that logical branch boundary. The companion skins were reviewed as complete pieces against the first-hit contour, not cut by screen pixels. Component231 (16 triangles) was the last disconnected thin lower return remnant.

Neighboring long side curls202/193/211 and inner pointed layers292/239/278 remain. Front bangs, true forelocks, braid, gathered-hair bun, Crown geometry and all other actors are outside ownership. Full face IDs/raw source IDs/triangle vertex triplets are in `loop-mask.npz` and `manifest.json`. Runtime selection is an explicit fixed payload, never a camera rectangle or dynamic height threshold.

`topology-family-before-after-DATA.png` shows baseline, rejected six-only, backing-only extension and final family. These are CPU Main-only geometry ownership diagrams, not shader renders or an ART check.

## Front visibility exception was inspected

The complete backing U has some lower-nape visibility from the front. The zero-front-change guard stopped before writing a new production payload. We then inspected `fullscene-front-profile-ownership-DATA.png`, original-aspect source context and exact hit locations. Root explicitly accepted this bounded lower-rear exception; accepted facial bangs/forelocks/braid/bun are unaffected.

At the384-square technical raster, selected first-hit counts were51 at000,8 at003,485 at021,104 at018 and1187 at back_full. Front000 selected world hits lie around X−0.0417…−0.0290, Y+0.0727…+0.0820, Z1.4256…1.4413: the nape/shoulder tail, away from facial features. Diagnostic barycentric-ray counts and raster counts differ and are recorded separately. Neither is a source-likeness score.

Four backing-root edge midpoints are obscured by retained hair in back/low/profile checks. Two are exposed from021 in the CPU test, so actual021 review is required rather than assuming hidden cuts. Back coverage after removal includes retained body; the source's missing descending hair volume has not been rebuilt by this cleanup.

## Portable application and exact rollback

```python
from pathlib import Path
import sys
folder = Path("<checkout>/asset/mia/blender/mia-fit-v003/hair/rear-loop-cleanup")
sys.path.insert(0, str(folder))
import apply_loop_mask
result = apply_loop_mask.apply(folder)
# During a coordinated review, before any later Main material append:
apply_loop_mask.restore(folder)
```

The helper works on the current scene. It opens no old native, appends one transparent material and assigns exactly the owned triangles. It preserves the current selected A+B Crown material and captures current original slots for rollback. It checks the Main coordinate/topology hash and raw source correspondence before changing anything. It refuses a duplicate install, unexpected geometry, or uncoordinated rollback after another Main material append.

The final guard verifies618 existing object owners, all seven current UV layers, authored coordinates/topology/POINT fields/weights/shape keys, actual corner normals and the scene. Only the Main material list/signatures and owned face material indices change. Apply→restore returns the entire authored snapshot and face indices exactly. The original six UVs remain unchanged; the selected color checkpoint's seventh UV remains unchanged too.

The raw U mesh remains physically present because this is reversible render visibility. A later collision/export proxy must explicitly omit these face IDs. This is not a physics or deformation acceptance result.

## Actual review and limits

`actual-first4/` contains two complete actual baseline/candidate pairs: back_full and oblique_low_full. Each pair retains the same orthographic camera, clip0.1/10, three actual source lights60/15/8, world and neutral pose. Full lower hair is framed at scale0.72 around Z1.47. Runtime logs have no shader compile error. `ACTUAL_SOURCE_BACK_LOW_REVIEW.png` places original-aspect source context beside these renders; the profile source beside the low-oblique pair is explicitly not a camera match. No source feature/aspect warping was used.

The U disappears in both actual pairs. Remaining lower hair is still sparse/coarse, side underlayers retain torn/folded tips, and source-specific descending lock flow and fine ink are not finished. The cleanup does not fix those issues or establish whole-hair ART PASS. The first four640-square actual frames inherited the native sampling; the final six diagnostic frames explicitly use512-square/32TAA consistently within each pair, recorded separately. Their different resolutions are never mixed in a before/after pair.

Root owns final actual selection, integration, saved-native source-review validation, live application and remote Git operations. This child task does not save a native, replace the latest face/body guides, or claim full Mia completion.
