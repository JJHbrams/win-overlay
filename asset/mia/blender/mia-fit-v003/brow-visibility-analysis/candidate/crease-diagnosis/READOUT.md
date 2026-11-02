# Crease visibility diagnosis and bounded JSON trial

The intended skin mask is mostly behind the opaque upper lash stroke. It is registered to the true sclera rim, but the 1.3–1.8 mm superior offset does not clear the lash's upper silhouette.

The actual EEVEE output of `V30_UpperLash_DeepInk` is a direct Emission, RGB (.008, .005, .009). It has no transparent mix or alpha texture. With the exact crease-B front camera and its hairOFF flags, 35/36 left and 33/36 right centerline rays hit these upper lash meshes before the skin. This is independent of the corrected material-slot restoration. Neutral `V30_FoldOpen_L/R` and `V30_FaceRootFade` are 1. The CPU vector mask reaches .65 on the intended skin.

The active route is `V30_ActualFaceUV` → segment-distance mask × opening × .65 × root fade → Multiply `Mia.v003.AlignedCreasePigment` → `V30_PigmentTimesActualLight`. The shared face UV hash is unchanged. This audit does not identify a compiler failure or a disconnected pigment route.

The original physical full width is .34 mm before taper, roughly .90 pixels at the 768 / .29 m review scale. Taper makes that narrower. This limits the remaining exposed line's strength, but the measured opaque lash occlusion is the principal cause of near absence. UV anisotropy and the exact rendered footprint remain unmeasured.

`upper-crease-vector-visible-candidate.json` retains the ten true-rim stations per side and their actual rising canthus curve. At each station it measures the opaque lash's upper edge in .05 mm increments, adds .8 mm, and limits the total rim offset to 3–5 mm. It recomputes the same .17 mm physical half-width in the actual skin UV. Original lash, eye opening, UV, keys, and scene are untouched.

The 20-station before/after report is `visibility-20-stations-before-after.json`. Eighteen revised stations are skin-first. Screen-right t=.10 and .93 remain lash-covered at the 5 mm limit. Fifteen stations retain .8 mm clearance; three other skin-first stations have only .075–.575 mm clearance. These are explicit limits, not a passing visibility gate. A source-faithful next choice is to taper/end the crease before those covered corners, rather than lift the whole line into the brow band. Root chooses the span and actual render trial.

The portrait shows a thin warm crease above the heavy black upper lash and below the separate brow fragments. The clear gap varies with the real eye/canthus slope; a generic replacement arch would lose that relationship. This inspection does not establish an exact source-pixel-to-model-mm equivalence. The supplied .8 mm gap is a bounded trial, not a measured source proportion or ART approval.

The full initial CPU ray and active opacity graph inventory are retained in `../../crease-mask-readonly-audit/crease-owner-rays.json`. All rays use evaluated viewport meshes and the recorded actual camera; no render-DG capture or new raster proof is claimed. No GPU, native save, canonical edit, or model modification occurred.
