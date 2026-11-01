# Eye contour E2 — bounded working correction

Input: `Mia_ConnectedLoft_Q7_SurfaceFit.blend` from the connected-face producer. Output: `e2-q7/Mia_EyeContour_E2.blend`. Neither producer input nor live Blender was modified. Materials, including the separately preserved M4 trial, were not changed.

## Source interpretation and actual structure

The concept's upper stroke has a shallow middle span with a short outer-end change in curvature; its lower line has a shallower central arc and a separately directed outer third. The previous model's upper arc was one high bow and the lower rim a deeper U. The concept has hair/iris/ink occlusion and slight head roll, so this is an artistic contour interpretation, not a claimed exact 2D-to-3D reconstruction or universal anatomical ratio.

`eye-topology.json` records the verified dense bake-only surface's actual topological eye boundaries, their local coordinates, UV coordinates and frozen-camera projected positions. The new applicator independently finds those boundary loops on every input; it never treats low-density legacy vertex numbers as dense indices. On the measured right-local upper rim, inner-to-outer spans local X 0.01775–0.05424 m, with Z 1.53995 at the inner corner, 1.54573 near the old high arc and 1.54413 at the outer corner. The lower central region reaches Z 1.53534 m. These are measured model coordinates, not source-art targets.

E1 added a changing offset to that old bow. It created a new small double hump and was rejected. E2 instead defines a single absolute upper target arc: inner rise → shallow middle plateau → short outer downturn. Its lower target is a single shallow U with an independent outer-third rise. The exact knots are in `build_eye_contour.py::target_deltas`, relative to the actual inner corner. Endpoint changes are shared by upper/lower branches. The control values are a bounded artistic hypothesis informed by the source, not falsely precise pixel-derived measurements.

## Modified owners and deformation

- `MIA_V14_SculptedSkin`: 1,950 dense neutral vertices; maximum displacement 1.782 mm; 0.5–3.5 mm smooth support distance from the actual 3D rim.
- `MIA_V14_UpperLash_-1`, `MIA_V14_UpperLash_1`: follow the newly shaped upper arc in their own coordinate systems.
- `MIA_V14_OuterWing_-1`, `MIA_V14_OuterWing_1`: follow the upper endpoint; only their extension beyond the canthus is shortened by 10% in neutral.
- The actual eye surface/iris is unchanged. There is no whole-eye vertical scale. Hidden legacy lower-lid cards are unchanged; the visible lower rim is the skin aperture.

All 47 skin shape-key names/order remain. Each key's actual upper/lower gap controls how much of the new neutral curve it retains. Near-full closure returns to the pre-existing closed surface, preserving the stored full-close skin key exactly. Lash follower keys use the corresponding closure treatment. This is more restricted than claiming all expressions or key combinations are validated.

## Actual review and limits

`e2-q7/actual-review` contains matched baseline/candidate actual Blender EEVEE renders: source-camera front, both obliques, profile; bare neutral, half blink, full blink; matte front and left oblique. I inspected all four neutral views, half/full blink and matte comparison. E1's new double hump is absent in E2, and the upper/lower curves are visibly shallower. Root also inspected front/left/full-close and identified a useful bounded change, not source-identity completion.

`blink-gap-diagnostic.json` measures signed vertical aperture separation at matched normalized X samples. Full-close baseline and E2 retain the same approximately -0.004 to 0.120 mm range. This is **not** a skin/eye collision solver. Neutral and half blink are narrower than baseline because the lower central arc rises and the high upper bow lowers. No general expression, bone-pose, combination-key, tear-line or extreme-eye-look pass is claimed.

`saved-native-audit.json` separately checks saved/reopened native geometry, topology, UV, keys, material assignments, transforms, modifiers, vertex weights and original packed image bytes. The wider jaw/profile and midface limitations are inherited from Q7; this eye-only pass does not resolve them. The old and new candidates remain available for root integration/review.

## Reuse

The Blender script requires only Blender's bundled `bpy`, `mathutils` and NumPy. No external file is read by `apply_eye_contour('e2')`; the default `--source` path is only a convenience for this workspace. For another same-layout dense Mia candidate:

```text
blender --background --python build_eye_contour.py -- --source <input.blend> --output-dir <fresh-output> --variant e2
```

Requirements: actual dense skin with shape keys; the named skin/lash/wing owners; the same character scale/rest-axis convention. Boundary detection and owner-to-skin coordinate conversion are recomputed on the input. The function neutralizes skin keys for the operation. It refuses an existing output native. Reapplying E2 to an already corrected native is not an intended use. A new input with changed midface/orbit support needs fresh actual matte/contact/source comparison; a reusable script does not make that review automatic.
