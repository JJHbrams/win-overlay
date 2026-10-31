# Selective hair pigment experiment

This candidate projects newly authored imagegen paint into the existing MIA_V17_PAINT_UV atlas. It does not reconstruct lost source detail. The generated five-view image is 1536 by 1024 (512 square per panel); the resulting 4096 atlas is a UV storage layout, not 4K unique detail.

Frozen material checkpoint 396840f3 remains unchanged. Geometry, both original and paint UVs, shape keys, transforms, source packed images, face/body materials and auxiliary hair owners are preserved. Only the main Pixal hair material and its shared crown donor material receive the new pigment. The additional procedural Glossy sheen is bypassed on these owners to avoid doubling painted sheen; their physical scene-light diffuse toon response remains active.

Replay in order:
1. Blender background --python-exit-code 1 --python capture_projection.py (read-only capture from checkpoint).
2. Python project_paint.py (visibility/depth weighted UV projection).
3. Blender background --python-exit-code 1 --python build_candidate.py (save new native, fresh reopen, five actual renders).
4. Python build_review_package.py and root validate_reference_review.py.

hair-paintover.png is generated art, NOT a native render. candidate_*.png files are actual Blender renders from the saved candidate. The source crop boards preserve the previous uniform registration and explicitly record oblique-view uncertainty.

Projection rejects skin-like colors and occluded surface samples, blends five views by surface orientation, and falls back to checkpoint pigment for unseen regions. It divides out the captured technical diffuse multiplier, not every artist-painted shadow. This is stylized pigment with painted highlights, not a physical albedo/specular decomposition. Cross-view drift and local projection seams must be reviewed in actual renders. Rear knot shape and braid shape are outside this material experiment and remain unresolved.

Frozen native: `Mia_HairInkPaint_v22.blend`
SHA256: `0d787482198137c37a5fd80067f7f6ce74678c1a99df783b0ece7cb59c5fb319`.

Actual five-view review finds more legible overlap lines and selected crown sheen than checkpoint396, without obvious large skin bleed or a newly opened seam. Fine projected strokes soften across views and lower wisps remain rough. Root specks, braid, rear knot and profile-eye occlusion remain unresolved. This is an improved material experiment, not final character ART approval.

Fresh read-only verification: all160 mesh geometry/UV/weights/shape-key/matrix/visibility signatures identical; all63 original packed image bytes identical; one new packed image; only two expected hair slot owners changed. Native/source files unchanged during verification. All recorded runtime commands exit0. See manifest.json, fresh-preservation.json, projection-provenance.json and five reference-board PNGs.
