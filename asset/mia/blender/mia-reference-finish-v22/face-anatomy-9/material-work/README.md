# Material-only identity trials

The baseline already consumes its actual 2K BasePigment, FatigueMask and FineLineMask. The missing impression is not a missing image connection: the prior look contains one broad lower-lid crescent and one adjacent fine line, with weak separation of the concept's pigmentation and fold layers.

- M1 increases the existing mask response and shifts a second copy of the fine line. The fold remains inside the bag and too red.
- M2 moves that copy below the bag and reduces the red bias. The original UV-triangle streaks become visible in the copied line; do not select it as the final fold.
- M3 retains the M2 brown/mauve pigment and uses a smooth shader UV curve measured from the old lower-lid UV arc for a separate, tapered lower fold. Actual front/oblique/color-only renders show a visible second layer without copying those streaks. The result is still too clean and long compared with the concept's irregular line emphasis. It is a working material study, not source-likeness acceptance.
- M4 responds to the root review of M3: half-strength, narrower fold restricted to the outer third; its inner and central extent fades out. It is the next material candidate for root review, not automatic promotion.

M4 was rendered and visually checked in front, left oblique, bare lit and color-only. The continuous dark ellipse is gone; the outer fold is subtle and partly hidden by hair. The concept's upper crease and irregular pigment emphasis are still missing. A successful graph/geometry audit does not close that visual gap. `saved-trial-audit.json` confirms all four saved natives preserve mesh/UV/topology/keys/transforms, all other material assignments, and the three original packed maps exactly. M4 native SHA256: `cd6a862839858a33e97d9afd8fed2b40576818bee8978e76d885a74bd8d20ae2`.

No mesh, UV, topology, shape key, transform, body/hair material or light was edited. Saved natives are re-read and audited. Existing map bytes remain exact. No new raster texture, resolution, normal or specular map is claimed. All images under `actual-review` are actual Blender EEVEE renders, with the frozen source-review camera/light values. Pigment-only output bypasses the existing light multiplier in memory for inspection only.

Reusable application: import `apply_material_identity.py`, then call `apply_identity(bpy.data.objects['MIA_V14_SculptedSkin'], 'm4')` on a new geometry candidate that still has the Finish8 material route. Or run the script with `--source <native> --output-dir <fresh-directory> --variant m4`. Do not overwrite baseline. New geometry and blinking require a fresh alignment/contact/appearance review; the old shader UV curve is not automatically a fit to a different aperture.

The wider face geometry and final character remain unaccepted. Root owns integration, Wiki, Git and any promotion.
