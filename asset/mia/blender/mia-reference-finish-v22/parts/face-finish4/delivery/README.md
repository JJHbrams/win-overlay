# Mia face finish v22 — frozen candidate, independent art review required

The c02 face had a low nasal point, projected philtrum/muzzle, a nearly horizontal chin underside, weak source-style pigment and an iris whose upper-tone UV range was mostly hidden by the lid. This candidate changes the connected nasal/philtrum/jaw profile, broadens the curved eye presentation, restores a real tapered lash ribbon, and replaces the inherited face paint with a new fixed UV albedo under the common scene-light contract.

It is **not a full reference-likeness or animation PASS**. Front/profile/oblique source boards show improvement and remaining differences directly.

## Frozen native and source

- Candidate: `Mia_FaceFinish_v22.blend`
- SHA256: `9d2c9d42c01c99f0138bb9227e3679ce3afa882d2f43c339ab26496c4c559a4b`
- Immutable c02 source: `C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend`
- Source SHA256: `c02b8ad73b86b278f2768e61eff019be223a8828bd92df62ce0ab7cb60f56936`
- `delivery-manifest.json` records exact phase natives, source artwork, maps, recipes and dependencies. `REPLAY.ps1` gives the four replay steps into a fresh directory. `.blend` serialization hashes are identity records, not a claim of byte-identical reserialization.
- `../finish-3` remains frozen at `6fdba62420f6ea80f4cfa04a94d16c52929403ddccf83a017263f851c6b39a74`. Finish4 changes only surface materials/maps; all its coordinates, topology, UVs, keys and weights match finish3.

## Actual changes and scope

The geometry recipe uses **actual Basis coordinates**, applies identical per-vertex offsets to every relative key and separately to the vertex cache, then inspects reopened/evaluated neutral geometry. It does not infer neutral geometry from a stale cache.

- Connected nasal profile: nasal apex lift 2.2mm, local depth redistribution through bridge/tip/philtrum; limited normal fairing to soften the knife-like initial trial. Nose tip is not globally flattened.
- Posterior chin underside rises locally. The corresponding Body headcap boundary uses the same local field to maintain the join. No global head scale/height change.
- Eye aperture field scales local X/Y by up to8%; complete curved iris carrier X/Y by10%, retaining curvature and culling; gray UV radius+4%, pupil radius .285→.215. These are actual recipe factors, not claimed screen-space proportion matches.
- Four visible upper-lash/outer-wing owners follow the moved skin and gain a tapered central ribbon thickness of1.35mm. The same offsets preserve their existing relative Close follower deltas.
- Iris has darker visible upper tone, a small vertical pupil, gray limbal rim and a restrained lower reflected arc. It remains a static curved carrier with UV shader art, not a full spherical eyeball or new final eye rig.
- Only seven mesh owners change from c02: visible skin, EyeSurface, four lash/wing objects, and Body headcap. Hair and all other mesh snapshots remain exact. Body slot0 material is additionally replaced with the authorized common skin helper.

`body-headcap-deltas.json` contains **21 explicit Body vertex IDs/local offsets**. Merge these into the original Basis/key coordinates alongside the other producer's lower-body changes; do not replace the whole Body mesh with this producer's Body.

Important scope caveat: all3723 Body Basis vertices with source worldZ<1.46 remain exactly unchanged. Subdivision propagates the upper edit into194 evaluated vertices below1.46 by more than1µm, with maximum1.277mm, over source worldZ1.4313–1.45997. This is explicitly disclosed for integration review.

## Actual UV maps and lighting

- `Face_BaseColor_LINEAR_2048.exr`: active packed2048² float **scene-linear full albedo**, Non-Color. Explicit original skin UVMap, camera-independent at runtime.
- `Face_BaseColor_sRGB_2048.png`: sRGB-encoded visual/export counterpart. Decode once when using it as a color texture.
- `Face_PaintRegion_MASK_2048.png`: scalar transfer coverage, not roughness/specular/AO.
- `actual_front_skin_visibility.png`: actual geometry/occluder mask used for projection. Eye whites/blue-gray carrier pixels are excluded; warm brown/mauve pigment is retained.
- Source `../paint-source/source-v3-not-model-render.png` is **imagegen artwork, not a model render**. Built-in imagegen made the source and a bounded under-eye edit; exact prompts and original PNG bytes are preserved. Python/Blender performs technical UV rasterization/color conversion/padding only.
- Original source art is not resampled in place. Local sample offsets align mouth−.006V and eye region−.007V to the registered geometry. The atlas fades to common base on lateral skin, ear/headcap/neck boundaries. Eight-pixel technical UV padding is used.
- No old beauty ratio or baked gloss is remultiplied. One global neutral-color calibration maps the flat source plate base to shared linear(.92,.69,.60). New face full albedo directly multiplies the shared actual Diffuse luminance ramp. Body legacy pigment is divided by its legacy neutral before the shared base/ramp.
- Root shared ramp uses actual white-Diffuse luminance/4, EASE stops at light signals .10/.70/2.20/3.80. Standard/None, exposure0, gamma1. `actual-material-route.json` records active datablock/node bindings.
- No new specular/roughness/normal maps were fabricated. This is a toon diffuse/pigment workflow. Iris art is procedural in UV coordinates and is disclosed as such.

## Source evidence and limitations

`source-review-hair/` and `source-review/` each contain SOURCE ART | c02 BASELINE | CANDIDATE boards for front, matched side, expression04 left oblique and expression03 opposite subtle angle. Exact paths/hashes/crops/camera matrices/pose uncertainty and uniform SRTs are in `reference-review-hair.json` and `reference-review.json`. Both validators report evidence_valid=true, art_acceptance=NOT_EVALUATED.

All before/after images use identical camera/light/display records. Baseline retains its old fixed-normal skin shader; candidate uses the new actual-light skin contract, so these are combined form/surface comparisons. Eye-to-chin distance and in-plane orientation are normalized by baseline anchors; they are **not independently validated proportions**. The same SRT applies to the candidate. There is no anisotropic/per-feature image warp. SIDE is low-resolution and stylized; opposite expression03 is not confirmed−45° ground truth.

Earlier trial boards had a camera roll sign issue. Final `baseline-common-rollfixed` and finish3/finish4 fresh review renders use the corrected sign and matching explicit camera matrices. The geometry and frontal paint calibration were unaffected.

`renders/` includes actual front0,±45,90 profile, hair-on source views, color-only front/45, actual UV checker front/45 and Close0.5. Fresh native hash is unchanged after rendering. The UV checker shows inherited compression around eyes/nose and uneven density; UV preservation is not a claim of optimal unwrap.

Remaining visible limits: broad temple/side plane and upper cap tangent/shading seam, flatter/less graphic eye styling than source, scratchy brows, under-eye line/pale waterline registration, weak drawn face outline and static pigment. Close0.5 already nearly shuts the aperture and the lash band is thick; no final blink/smile/rig pass. The uneven triangular control cage remains unfinished for mature deformation.

`preservation-audit.json`: all source61 packed images byte-exact (the prior59 archive plus2 later images); candidate69 packed images all fake-user. All mesh UV/topology/weights/matrices/modifiers exact. Maximum relative-key delta error7.45e-9m. Evaluated face/headcap join median0.00013mm, maximum1.926→1.963mm; this nearest-distance metric does not validate tangent continuity.

No source native, source artwork, hair geometry, prior candidate, or other agent file was overwritten. Root owns integration and final independent art judgment.
