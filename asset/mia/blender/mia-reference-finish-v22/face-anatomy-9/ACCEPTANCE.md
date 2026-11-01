# Face anatomy correction contract

User request: study how artists construct the human face before continuing face sculpting. Previous WIP8 cheek fill did not resolve the orbital/malar/maxillary transition. This work owns face structure only; the wider static-finish request remains incomplete.

## Latest user correction supersedes feature locks

The user explicitly identified broad/short face proportions, abrupt cheek-to-pointed-chin taper, wrong upper-outer and lower eyelid curves, and weak/missing source-style eye makeup. A cheek-only correction with frozen jaw/eye geometry does not meet this request. Preserve original assets, not their erroneous positions. The prior AC3/AC4 feature-position locks below are superseded by this section.

Execution order: whole face proportions and cheek/jaw/chin together; eye aperture/upper-outer and lower lid/iris/lash contact together; then fatigue/makeup/line appearance. Check the form without pigment before judging the final look.

Additional critical outcomes:

- AC0: eye-spacing-normalized source/raw-render comparison must expose eye-to-chin height and gradual jaw taper. Do not normalize away the dimension being tested. Source roll/hair/pose uncertainty remains. Manual eye landmarks are estimates, not an exact percentage prescription.
- AC3 revised: correct jaw/eye shapes toward source identity; preserve technical coherence rather than exact wrong feature positions. Source front/profile/both obliques and subtle expression angle must be inspected. A frontal-only warp is insufficient.
- AC4 revised: permit coordinated skin/eye/lash/mouth/jaw-line changes when needed for the corrected shape. Verify UV/keys/contact after the change; exact unchanged coordinates are not a requirement. Non-face body/hair and originals remain protected.
- AC5: apply source-like layered undereye pigment and lines after the shape pass; actual color-only and lit views must show the intended impression. Existing map connectivity is not visual completion.

Current A1/A2/A3 tests are unselected. A3b is only a target proxy, not a new face. Continue from original WIP8 and the new whole-face criteria.

Baseline: `../integration-wip-8-review/Mia_ReferenceFinish_v22.blend`, SHA256 `ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4`. Preserve it. Render geometry evidence from actual Blender, not image generation.

## Acceptance criteria

| id | criterion | user_visible_outcome | intended_runtime | verification | evidence | critical |
|---|---|---|---|---|---|---|
| AC1 | Diagnose orbit, zygoma, maxillary/mouth mass, cheek and jaw relationships; distinguish pigment/light from geometry. | A concrete structural explanation of the sunken/creased cheek. | Blender evaluated neutral surface | Bare matte and opposite-light comparisons, inspect topology/actual coordinates, relate to creator primary-source text. | SOURCES.md, DIAGNOSIS.md, actual baseline images | true |
| AC2 | Restore broad anatomical transitions without flattening malar support or inflating isolated spherical cheeks. | Undereye/front/side cheek read as one coherent form while rotating. | Actual saved candidate | Front, both obliques, profile, low and intermediate angles; matte first, then native look. | Paired actual renders and independent visual judgments | true |
| AC3 | Preserve Mia identity across source front/profile/both obliques. | No isolated view improvement at the cost of eye/mouth/silhouette regression. | Fixed Blender cameras and original uniform source SRT | Source/baseline/candidate boards; pose/crop/normalization uncertainty retained. | Valid reference-review.json plus actual visual review | true |
| AC4 | Bound edits to face and protect eye/mouth contact, UV, materials, topology, relative deformation and all non-face owners. | No new clipping, pigment shift or unrelated body/hair change. | Saved Blender native, neutral and limited blink/mouth probes | Actual delta/owner/UV/key/material audit and rendered probes; list untested expressions. | Guard report, save/reopen images, limited deformation evidence | true |

## Implementation and ownership

Root owns canonical documentation, live Blender and integration. Face producer owns only a new `asset/mia/blender/mia-face-anatomy-v25` directory in its separate worktree. Research/planning and independent review are read-only. Do not modify original natives or erase failed candidates. The working hypothesis must not become a fixed numerical target without actual form review.

## Research applied

- Uldis Zarins / Anatomy for Sculptors: https://anatomy4sculptors.com/blog/forming-the-head-simple-to-complex/ — actual public full text read 2026-11-01; no full video viewed or timestamps. Foundation/primary transitions before cheek-pad/undereye secondary forms; anatomy explains relationships, not Mia's exact proportions.
- Marco Bucci / Proko: https://www.proko.com/lesson/painting-the-head-from-imagination-lighting-without-reference-with-marco-bucci — actual public Lesson Notes read 2026-11-01; video not viewed. Orbit-to-zygoma-to-front/side-cheek-to-jaw planes and mouth mass; light tests expose their direction. Painting source, not a Blender rig prescription.
- Scott Eaton old PDF returned404; exclude as verified body text. Course descriptions are not watched tutorials.

No material scope reduction is authorized. A failed form candidate stays unselected and the acceptance report remains FAIL/UNVERIFIED; technical preservation cannot replace art acceptance.
