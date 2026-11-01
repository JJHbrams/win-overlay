# Whole-face reconstruction — current user directive

The user rejects WIP9+M5 including its eyes and hollow malar/front-cheek volume. Autonomously rebuild a face resembling the confirmed multi-view concepts. Earlier local-gain reports are not user approval. Preserve original files, not erroneous face positions or the E2 eye shape.

## Source and baseline

- Current live but user-rejected baseline: `../integration-wip-9-review/Mia_FaceReview_v22_WIP9_M5.blend`, SHA `c04f81985330eace7ba06142cb99419f7c043f680f8fcfbefefff237ece56778`.
- Design sources remain `references/received/mia-face-reaffirmed-20261031.png`, `references/mia-expression-style-confirmed-20261031.png`, `references/mia-clean-master-v22.png`. See REFERENCE_INDEX and REFERENCE_REVIEW_GATE. Do not generate an easier substitute reference.
- Read-only discovery finds a hidden pristine `Face` inside the current native. Its Basis/all42keys/topology/UV match the original Victoria import and02:40 saved source. This establishes provenance, not sculptural quality or Mia identity. Inspect actual neutral multi-view renders before choosing it as a foundation.
- Original `Face` is identity transform; current visible face is Rz180. Explicitly align coordinate frames. All keys must be neutral for foundation inspection. Head cap is a separate owner; include its connection in the head scope, while protecting lower body/hair/accessories.

## Acceptance criteria

| id | criterion | user_visible_outcome | intended_runtime | verification | evidence | critical |
|---|---|---|---|---|---|---|
| AC1 | Coherent orbit–malar–front/side-cheek–muzzle–jaw primary volume; no hollow undernourished cheek, local sphere or seam-like fold. | The face has the concept's supported cheek mass and a continuous turn in space. | Saved neutral head and limited expression probes | Bare matte front, both obliques, profile and intermediate yaw/elevation, independently viewed | Actual before/after/source boards and turn views | true |
| AC2 | Whole-face width/height and cheek-to-chin taper, forehead/nose/mouth/chin depth conform to the observed source views. | No short broad mask, cheek notch or isolated pointed wedge. | Saved neutral head | Fixed matched source4 cameras; separate eye-spacing calibration exposes disputed height, pose uncertainty retained | reference-review.json + valid evidence check + actual visual judgment | true |
| AC3 | Reconsider upper/lower eyelid curves, corners, eye depth, iris coverage and lashes together; E2 is not a locked target. | Source-like tired gaze with coherent neutral, half and full blink. | Neutral / half / full blink, front and oblique | Actual visible eye/lid contact and images, not key counts | Rendered contact probes and original/new ownership mapping | true |
| AC4 | UV/pigment, upper crease and fatigue support source identity after primary form; original/non-face data remains protected and current actual native is reviewable. | Makeup does not disguise form defects; no unrelated model regression. | Actual saved native and live Blender MCP | Color-only/lit source views, hashes/scope audit, actual live head-centered inspection | Surface records, source4, saved/reopen audit and MCP captures | true |

Scope allows new face topology and UV/key remapping if necessary. Do not constrain incorrect old vertices merely to claim exact preservation. Preserve untouched owners and record any reconstructed face key/UV limitations explicitly. Full event-animation acceptance remains downstream; these minimal expressions diagnose the face rather than completing animation.

## Execution

1. Inspect the actual unwarped source foundation in the same current scene, with correct visibility/frame. A generic donor is not the finished design.
2. Sculpt the connected primary form and source features as one head. Do not repeat cumulative local Gaussian/polynomial/X-only fields on the damaged dense face.
3. Read actual source4 and bare intermediate views early; revise observed form, not a guessed numeric target. Match makeup only after the primary-volume check.
4. Independently review the integrated native, actual blink and live MCP. Keep all critical failures open. Technical success or version numbers do not grant ART PASS.

Root owns canonical docs/integration/live/Git/Wiki. Producer owns only new `mia-face-foundation-v27` outputs in the separate `codex/mia-face-foundation-v27` worktree. Preserve previous failed outputs for provenance; do not silently adopt them.
