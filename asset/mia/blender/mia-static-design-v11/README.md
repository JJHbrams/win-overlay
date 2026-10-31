# Mia static detailed-hair v11

**Status: ART FAIL / static study, not a replacement for the preserved body-head checkpoint (its face art is also unapproved).**

Base: v09 rather than v10, preserving its complete Face44, eyes/mouth material islands, approved body and existing rig. No new rig, weights, motion or pose tests were authored. Face/forehead/neck/body polygons were not removed.

## Part ownership

- Detailed v07 source: separate Bangs, CrownAndCheekLocks, and Rear meshes; retained UV and original material. Hair-owned warm/light and lateral contamination was filtered.
- Scalp Front/Rear: new separate support copies of existing skin regions; original skin remains complete.
- One left braid and half-up knot: separate parts reused from the original HairSurface source.
- Eyes/mouth remain on the preserved Face44 master as original material-owned islands. They were not silently split or fused into the hair.

## Actual result and limits

Five actual-color views were rendered after reopening the saved native. Upper messy cheek curls and flyaways are more faithful than v10 ribbons. The study still fails art review: rear scalp exposure and nape separation remain; the elongated lower cut source reads as a flat-ended curtain. The separate braid/knot also have flatter shading than the detailed hair. These failures are visible in back/profile views; no skin cuts conceal them.

The bounded study is frozen. Reusing the upper detailed hair is promising; the lower source needs actual reconstruction of the nape-to-wave transition, rather than more stretch-fitting.

## Reproduce

Run Blender background with `--python tools/mia/blender/build_mia_static_detailed_hair_v11.py`. Repository paths resolve from the recipe location. The original HairSurface source retains its explicit external path; it is read-only. Final execution exit code: 0.

## Hashes

Recipe hashes below describe the actual executed working bytes. Git normalizes CRLF to LF; `code-provenance.json` records both hashes. Native/render binaries are unchanged by that normalization.

- Native: `02f8f8acaf074e9c61b8f4ed9200f7e8c9d6c1e5389c107adcf95d9c9df79ffc`
- Recipe: `fcf41d275deb83c06074832a089e10f7bc7f8b657a2e7b4917e4e2873dc057f3`
- Source `C:\Users\antio\.codex\worktrees\mia-head-refine-v06\win-overlay\asset\mia\blender\mia-head-refine-v06\astra-v09\Mia_Astra_Head_v09.blend`: `63523417f451b5bc193d6cb2ef8940f4a0004f0db0e89f713d01f486cb408232` (before/after identical).
- Source `C:\Users\antio\.codex\worktrees\mia-head-refine-v06\win-overlay\asset\mia\blender\mia-production-stage2-face\v07\Mia_ReusedFoundation_DetailedHair.blend`: `afb4cb651da32c678ae6a69f3ee988a502e09611d69640b5146dd28c22ccd1f2` (before/after identical).
- Source `D:\ai\Mia3DWork\model-v02\hair-surface-stage\Mia_HairSurface_v06.blend`: `9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6` (before/after identical).
