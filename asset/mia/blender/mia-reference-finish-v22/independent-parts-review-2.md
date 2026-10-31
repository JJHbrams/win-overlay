# Parts review after resume, 2026-11-01

These judgments are based on actual source-paired renders, not package validation.

| Part | Frozen native | Local decision | Art gate |
| --- | --- | --- | --- |
| Face finish4 | `9d2c9d42c01c99f0138bb9227e3679ce3afa882d2f43c339ab26496c4c559a4b` | Use as an integration WIP. Under-eye paint, iris rim and upper lash improve the tired expression. | AC2 FAIL: wide planar upper face/cheek, simplified nose/mouth and generic chin transition remain. Half-blink is only a diagnostic. |
| Hair projected pigment | `0d787482198137c37a5fd80067f7f6ce74678c1a99df783b0ece7cb59c5fb319` | Supersedes396 as a material-only WIP. Crown sheen, directional variation and back lock separation improve. | AC4 FAIL: root specks, muddy lower locks, weak graphic ink hierarchy, braid/knot shape and profile eye occlusion remain. |
| Body candidate8 corrected | `8a5bc113690ab336dd9fd990d42a5e656c86a701c8dda9483e6df0c085e378fa` | Reject integration. Preserve as a diagnostic of an actual returning underside. | AC3 FAIL: long horizontal lower edge creates cuboid masses in front/oblique. |

The hair review found no obvious large skin bleed, hard projection seam or strongly view-locked new shadow across five views. This does not certify animation. The five generated paint panels have512px per view; the4096 atlas is storage resolution. Only22.29% of UV samples had confident projection, with the396 pigment retained elsewhere.

The body next step changes the lower-pole height across X, with a rounded central low point and earlier medial/lateral attachment. Changing only mass/fold width left the same horizontal termination. The reference garment hides the exact bare fold, so a deep continuous crease would be an unsupported invention.

Root independently inspected the integrated diagnostic front/oblique face and profile body boards, plus corrected8 profile/oblique close boards. The preserved face4/body5/hair396 diagnostic is not an art selection. All14 source comparison pairs use the same recorded camera, light, display and actual active keys for baseline and candidate. Evidence validation passed; art did not.

## Portable frozen evidence

- Face: `parts/face-finish4/reference-review.json`; original delivery, maps, recipes and yaw bracket in `delivery/`.
- Hair: `parts/hair-ink-paint/reference-review.json`; generated paint/prompt and actual render provenance in `delivery/`. Historical exact recipes retain producer absolute paths; use the archived packed native for material replay.
- Body5 diagnostic: `parts/body-candidate5/reference-review.json`.
- Integrated diagnostic: `integrated-review-diagnostic-1/{face,body,hair}/reference-review.json` and README.

Original producer metadata is retained verbatim. Portable packages rewrite artifact paths only. No private real-person reference was used or archived.
