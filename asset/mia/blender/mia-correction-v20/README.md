# Mia correction checkpoint — partial, not an approved character

Current selected native: `integrated-r2/Mia_Corrected_v20.blend`, SHA-256 `c02b8ad73b86b278f2768e61eff019be223a8828bd92df62ce0ab7cb60f56936`.
The previous integrated native `aa02b736…` remains immutable under `integrated/`.

## Applied changes

- Face: the independently reviewed `3cd4b641…` orbital guide fills the abrupt outer-eye-to-upper-cheek recess while retaining the face outline and iris design. It replaces first-pass face6794. Full likeness, temple/cap shading, final facial deformation and paint remain unfinished. The prior c13 width-reduction candidate steepened the wall and is excluded.
- Hair: `83c0df5e…` retains Pixal source polygons and both UVs while correcting selected rear/lateral tips and restoring coincident UV-split boundary positions. Body and the rest of the face retain their respective producers' scope.
- Body: original first-pass `8e262b27…` corrections remain. All later underside, loop and primary-form experiments were rejected. None of those rejected body changes is in the selected native.

The integrator verifies body topology/UV/weight invariants, protects face/headcap and other owners, transfers only body coordinates below Z1.46, and preserves the exact hair geometry/UV/source visibility. Its frozen exact recipe and source hashes are next to each integrated native. These are technical checks, not art approval.

## Latest user concerns and decisions

**Body form:** Body Foundation front/profile are construction references. The body still needs a coherent chest-to-breast primary form; protected vertex IDs or an unchanged apex do not justify retaining a bad shape. Rejected v21 studies included a corrected left/right mapping bug, but the subsequent art review still rejected the shelf/perimeter seam/isolated outer volume. Evidence and independent verdicts are under `evidence/body-form-v21-rejected` and `evidence/body-primary-rejected`.

**Outfit-dependent form:** Our proposed design is a preserved continuous body plus outfit-specific corrective shapes and reversible hidden-skin masks. A separately replaceable breast patch is possible but is not assumed to be a mandatory or universal production method; it adds visible-boundary, normal and deformation coordination. Official [VRoid skin-mask documentation](https://vroid.pixiv.help/hc/en-us/articles/4405516267033-How-to-use-Skin-Masks) supports retaining the underlying body while hiding covered skin. [Blender shape-key documentation](https://docs.blender.org/manual/en/5.4/animation/shape_keys/introduction.html) describes soft-form/corrective deformation; this is design rationale, not a claim that outfit morphs are already authored. [Proko's public Form & Motion notes](https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/) informed the gradual pectoral/axillary transition. No tutorial video or premium content was claimed as watched.

**Eye depth:** On face6794, separate diagnostic eye translations ±0.5/±1.5 mm and depth scale0.9/1.1 change sclera exposure and lid contact but leave the fixed skin wall. Advance1.5 mm produces a visible protruding line. Thus eye depth matters for contact but does not alone explain the observed cheekwall. These probe variants were not saved as selected natives. The actual eye consists of open curved sclera/iris surfaces, not a closed sphere. The selected face guide includes only a0.35 mm iris retreat alongside the coordinated cheek correction. See `evidence/face-orbital-v21/eye-depth-diagnostic/FINDINGS.md` and the separate curvature panel.

**Rear gathered hair:** The concept feature is rolled/gathered hair, not a tie or ribbon. The bulb and rolled-tube replacements were rejected; their renders are preserved in `evidence/hair-rejected`. The chosen native still has an unresolved rear gathering feature. Sparse original-surface rays found central scalp surface, but this does not certify a watertight hair shell or reference-complete finishing volume.

**Hair texture:** The active4096 atlas is an EMIT rebake of a2048 original, not newly painted high-frequency detail. Measured area-weighted density supports insufficient source detail in close views; coarse geometry/baked marks also contribute. Simply increasing the container to8K would not restore absent information. No texture-resolution repair is claimed. Exact density definitions and limits are preserved in `evidence/hair-rejected/candidate-bundle/TEXTURE_READONLY.md`.

## Verification and recovery

- `fresh-review-r2/review-evidence.json`:19 fresh saved-native views with fixed camera, pose, light-mode and color-management records. No native save during review.
- `comparison-r2`: same-view first-pass vs additional-correction contact sheets, uniform sizing only.
- `live-mcp-r2`: actual installed Blender MCP preview; source hash must remain unchanged.
- `acceptance-round-1.md`, `acceptance-round-2.md` and per-part independent verdicts: art failures remain explicit. Full character completion, garments and final event motion are not approved.
- Cleanup: `../../WORKTREE_ARCHIVE.md` documents7 preserved inactive worktrees and exact recovery mapping. Existing working/canonical workspaces remain.

Remote checkpoints96761ba andfc61e0c preserve the first integrated WIP and repaired hair source respectively. This checkpoint adds the selected correction and the rejected experiments' evidence; a Git checkpoint is not art acceptance.
