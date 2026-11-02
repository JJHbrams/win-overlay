# Mia v003 rear hair — working readout

Canonical source is packed R3b (`4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`). This folder contains portable candidates and actual diagnostic evidence, not a final hair ART PASS. Root owns native integration/Git/live Blender; none of those were changed here.

## What actually caused the regression

Retained v29 and R3b orbit records have exactly equal camera matrices, ortho scale, source three-light fixture, color management and neutral pose for 000/009/012/015/018. Historical v29 geometry and shaders differ, so their screenshots alone do not isolate a cause. Current Main pigment-only and gray diagnostics do:

- Slate Crown sectors are incomplete pigment coverage/fallback, rather than a collapsed cap.
- Broken dark strokes remain in pigment-only mode; artistic guide errors are not certified by depth/owner confidence.
- Torn/folded lower rear sheets also remain in actual gray. They require geometry work independently of paint.
- v29 used a static ash/strand/overlay paint chain plus a view-dependent Fresnel/object-normal/light chain. Only the STATIC pigment was recovered; stale normals, geometry and lighting were not replayed.

## Candidate ledger

| Candidate | Actual evidence | Current status |
| --- | --- | --- |
| Geometry A: five central closed rear locks | Three paired gray angles | Bounded featureless-V improvement only; not in production replay |
| Geometry B: varied central locks + 0.6 mm edge fairing | Three paired gray angles + original-aspect source back | Central improvement provisional; not in production replay; fairing does not fix torn sides |
| Geometry C: eleven locks + exact reversible underlayer mask | Eight actual gray frames including front/profile/high/low | **HELD**: repetitive smooth ribbons and remaining torn side/lower U loop |
| Live static v29 fallback graph | CPU guard passed; ten frames written | **REJECTED**: EEVEE explicitly reported too many attributes; candidate PNGs invalid despite normal process completion |
| One-image static fallback recovery | Full guard + error-free actual018 | Useful slate-sector coverage recovery; current dark guide strokes intentionally remain |
| Conservative rear-guide art challenger | Full guard + error-free actual018 | **HELD**: front-visible Crown protection also holds much of the opposite-profile slate sector; standalone challenger partly restores old gray fallback and does not fix held-front strokes |
| Color A+B: static fallback base + conservative rear-guide override | Full guard and four error-free actual000/006/012/018 views | **Root provisionally selected bounded COLOR checkpoint**, not geometry A/B/C or whole-hair ART |

The rejected live-graph render folder has an explicit `VALIDITY.json`. Never adopt its candidate images or infer success from `Saved:`/exit0.

The selected replay is only `apply_baked_v29_crown.apply(..., mode="combined")`. Geometric prototypes with the same A/B lettering are separate failed/incomplete studies and are not silently included. `HANDOFF.md` and `SELECTED_CHECKPOINT.json` identify the exact production files and remaining integration source gate.

## Exact texture recovery

All4999 pure-Crown target triangles matched v29 by source polygon ID AND exact raw vertex IDs. All original `MIA_V17_PAINT_UV` corners are byte-identical. The old generated alpha overlay alone covers only13% of slate-core samples; recovering that image alone was insufficient. Twelve whitelisted static pigment nodes/three retained packed images supplied the ash palette, red/green authored strand signals and overlay. No geometry, BSDF, Fresnel or normal nodes entered the numeric bake.

Original UV has four measured overlap pairs and only1.204% atlas coverage for this Crown, median35texels/triangle at4096. A unique geometric strip UV was therefore prepared on a proxy. Its first unwrap was positive but had179 global self-overlaps;77 tiny local-return UV cuts (0.39% physical area) removed those. Final4999 triangles are float32-positive, overlap0, anisotropy median1.054/P901.265. The335 slate-core faces in the pure-Crown layer have median1.047/P901.168/max2.04;24 mixed Side_Nape/Roots diagnostic edge faces remain on their existing route.

The initial data-guide blue→orange palette confused orange rim fill with the red anisotropy legend. It was corrected to blue→teal with magenta metric outlines, using current UV payload SHA. Fifty faces exceed anisotropy8, accounting for0.178% physical area. These are UV data, not new artwork or source-grooming approval.

`RecoveredStaticCrown_4096_RGBA.png` is a numerical existing-pigment remap. RGB is old static art; alpha is a4mm physical boundary fade. All4999 faces are sampled; one subtexel triangle receives a numeric centroid sample. Boundary bilinear alpha is exactly0 at84,196 samples. Interior remap error median0.00042/P900.00123 linear; seam tails remain at tiny UV tips/border support and require actual inspection (P990.014/max0.135). Current live guide is not baked.

`apply_baked_v29_crown.py` appends one UV/material and no POINT fields. All six original UVs, coordinates, topology, weights, original material graphs, keys and actual corner normals remain exact. The copied current shader keeps current K/light/actual-normal routes. Fourteen logical streams are only a diagnostic count: actual successful compiler probes are required and recorded.

## Remaining geometry ownership

`rear-relief-C/remaining-firsthit.json` excludes the2624 transparent replacement triangles, so probes reflect what was actually visible:

- Torn side transition: Main pure Rear_Waves, e.g. source IDs157731/155537/162819/162858, worldX≈0.085–0.097,Y≈0.078–0.096,Z≈1.43–1.475.
- Lower U loop: Main Rear_Waves+Loose_Tips, e.g. source IDs93498/82771, worldZ≈1.315–1.333, outside C's lower replacement extent.
- Some apparent central openings expose actual body. They must not be covered by arbitrary planar fills.

Next geometry design must trace individual source paths/widths/layers and replace coherent whole locks with rooted overlap/closed volume; repeated S cushions or masking a few exposed triangles leave cut remnants. Preserve front/true forelocks/bun and buried P banks. Head/UpperChest weights are not a physics/collision proof; actual head/neck/shoulder poses and high/low/orbit checks remain required.

Right braid source-form cleanup is **required but deferred until face/body gate**, not discarded. No braid edits were made. Eyebrow/fringe visibility is owned by the separate facial agent.

## Relevant evidence

- `v29-hair-ancestry.json`: retained native/static ancestry and historical fixture comparison.
- `rear-diagnostic/`: actual gray vs Main pigment-only, fixed source lights.
- `rear-relief-B/source-back-A-B.png`, `rear-relief-C/source-B-C.png`: source crop/uniform scaling only, no aspect/feature warp.
- `v29-pigment/baked-probe/baseline-v29-recovery-018.png`: actual historical/current/recovery comparison.
- `v29-pigment/rear-guide-probe/`: conservative rear challenger actual018.
- `v29-pigment/*CPU-guard.json`, `baked-seam-audit.json`, `baked-report.json`: technical preservation and numeric limits, not ART certification.
