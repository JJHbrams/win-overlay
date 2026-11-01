# M5 upper-fold material candidate

M5 adds a thin, separately fading warm-brown upper crease, weak upper-lid pigment and a faint lower-lid highlight to the existing M4 material. It is an incremental material candidate, not finished source likeness. No raster map was created or repainted.

## Preserved state and candidate

Input is v22 `integration-wip-9-review/Mia_FaceReview_v22_WIP9.blend`, SHA256 `fb85468a623e1befc590176a24636548b944491ce4ae19decaece625304945b2`.

Retain `placement-corrected/Mia_UpperFold_M5.blend` as the one look candidate. `placement-corrected/manifest.json` gives its exact hash and saved/reopened audit. All mesh coordinates, topology, shape keys and values, UVs, transforms and original packed image bytes remained exact. Only the skin material slot 7 assignment changed; all other mesh material assignments remained exact. The original WIP9 native was not overwritten.

The first attempt is preserved under `trial/` and `actual-review/` but is not the candidate to use. It added the same bounded look too close to the actual lid boundary, which left most upper crease under the thick black lash. Its original recipe is preserved as `trial/executed-recipe-under-lash.py`, and that trial's manifest points to those exact bytes.

## Measured placement, not blind contrast increase

The reaffirmed face portrait was directly inspected before this pass. The reference shows a warm crease above the black lash, a wider muted fatigue mass below the eye and lighter separation toward its lower edge. It does not show a dark closed ring around the entire eye.

`measure_lids.py` reads each actual dense boundary cycle and its face-material UV samples. `measured-lid-uv.json` records the observed left/right upper/lower boundaries. No legacy vertex index map is reused.

`probe_lash_clearance.py` barycentrically maps UV positions onto the actual skin and compares them with the nearby upper-lash top. `lash-clearance-probe.json` records three stations. The original crease centers were approximately -0.70 to +0.16 mm relative to that top, explaining why the line was largely obscured. An offset near 0.020 UV gave approximately 1.90 to 2.42 mm clearance in these samples. These are local-Z clearance probes, not camera ray visibility or collision guarantees.

The corrected pass keeps the same line strength and width and changes only the upper crease/pigment placement. It does not increase global contrast. UV-to-physical distance varies; offset/width/strength remain artistic parameters informed by the reference, not an anatomical measurement from the illustration.

## Reusable application

`apply_upperfold_m5.py` is self-contained except for Blender's `bpy` and bundled `numpy`. Import and call:

```python
from apply_upperfold_m5 import apply_upperfold_m5
material, measurements = apply_upperfold_m5(bpy.data.objects['MIA_V14_SculptedSkin'])
```

Apply M4 first if the new geometry native does not contain it. M5 requires the actual `IDENTITY9_SecondaryFoldPigment` and `FINISH8_ACTUAL_UV` routes. Reapplying M5 to an already-M5 material is rejected. It rereads boundary topology and UVs and copies only skin slot 7's material. It does not edit geometry, keys, UVs, images, lighting or camera. Save and reopen are handled by the CLI wrapper or by the parent's integration stage.

This is scoped to the current Mia dense topology, face slot 7, `UVMap` and existing coordinate frame. It is not a generic character-material tool. The renderer depends on the established v22 frozen review helper; the apply function itself does not.

## Actual render review

`render_upperfold_m5.py` produced 12 actual Blender EEVEE images for the corrected candidate: baseline/M5 x lit front, lit left oblique, color-only front, color-only left oblique, half blink and full blink. The output is `placement-corrected-review/`, including exact native/render hashes and matched camera/light/display/key records. All paths were absolute. No native was saved by the render helper.

`compose_m5_review.py` only lays out original source and the actual renders under the inherited uniform SRT. It does not paint textures, generate model imagery or refit the candidate to the source. Color-only hides hair and bypasses only skin lighting; eye/accessory shaders retain their native routes.

Producer review and the independent reviewer inspected the corrected source boards and half/full-blink pairs. The thin warm-brown upper fold is now readable above the lash in neutral and blink states. It follows the deforming skin without an obvious new black ring, detached floating line or white leak in this limited set. Hair-on improvement is subtle. The faint lower highlight does not fully restore the source's lower rim identity.

The independent reviewer recommended retaining M5 as an incremental material gain only. Source fold strength/shape, lower rim identity, the broad uniform under-eye band, irregular linework and overall facial proportions remain incomplete. No all-expression or ART PASS is claimed. Underlying WIP9 cheek/shading defects seen during blinking were already present in the baseline; this material-only audit does not resolve them.

No further material variants were made after the single measured placement correction. No Git, Wiki, live Blender, or files outside this owned folder were changed by this task.
