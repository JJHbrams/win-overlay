# Mia v27 — adopted face working candidate

Open `native/e9c865412130-Mia_Foundation_v27.blend`. SHA256:
`e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4`.

This replaces user-rejected c04 face geometry/eyes with supported connected cheek volume, revised source-informed eyelid/iris proportions, neutral mouth, shared head/body topology and actual Face-UV pigment. Hair, lower-body art, garments and final events are not completed by this adoption. Read `../REVIEW.md` for actual findings and limits.

## Evidence

- `reference-review.json`: portable source/baseline/candidate package, four matched views, camera/light/pose/display records and hashes. Validator success establishes evidence integrity, not ART acceptance.
- `diagnostics/`: frozen-native matte, intermediate view, three blink values in two angles, Face pigment-only and Face UV checks. Pigment-only replaces material slot0; it is not a full head/body albedo test.
- `rig-proof/`: +/-12 degree head-follow and same-settings whole-body comparison. Full motion and all expression combinations remain unverified.
- `maps/`: actual2048 scene-linear EXR pigment and its rasterization masks/records. Packed active image audit under `provenance/` confirms14 consumed images packed, with no required producer-path external image.
- `../live-v27/`: actual MCP front/both obliques/profile/zoom/body captures from this unchanged native.

## Reconstruct from the preserved baseline

`replay/` contains the compact six-owner library and replay script. In Blender5.2.3, run `replay/replay_face.py` in background mode with `-- --source <absolute path to integration-wip-9-review/Mia_FaceReview_v22_WIP9_M5.blend> --output-dir <new output directory>`. The source SHA is checked before loading. This produces a fresh native without replacing the baseline.

The producer actually executed this replay. `replay-verification/` records exact six-owner keys/topology/rawUV/weights/material-reference/transform fingerprints and exact evaluated coordinate/UV arrays. A saved .blend byte hash can differ because serialization/path differs; data equivalence is the relevant result. The adopted native above remains the directly reviewed file.

Earlier bridge and shared-weight failure variants remain in the producer worktree and are documented in `../PROGRESS.md`; they are not included as competing current natives.
