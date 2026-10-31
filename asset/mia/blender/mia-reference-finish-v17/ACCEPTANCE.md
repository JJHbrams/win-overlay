# Mia head, face and Pixal hair refinement v17

User request: refine face/head/hair meshes, textures and UV maps against confirmed artwork; retain detailed Pixal hair and reshape it together with the head. Future bones and partial morphing for braid/tips/messy hair follow static refinement.

This continues the existing isolated Mia worktrees. All original art, raw Pixal files, prior studies and v16 native 9b21f94c2214bf225e7cacd6d4caa059b2f102f1b63556cf7730f5d62a5608b2 are immutable inputs. No new body/clothing, final rig, secondary physics or event motion work is included in this phase. Full-character completion remains outstanding.

| ID | Critical required outcome | Intended runtime | Verification and evidence |
|---|---|---|---|
| AC1 | Preserve sources; separately editable head skin, eye/oral parts, hair, and owned face/hair materials. | Saved Blender static native | Source hashes, object/collection/material/UV/key inventory. |
| AC2 | Retain actual Pixal strand detail while repairing rectangular fringe/temple cuts, tapering ends and matching canonical crown/nape/rear-wave, half-up and left braid silhouette. | Saved Blender static native | Front, both three-quarter, profile and back beauty/clay against confirmed art, close and wider framing. No automatic approval from polygon count or file existence. |
| AC3 | Fit hair and skull jointly using recorded landmarks and full-head geometry, with natural hair-hidden head and hairstyle-specific reversible masks only where needed. | Saved Blender static native | Same-camera hair-on/off five views; source alignment assumptions, landmarks and clearance notes. A zero delta to a region is valid only if the combined art comparison supports it. |
| AC4 | Improve heavy eyelid, iris/pupil exposure and profile curvature, nose/jaw/mouth shapes to match Mia; keep corrected sclera culling and no lower white band. | Saved Blender static native | Before/after head and eye close-up front, both three-quarter, profile; isolation of iris/sclera/skin where needed. |
| AC5 | Refine fixed UV face and hair surface appearance: readable line/under-eye marks, restrained cel color, ash-gray detailed hair. No camera-dependent billboard. | Actual active materials in saved native | Packed atlas and active shader trace; actual visible FACE and HAIR UV checker front/three-quarter/back where relevant; seams/stretch inspection; fresh reopen beauty. Imagegen paint source must be labelled separately from actual 3D renders. |
| AC6 | Prepare meaningful hair regions/owners for later local deformation without claiming finished animation topology or weights. | Static native ownership | Crown/fringe, side/nape, rear-wave, braid and loose/tip ownership or vertex regions; root/contact review. No new motion/physics now. |

All criteria are critical. Technical preservation is not art acceptance. A fresh independent reviewer assesses the final integrated native/render evidence; unresolved criteria remain FAIL/UNVERIFIED. Do not report the full model complete or push a completion commit from partial art results.

## Ownership

- Astra head/hair: mia-head-hair-fit-v16 worktree, new refine_mia_pixal_head_v17.py and mia-pixal-head-v17 folder. Hair plus scalp/forehead above brow; preserve lower face/body and source UV.
- Astra face: mia-final-face-v12 worktree, new refine_mia_face_surface_v17.py and mia-face-surface-v17 folder. Eye/lid/lower face, materials and UV; no global skull or hair transforms.
- Root: this integration folder and replay/verification, optional new registered paint plate generated only after face geometry settles.

## Reference priority

Latest reaffirmed portrait codex-clipboard-4757319a-0704-45b5-b59c-0d588cb596a3.png, received/mia-front-body-reaffirmed-20261031.png, mia-expression-style-confirmed-20261031.png, and mia-clean-master-v22.png. Illustrations differ in tilt and some proportions: record target and view assumptions rather than pretend exact orthographic agreement. Private real-person references must not be used or recorded.

## v18 user steering and renewed checks

The user identified an unnatural eye–cheek transition in oblique views, an overly broad face, narrow-looking irises, and an apparently low upper head. The latest portrait attachment `cf6f0fa1-485f-4002-99bd-44f830279526.png` has the same SHA256 as the registered reaffirmed portrait `179d3ee9ebfea9c7f4b5725d487bf32a91b37397687cdef1d8c7b301cfee0a44`.

- AC3 remains open: evaluate the actual bare-head arc and hair frame separately; a global skull-height increase is not presupposed.
- AC4 is reopened: compare face width relative to eye-to-chin height, gray iris width relative to aperture, and orbital/cheek curvature in front, both obliques, profile and elevated oblique views. Preserve the heavy upper-lid character. A fixed-world-X normal-angle sample is diagnostic, not an acceptance target after narrowing changes the sampled anatomy.
- Isolated narrowing behind a fixed outer eye rim and an isolated forward cheek fill worsened the ledge. Those trials are rejected; their existence and successful saves are not completion evidence.
- Current topological/key preservation does not establish mature facial deformation. A small actual blink/squint check is needed after a coordinated rim/cheek correction; no event-motion production is added.
- Reference organization: current body-underwear studies, confirmed expressions and the reaffirmed portrait must be discoverable together. The Desktop checkout's missing fictional references are synchronized additively, preserving originals and explicit candidate statuses.
- The user explicitly authorized discarding the open Blender scene's test-only viewpoint changes. New candidates may be opened through MCP without another view-state permission request, while saved input natives remain immutable.
