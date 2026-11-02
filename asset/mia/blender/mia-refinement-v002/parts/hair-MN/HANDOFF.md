# Hair v002 handoff — bounded challenger, not full ART approval

Current integration challenger: `portable-MN-static/`. It combines F's coherent, skin-safe original-guide pigment; G's two physically connected tapered cut-panel repairs; H's confidence/opacity correction; I's bounded near-ear contact patch; K's measured restrained RGB contrast; and N's cold-bright generated-eye boundary rejection. Optional J/L Head/UpperChest coupling is included as separately selectable data/materials. No full scene snapshot was added.

## Exact entry point and small inputs

Only `apply_bundle_M.py` and the complete `portable-MN-static/` directory are required by the replay API. The loader imports no producer helper, source .blend, body, face, rig, camera, light, or world.

```python
import sys
sys.path.insert(0, r'C:/Users/antio/.codex/worktrees/mia-v002-hair/win-overlay/asset/mia/blender/mia-hair-refine-v002')
import apply_bundle_M
report = apply_bundle_M.apply(
    r'C:/Users/antio/.codex/worktrees/mia-v002-hair/win-overlay/asset/mia/blender/mia-hair-refine-v002/portable-MN-static',
    include_binding=False,  # True selects optional J/L in the same one-time application.
)
```

Apply once to a fresh target whose hair still matches canonical457. Face/body changes in that target are allowed; all hair coordinates, topology, original UVs and semantic weights must match the per-owner preflight guards. Binding requires real neutral Head matrix basis I. Reapplying to an already modified target deliberately fails its source guard; reopen the intended pre-hair target to change the binding selection.

- Loader SHA256: `e51dee54f19e61767c5df3cb4003d9757dcbbb599f372909a2506c52e505b039`.
- Manifest SHA256: `af060a2b35b5f567ea1a8739c19bf68f550e5ce5134b1c5d41bf1ffe65a4c0ef`.
- Material-only library: `hair-materials.blend`, 39,876,910 bytes; SHA256 `a7f92fe5e3aff9678981eb00f79a9604f5d3ddb45f9b7e784196c5caa0c5c80f`.
- Fourteen actor NPZ payloads plus manifest/library and verification reports total49,821,734 bytes at handoff.
- All14 applied actors, including two new tips, receive `mia_component='hair'`. Scope uses explicit ownership and never classifies DentalCrowns by a generic Crown substring.

## What actually passed technical replay

`fresh-replay-verification.json` and `fresh-replay-binding-verification.json` each reopen actual canonical457 and apply the numeric/material library bundle. All14 coordinate arrays match exported targets exactly. Original nonhair objects, all existing material/image data, face/body shape coordinates and values, rig pose, camera, lights, world and scene state have an empty preservation delta. Main remains100383 vertices/120913 polygons with all original UVs and semantic groups; no additional face cleanup or raw bank cut.

Binding replay adds only the declared hair groups/modifiers/carrier. Evaluated neutral world error is at most0.174µm, without double transformation. Source meshes/maps are preserved. This establishes data integrity, not likeness or contact acceptance.

## Actual image evidence

Latest3 actual512 frames are under `reviews/contact-grade-KN-proof/`:

- `GHIN_contact_inMemory-profile.png` — bounded near-ear patch, no palette grade.
- `GHIK_palette_inMemory-front.png`, `GHIK_palette_inMemory-profile.png` — the same geometry with measured K grade and N semantic guard.
- `H-I-KN-profile-board.png` — unmodified image side-by-side comparison.
- `records.json`, `override-recipe.json`, immutable copied helpers — actual pre-render light flags/energy, camera/pose/color state and exact helper versions.

Active lights are actually Key60/Fill15/Rim8; archived lights stay hidden. I does not produce an obvious new profile bulge. K gives a restrained stronger warm-ash/shadow response. These frames are in-memory changes on F, explicitly not mislabeled as a saved MN native. Root's integrated native/source4/head/gaze/critical suite must verify the actual replayed result with current face/body.

Earlier actual source4/back/top/direct-color F context is under `reviews/fineSafe-F-source/paired/`. Original-source crops keep aspect, with frozen common uniform SRT. Nonfront source pose/size uncertainty remains declared. Geometry G production4 and physical-gray baseline/candidate are in `reviews/rim-G-proof/`. H2 is in `reviews/ink-H-proof/`.

## Why these changes, with limits

- Actual packed original main maps are nominal4096². New authored pigment comes from one1254² generated fourview guide, each627² crop; nominal4K original storage is not a new-detail claim. Four new fixed rest-projective UVs and owner/depth/confidence maps are declared. They are attached to the rest mesh and deform with it; they are not active-camera projection. They are deliberately visibility-gated overlapping UVs, not a final unique bake atlas or an export-runtime guarantee.
- C/D micro-island atlas paint remained granular in actual images, even after denser UV construction; rejected. F's projective route reduces that granularity and restores original braid maps. N additionally rejects55 front guide eye-edge/white pixels that escaped warm-skin rejection; no raster is repainted and no new image generation occurs.
- Source clean semantic forelock RGB median[120,109,109] versus H[116,108,107] contradicts blanket darkening. Recorded P10/P50/P90 ranges motivate K's restrained contrast grade before the actual diffuse/light route. ROI coordinates and original images are in `audit/forelock-palette-F-H-source.json`.
- G modifies1887 main vertices, maximum10.56mm, only through physical connectivity to the verified two cut panels. New curved tips supply every inherited UV route and match actual parent root rings. Fine-detail geometry is preserved elsewhere; no generic cap, long-edge eartuck or broad bank cut.
- I modifies456 vertices, maximum6.99mm. The20 originally flagged instances/12 unique near-ear seeds clear to+0.886..+2.116mm signed skin distance. **Twenty-five neighboring pre-existing negatives remain listed**, not automatically labeled intentional roots or passed. No skin/face hole was made.
- All current original hair was actually static while Head moved. J makes Head follow neutral-preserving, but rigid long hair creates large contact alarms. L gives hanging waves/side locks/braid bounded Head→UpperChest skinning, while crown/fringe/bun remain Head-driven. Both new tip seams stay below1µm across CPU probes.
- L lower-hair new nearest-skin alarms: yaw+8°2429→145, P04689→19, P06412→11, P10897→22. Signed nearest distances are inspection alarms, not confirmed visible intersections or a contact PASS. P04[-3,-22,18], P06[-6,-18,15], P10[0,0,14] are root's current source-pose estimates; Neck/Chest stay unchanged. Root will inspect actual integrated poses rather than repeat an isolated6frame batch here.
- Skinned L actors use actual deformed geometric normals because original OBJECT-space map directions would stay in undeformed object axes. Pure Head-parented actors keep their original normal-map route. Original maps/graphs remain archived. Pose lighting must be verified in the integrated suite.

## Still open — do not claim full hair completion

Broad eye-occluding forelocks, blocky crown stubs/inner pits, jagged ear/nape fragments, weak source-style thin ink hierarchy, ambiguous hidden roots, current-body pose contact and later coherent strand chains remain open. There is no full hair ART PASS, no all-clipping PASS, no whole-hair physics, final unique atlas/export bake or30fps animation approval. The parent owns canonical/live/Git integration; this agent made none.

Native cache remains the verified D junction with E/F only. Cleanup/deletion ledgers preserve exact authorization/scope; all scripts, artwork, maps, NPZ, PNG, logs and failure history remain. GPU has been released to the parent; no more isolated rendering is queued here.
