# Frozen orbital surface candidate v21 — independent art review pending

The primary candidate fills the excessive depth recession between the lateral lower orbital rim and anterior cheek. It does not narrow the whole head or reinterpret reduced face width as success. Compared at the same front/20°/45° camera and neutral diffuse rig, the recessed wall is less pronounced, while the outer corner and broad temple transition remain imperfect. No full face/art/expression pass is claimed.

Native: `Mia_OrbitalGuide_v21.blend`

SHA256: `3cd4b6414b017223d4be721c4022df361f7d2e83b5b6f0276bc82711838bed75`

Source: `C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-correction-v20/frozen/Mia_FaceCorrection_v20.blend`

Source SHA256: `6794a9b331b7c061e6d75ffc27e9f65d8d31e48971d3f82dd2e98be499b52ed0`

Exact recipe: `exact-recipe.py`, SHA256 `33239f453adbcf45a04ccb6d792a6ea0135e55f8e39f025a1d12d167e9c9dff4`. It equals sibling `../build_orbital.py` at freeze. Required existing helpers are the producer's `tools/mia/blender/refine_mia_head_v06.py` and `asset/mia/blender/mia-face-correction-v20/verify_v20.py` (the latter supplies read-only preview functions). The recipe accepts `--source` and `--output-dir`, refuses an existing output native, and refuses a source already marked with this correction.

## Actual change and preservation

The guide uses the actual evaluated lower orbital rim, a cheek surface ray sample 16 mm below the rim, and a lower cheek surface sample 40 mm below it. A continuous curve defines the affected region. A lid-depth envelope limits forward filling. The field is defined on **Basis**, not the separate mesh coordinate cache. The same per-vertex delta is applied to every relative key and to that cache.

Skin changes are local Y only, maximum 3.812 mm. No skin X/Z scaling occurs. Iris vertices retreat 0.35 mm; their curved shape, material and UV are retained. Non-iris eye vertices follow the local field. Existing lash/wing owners follow and are reseated on the evaluated skin. These are the only six changed mesh owners:

- `MIA_V14_SculptedSkin`
- `MIA_V14_EyeSurface`
- `MIA_V14_UpperLash_-1`, `MIA_V14_UpperLash_1`
- `MIA_V14_OuterWing_-1`, `MIA_V14_OuterWing_1`

Topology, UV layers, weights, object transforms, material assignments and modifiers remain unchanged. All other mesh owners, including the complete Body/headcap and hair, retain their source snapshot. All 47 skin relative-key deltas remain within 3.726e-9 m of source. All 59 packed image byte hashes match source, and every packed image has fake_user enabled. `readonly-freeze-audit.json` is a fresh-process verification; `manifest.json` records the build snapshots and exact hashes. The archive images previously lost in the rejected c13 save are present here.

## Evidence and limits

`before-after-neutral.png` compares actual 6794 and 3cd front, yaw20 and yaw45. Individual saved-native renders include neutral front, both45, profile and beauty front/45/profile. The same neutral rig and orthographic scale 0.29 m, target Z1.55 m are used. `blink_half_front.png` checks inherited Close0.5 after the correction; it is not a final eyelid rig or expression approval.

Anatomically anchored section evidence in `../anatomical-probe/diagnostic.json`: at outer canthus minus4 mm, depth recession from4 to20 mm below the canthus changes 4.980→2.615 mm; first2 mm normal turn changes14.686→12.543°. At canthus plus2 mm, 0→20 mm recession changes12.085→9.071 mm. These support the observed shallower wall; they are not acceptance thresholds or substitutes for the actual images.

The triangular control cage remains uneven, with residual outer-corner sharpness, broad temple/side-plane character, inherited forehead/cap shading seam, and fixed painted crease limitations. The cheek correction does not establish exact reference likeness, final blink compatibility, or mature deformation topology. Previous candidate3/4 and c13/2cd are excluded.

The portrait and expression04 remain reference evidence, not camera-calibrated ground truth. The old view labeled expression04 (yaw−20/roll−9) is only a rough diagnostic and does not match the sheet's image-left facing, more strongly rolled pose. Do not treat that old label as a matched reference camera or use it for exact facial ratios.

## Separate eye-depth causal probes

Sibling `eye-depth-diagnostic/FINDINGS.md` and two comparison sheets document rigid eye-position ±0.5/±1.5 mm and separate depth-scale0.9/1.1 experiments on **6794**, with the face/lids fixed. No native was saved or selected for these probes. Eye depth affects occlusion/white distribution, but the fixed skin wall remains. Advance1.5 mm reveals dark protruding marks above the lid. None of these variants changes the frozen 3cd candidate.

Reviewer decision pending: compare 6794 and 3cd actual surface images before selecting or rejecting the candidate. No further geometry change is included in this handoff.
