# Eye depth causal test — frozen 6794 face

The current eye is an open curved carrier assembly, not a closed spherical eyeball. Changing its depth affects iris/sclera presentation and lid overlap. It does not remove the fixed outer lower-lid-to-cheek wall in these actual renders.

Source: `../../frozen/Mia_FaceCorrection_v20.blend` (absolute source path is in `diagnostic.json`), SHA256 `6794a9b331b7c061e6d75ffc27e9f65d8d31e48971d3f82dd2e98be499b52ed0`. This corresponds to the face geometry in the user's live aa02 neutral scene. No native was saved in either depth experiment. Source bytes, all other mesh coordinates/keys/object transforms, aperture, lids, lashes, and skin were checked unchanged.

## Structure

`MIA_V14_EyeSurface`: 436 vertices / 544 polygons, no shape keys or modifiers. Sclera: 96 polygons, 142 vertices, 140 material-region boundary edges, backface culling enabled. Iris: 192 polygons, 122 vertices, 48 boundary edges. The remaining 256 polygons are legacy glint surfaces using the hidden material. These boundary counts include disconnected/seam structure; they are not a manifold eyeball topology claim. Both eye regions together span 18.05 mm in world depth for sclera and 6.67 mm for iris; these are carrier depth spans, not anatomical globe diameter.

## Position only

Five variants move the entire EyeSurface rigidly in world Y: retreat 1.5 / 0.5 mm, unchanged, advance 0.5 / 1.5 mm. Front, +45°, true +90° profile share 1400² orthographic scale 0.29 m, target (0,0,1.55), roll 0. Other geometry and source appearance are fixed. `position-comparison.png` is an unwarped crop sheet; original full renders and exact camera matrices are retained.

| Variant | Actual observation |
| --- | --- |
| Retreat 0.5 mm | Front RGB identical to baseline. At 45°/profile the iris shifts within the fixed aperture and white distribution changes slightly. No loss of far iris. |
| Retreat 1.5 mm | More noticeable profile iris shift/white redistribution, with small occlusion changes. Does not soften the skin wall. No complete iris disappearance in the tested views. |
| Advance 0.5 mm | Front changes only 3 pixels above one code value; oblique eye presentation changes slightly. Skin wall remains. |
| Advance 1.5 mm | Thin dark protruding marks appear above the upper lid, visible in the front and oblique render. This is a regression; it should not be adopted to solve the cheek. Lower eye overlap also changes. |

For ±0.5 mm, changed pixels in the oblique renders stay in the eye region; the cheek silhouette and shading away from it are unchanged. Exact RGB difference bounds are in `pixel-difference.json`. Appearance alone does not identify which hidden carrier triangle causes the +1.5 mm dark protrusions; the causal isolation identifies the moved eye assembly, not a new skin defect.

## Curvature depth only

Separate sibling `eye-curvature-diagnostic/curvature-comparison.png`: Y depth scales 0.9 / 1.0 / 1.1 around each iris's original frontmost tangent plane, keeping X/Z, face, aperture, object transform and material fixed. The two local-Y pivots are 0.06424427 and 0.06431536 m. This is a depth-curvature perturbation of the existing open surfaces, not a new spherical eyeball or an anatomical thickness reconstruction. Maximum coordinate change at 10% is 1.873 mm including legacy surfaces.

The 45° and profile renders show modest changes to visible iris width/curvature and white distribution. Both retain the same broad lower orbital/cheek wall. No far iris collapse or new major lid gap appears in these two tested views. This limited test does not establish a final preferred depth scale or animation compatibility.

## Relationship to frozen v21 3cd

`main/Mia_OrbitalGuide_v21.blend` remains SHA256 `3cd4b6414b017223d4be721c4022df361f7d2e83b5b6f0276bc82711838bed75`. It has a separate landmark-guided skin depth correction, plus **iris vertices only** retreated 0.35 mm; non-iris eye vertices follow its local surface field. That is not the whole-eye rigid translation tested here. No depth-probe variant has been incorporated into 3cd.

Conclusion: the user's depth hypothesis is relevant to eye/lid fit, especially in profile. The tested position/curvature changes cannot independently repair the residual skin wall. Keep eye fit and skin surface continuity as separate decisions; no production-depth selection or art pass is implied.
