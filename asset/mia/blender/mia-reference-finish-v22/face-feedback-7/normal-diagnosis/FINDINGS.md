# Face6 / R8 normal-route isolation

**Conclusion: the remaining diagonal inner-cheek/orbital ridge is not explained by stale, custom, sharp, or split shading normals. It persists in ordinary diffuse shading with freshly recomputed normals on exactly the same evaluated surface.** Correct the surface/curvature distribution rather than treating normal recalculation as the fix. This does not approve the current shape or prescribe a new shape.

## Direct checks

Both Face6 and R8 have:

- 1,342/1,342 skin polygons smooth; zero sharp edges; `has_custom_normals=False`.
- Armature followed by Subsurf level 2 / render level 2, `use_custom_normals=False`, `boundary_smooth=ALL`; no Weighted Normal modifier.
- Evaluated skin: 16,338 vertices and 16,104 all-smooth polygons; no custom normals or sharp edges.
- All skin polygons use material slot 7, `MIA_V22_Finish5_LocalUnderEye`, with no connected Normal input. Other unused legacy slots contain Normal Map links; those are not the skin polygons' route. The diagnostic replaces all skin/body slots with identical plain diffuse material anyway, removing paint/normal-node explanations.
- At each shared evaluated vertex, all corresponding corner normals agree (maximum spread 0).

The already evaluated skin was rebuilt in memory using exactly the same coordinates and polygon indices, all faces smooth, no custom/sharp attributes, and no modifiers. **All original vs recomputed corner normal vectors have exactly zero component/vector difference for both sources.** Coordinates and face indices compare exactly. The small nonzero angle values in `normal-report.json`'s dot/arccos statistic are floating-point unit-length errors; do not interpret them as a normal change when vector difference is exactly zero.

The report also compares corner and polygon normals. In the bounded inner-cheek region (local absX .015–.055, Z1.490–1.540, frontY>.025), median corner-to-face angles are 1.61° Face6 and 1.54° R8; maxima 8.00° and 10.58°. These are ordinary smoothed normals versus individual polygon planes, not stale-normal errors or an acceptance metric. Whole-mesh maxima include unrelated regions and should not be used to diagnose this cheek.

## Crease caveat

Both sources retain 34 crease edges of value 1.0, all on the previously identified face–cap outer boundary. None is an inner-cheek/orbital ridge edge. Subdivision creases affect evaluated geometry, unlike a stale shading-normal attribute. They may matter to the separate forehead/cap boundary shape, but removing them would alter geometry and was **not** tested or authorized here. `crease-supplement.json` lists every edge, vertex ID and coordinate. Do not confuse 'zero sharp shading edges' with 'zero subdivision creases'.

## Actual A/B

Eight fresh 700² RGBA renders: Face6/R8 × original/recomputed route × yaw+30 elevation−10 / yaw+60 elevation0. Orthographic scale .29, targetZ1.55, roll0; fixed root scene lamps, neutral frame1, hair/ink hidden, plain diffuse skin/body, unchanged eye appearance. The R8 low30 and level60 originals and low30 recomputed image were directly viewed; the ridge remains. Original materials cannot explain a ridge retained by this matte route.

Face6 low30 images are pixel-exact. Other pairs have small render differences after replacing the object/modifier route: mean absolute RGB differences .045–.050 levels out of 255. Differences include low-level surface sampling and edge pixels, not exclusively silhouette pixels; local maxima reach 49 at some edges. The direct normal-array equality is stronger evidence than a claim of pixel-exact rendering. `pixel-comparison.json` and `*_difference10x.png` retain these limits. No interpolation, repaint, or geometric deformation was used.

## Preservation and files

Face6 SHA256 `f5d17264e07f492983e7e075d5a3213b2bd14a4adaead82072899e9b3e15d98a`.

R8 SHA256 `8b92d4df49c80bccc44e8c5def1664788d68b56c0c6b5de805b3c72c1768d4b9`.

Both source hashes were verified unchanged after diagnostic operations. No native was saved, no production geometry/keys/materials were written, no GUI or Git was used.

Exact scripts: `inspect_normals.py`, `inspect_crease_values.py`. Data: `normal-report.json`, `crease-supplement.json`, `pixel-comparison.json`. Fresh images: `{face6,r8}_{original,recomputed}_{low30,level60}.png`. Diagnostic helpers are the frozen canonical sibling `../surface-diagnosis/dependencies/review_setup.py` and only the AST-loaded `rig`/`constant` functions from `shape_evidence.py`; their provenance was frozen in the surface-diagnosis delivery manifest. Native paths and image/camera hashes are recorded in `normal-report.json`.
