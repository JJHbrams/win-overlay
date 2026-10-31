# Face finish5: local under-eye pigment A/B

Frozen candidate; LOCAL WIP only. Face likeness/geometry remains FAIL. No further strength increase.

Cause: existing fixed source registration showed under-eye pigment too close in display value to adjacent cheek in front and oblique. Iris/skin width or lash edits were not justified by this local comparison. This change adds only a fixed-original-UV brown/mauve crescent following the actual evaluated lower-lid boundary.

Native: Mia_FaceFinish5_v22.blend
SHA256: a5ec86e9fab19fe0e62b9208f48a146760fc758cb42c7e13977d1573f29ffbbb
Source: ../finish-4/Mia_FaceFinish_v22.blend
SHA256: 9d2c9d42c01c99f0138bb9227e3679ce3afa882d2f43c339ab26496c4c559a4b

## Actual material change

Only MIA_V14_SculptedSkin slot7 assigned a copied material MIA_V22_Finish5_LocalUnderEye. Original UVMap -> lower-lid V(U) and approximate evaluated meters/UV ramps -> narrow distance band and canthus taper -> local pigment blend -> existing PigmentTimesControlledLight input1. Multiplier (.72,.62,.66) is scene-linear shader color control, NOT a measured reflectance. Strong band 2.16–3.60mm below rim; feather support approximately .78–5.28mm. Surface metric is a sampled UV derivative, not exact geodesic distance.

No new raster or atlas edits. Full original albedo and actual scene-light response remain. Geometry, keys, UVs, weights, iris, lashes, nose/mouth, hair and Body assignment unchanged. Source69 packed images retain exact bytes and fake_user. All nonreplaced material node graphs/socket values, lights/world/display match saved source. Replaced former skin material became zero-user and is absent in candidate; its complete source remains immutable in face4. No other material removed.

## Actual observation

Four SOURCE ART | FACE4 | FINISH5 hair-on boards and bare front/oblique A/B were inspected. Narrow crescent improves local tired-eye impression, without visible sclera spill or whole-cheek haze. It is still smoother/narrower and lighter than source. Profile yaw80 is hair-occluded and cannot establish under-eye agreement. Broad midface/temple and jaw/nose/mouth identity gaps remain unchanged.

The same oblique 9x9 ROI display-luma ratio becomes 1.010 -> .839 (source .563). The prior front ROI is just outside the narrow mask core: .976 -> .968 (source .659), NOT a target pass there. The explicit front vertical scan through the mask center gives .783–.840 at y290–296. Full locations/ranges are in display-contrast-measurements.json. Values are encoded RGB display contrast, not physical reflectance; source lighting/drawing/pose differ. No per-feature or anisotropic registration was used.

## Replay and provenance

build_under_eye.py is the exact executed build recipe; its recorded hash in manifest.json is unchanged. lowerlid-uv.json records fixed face4 evaluated rim anchors. inspect_lowerlid_uv.py is their read-only extraction recipe. replay_under_eye.py differs ONLY by using the archived dependency path dependencies/legacy_snapshot_apply_interp.py instead of prior finish4/replay path. --source and --output-dir are supported. Output path must be new; existing native will not be overwritten. Apply once onto a face4-compatible skin UV/shape. Do not replay onto finish5 itself or independently changed eyelid topology/UV without review. Root integrated body/hair can differ while the face4 skin remains compatible.

Blender command:
`blender.exe --background --python replay_under_eye.py -- --source ABSOLUTE_INPUT.blend --output-dir NEW_OUTPUT_DIRECTORY`

Native saved/reopened preservation assertions are in manifest.json and preservation-audit.json. Root evidence gate validates reference-review.json but does not grant art acceptance. No expression/animation pass is claimed. Earlier inherited blink concerns are unchanged; this material-only task introduces no rig edits.
