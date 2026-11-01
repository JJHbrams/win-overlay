# v27 reconstruction review

The c04/WIP9+M5 face is user-rejected. Its sunken front/malar cheek, E2 eyes and local Q9 gains are not an accepted target. The source-art roles remain those in ACCEPTANCE.md.

## Actual reviewed improvements

- Pristine hidden Face was inspected as a neutral foundation, not accepted as Mia. Its supported anterior-to-side cheek supplied a coherent starting volume; original smiling mouth, round eyes and donor colors were replaced.
- Connected primary-form work retains anterior cheek support while narrowing the outer lower face. Root and independent visual review saw removal of the old triangular hollow and abrupt cheek/jaw notch across front, oblique and low-front views.
- The actual mouth aperture, lip roll and cavity were corrected together. A fitted downturned seam alone had still rendered as a smile and was rejected.
- R2 actual canthal span, iris carrier and upper ink were compared with the source at a common eye-spacing scale. Manual estimates below have antialiasing, visible-boundary, hair and pose uncertainty; they are not exact anatomical measurements.

| Visible measure / IPD | Source | R1 rejected eye proportions | R2 retained locally |
|---|---:|---:|---:|
| Eye aperture width | .56–.60 | .45–.47 | about .57 |
| Visible colored iris width | .29–.32 | .39–.43 | .31–.33 |
| Upper black core thickness | .053–.068 | .026–.030 | .052–.056 |

R2 preserves current eye height and centers. Half/full blink was actually viewed at front and oblique; full closure showed no obvious exposed iris/sclera. This does not certify all42 keys, combinations, unilateral blinks, intermediate frames or final motion rigging. R3 separately addresses tiny ribbon triangle-interior pinholes.

## UV and material evidence

The welded skin preserves per-corner UVs, including38 duplicate-coordinate groups whose UV corners differ. Original coincident coordinate groups agree across all42 keys and vertex weights; averaging those UVs would have been destructive.

New2048 scene-linear EXR pigment is rasterized onto actual current skin UV triangles, using actual eyelid positions. The connected material route is UVMap → V27_ACTUAL_UV_PIGMENT → PigmentTimesControlledLight → controlled-light Emission. It is not an unused image node or copied old M5 coordinate field. Makeup is reviewed separately from bare matte geometry. No completed PBR specular/normal-map set is claimed.

## Head-connection failures retained as evidence

Nearest-surface matching was not boundary matching: F3 targets included Body-interior points and reversed correspondence. Later ordered bridges closed the positional gap and matched corner normals but retained actual folded geometry. R2 had93/304 foldback tests; R3 reduced this to24, all at cap/ear regions, with none at chin. R4 introduced a ridge, and R5 still left a visible seam in matte profile. These are rejected connection variants.

Body raw/evaluated custom normals are absent. Geometry-derived and actual corner normals agree; a stale-normal diagnosis was explicitly withdrawn. The head connection is being rebuilt with shared topology rather than more isolated bridge coefficients. Body Armature→Weld→Subdivision→Smooth must be included in the coordinate/evaluation analysis. Head-cap/upper-neck edits are allowed; lower-body preservation is verified separately.

## Frozen native structural audit

Final inspection native SHA `e9c8654121307b61fb75d73789c9b2443a3e42c53420dfdfada927d194b475d4` uses a genuinely shared38-control boundary: new `MIA_V27_SharedHeadBody` contains the connected skin and original Body prefix. Source originals remain archived. The earlier shared draft7ae354 is explicitly rejected: numeric vertex-group copying shifted Body weights. The corrected native copies by group name and the independent audit verifies zero mismatches over3957 original Body vertices.

Original nonboundary Body coordinates agree exactly over all42keys, and both UV-layer prefixes agree exactly. Evaluated lower-body vertices below z1.35/1.4 have matching counts56927/60135 and bidirectional nearest maximum0.000357628mm. This is floating-point-level evaluation agreement, not bitwise equality. Changes greater than1µm are bounded above z1.460778m. Rest-space head-weight material blending reaches z1.3936m and is recorded separately from geometry.

Feature master and all four boundary ribbons now have enabled Armature modifiers targeting MIA_V06_RIG. Master weights target Head or its descendants, without unweighted vertices. Each ribbon is fully Head-weighted. This resolves static features being left behind when the head bone moves, but does not certify the final animation set. The new native retains thin lip/nostril marks rasterized on the separate Face UV domain before joining; overlapping Body UV islands were not painted into the face map.

## Acceptance boundary

The frozen shared-head candidate is adopted as the current face working version. Independent final image review inspected source4, actual neutral/half/full blink, bare profile/low/oblique, UV and pigment-only views. It supports retained eye ratios/front-cheek support, removal of the cap/neck geometric seam and ribbon pinholes, and actual thin lip/nostril paint. Root also inspected source boards and actual live front/zoom/profile/body captures. The canonical archive's strict reference package is valid, and actual MCP opened this exact unchanged SHA with head-centered orthographic navigation and explicit visible owner. Six captures and their hashes are in `live-v27/live-review.json`.

The remaining source differences are under-eye line work, blush, outer upper-lid expression and nasal plane shading. There is no current evidence to justify hollowing the supported cheek again. `color_only` replaces Face material slot0 only: it is a face pigment diagnostic, not whole-head/body albedo-continuity proof. UV review is likewise visual Face-domain inspection. Blink evidence is three values at two angles; +/-12degree rigid head follow is a limited coupling check. Neither covers every expression, blend, action or simulation.

Native hashes, saved keys, valid evidence packages and render counts do not grant ART PASS. Body proportions/UV, rough hair extraction boundaries and bun/art fidelity, garments and full event animation remain unfinished independently.
