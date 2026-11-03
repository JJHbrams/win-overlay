---
name: mia-reference-modeling
description: Improve this project's Mia Blender character against its approved concept art, using relevant artist techniques, scoped mesh edits, and actual comparable renders. Use for Mia modeling, face/body/hair, UV/material, deformation, or source-review work.
---

# Mia: reference-guided character production

## Enter the current work, not a new rebuild

Read `asset/mia/AGENTS.md`, `CURRENT_STATE.json`, `WORKING_PROTOCOL.md`,
`REFERENCE_INDEX.md`, `REFERENCE_REVIEW_GATE.md`, and the active stage plan.
Paths here are repository-relative unless inside this skill. Run:

`python tools/mia/pipeline/mia_pipeline.py context --root <canonical-worktree>`

This is a short index, not a substitute for reading the current documents or images.
The configured worktree may be an old C: checkout; follow the canonical path in
current state, without moving files or switching another session's branch.

Preserve accepted work. Current pilot is the existing neck/shoulder/axilla body
correction and its review; do not restart the accepted face or supersede the
main session's H/FB acceptance criteria. If the main session has advanced, use
its latest state instead of this historical pilot label.

## Use professional knowledge for the current defect

- Body/neck/shoulder/axilla: read [body shaping](references/body-shaping.md).
- Face/eyelids/brows/lashes or hair: read [face and hair](references/face-and-hair.md).
- UV, color, normals and lighting: first read the existing Working Protocol's
  material diagnostics; follow the relevant part reference only as needed.

Before an edit, record briefly in the existing trial log: the visible mismatch,
its likely 3D cause (including camera/pose/occlusion/material alternatives), a
confirmed source principle, the chosen operation and affected/protected region,
and the views that would distinguish success from a regression. Do not add a
new contract document for every small adjustment. Source links and course
outlines alone are not learned techniques; record the material actually read
or the video segment actually examined.

Choose the representation that can make the needed shape: direct polygon
editing, proportional editing/cage, sculpting, or justified local retopology.
Procedural fields are useful when they have sufficient freedom; they are not a
reason to keep repeating an ineffective coefficient change. A preservation
boundary that prevents the requested change must be explained and re-scoped
explicitly; never silently erase the protected feature or redefine success.

## Choose the execution mode by the operation

Use **background Blender** for rough blockout/proportion candidates and repeatable
batch work: technical checks, a previously reviewed deterministic mesh delta,
UV processing, texture baking, matched-camera renders, orbit frames and export.
A blockout still needs actual multi-angle visual review before further shaping;
the background process is not evidence that the visible Blender contains it.

Use **live Blender through the existing MCP** for anatomy-sensitive refinement:
connected cheek/orbit/jaw or neck/shoulder/axilla volumes, eyelid/eyeball contact,
breast-to-thorax transitions, hair silhouette/strand spacing and local clipping.
These edits need immediate inspection of the actual surface and adjacent angles.
The current upper-body refinement belongs here; do not return to unattended
coefficient searches as the default way to resolve its remaining shape defects.

MCP may execute Python/bpy, polygon/cage edits or supported sculpt operations.
The distinction is the feedback loop, not mouse clicks versus code. Read the
installed schemas, identify the actual working file/object/evaluated geometry,
inspect and show the affected selection, make one hypothesis-sized edit, then
inspect actual before/after matte/wire and source views before the next decision.
An addon-status response alone is not a scene inspection or a modeling action.
Record the retained/undone decision briefly in the existing trial log; keep a
checkpoint/undo path without saving another full native for every small edit.

At background-to-live handoff, identify the exact candidate and verify it is
the scene being viewed. Do not overwrite another working scene or discard
unrelated unsaved edits. At live-to-batch handoff, capture the reviewed state
with the existing checkpoint procedure, then batch-render/bake that same state.
Batch validation can reject a reviewed candidate; it cannot replace the live
refinement step or automatically promote the candidate.

If live MCP is unavailable, report that limit and inspect the existing connection
without changing settings or interrupting Blender. Background diagnostics can
continue, but do not silently substitute another blind fine-shaping solve or
claim live review. Do not install/switch MCP or change origins as a shortcut.

## Small, visible edits

Compare source / baseline / candidate at matched camera, pose, visibility and
review lighting. Hide occluding hair temporarily for eye/axilla diagnosis and
restore it. Use neutral geometry plus early target-look/color checks to avoid
confusing makeup, ink, normals and shape. Reuse current fixtures and renderers;
do not build another framework before making a useful local change.

Review the defect and neighboring angles immediately, then expand valid
candidates to all views/poses required by the active contract. Good front and
profile views do not excuse a broken oblique/high/low view. A few edits without
visible improvement call for a changed diagnosis/operation, not more of the
same or an arbitrary HALF target. Retain or restore deliberately.

## Evidence and continuity

The helper can inspect existing H-style capture JSON without rerendering:

`python tools/mia/pipeline/mia_pipeline.py inspect --root <root> --capture <capture.json> --source <source.png> --views front,profile,back,oblique`

Add `--candidate <capture.json>` for declared before/after fixture comparison.
Add `--output <root>/.mia-cache/mia-pipeline/review.json --activate` only when
choosing that packet for this worktree's advisory Stop hook. This changes only
the helper's ignored receipt/pointer, never production CURRENT_STATE.

For final source boards keep using the existing `validate_reference_review.py`:

`python tools/mia/pipeline/mia_pipeline.py reference-review --root <root> --package <reference-review.json>`

Capture integrity is not source correspondence, visual likeness, deformation
approval or ART PASS. The helper never selects/promotes models. Inspect the
actual images and retain per-view differences, regressions and uncertainty.
After a post-review change, old evidence is stale for that changed state.

Update existing state/trial records at meaningful checkpoints with selected
file, actual verification, remaining problem and next action. Raw candidates
and frames stay in ignored cache; obey ARTIFACT_POLICY and the existing capacity
guard before heavy writes. Do not reduce final orbit/paired-review requirements.

Project hooks only supply short resume context and advisory evidence reminders.
They do not grant art acceptance or automatically continue a stopped turn.
They remain silent until `inspect --activate` opts this worktree into the pilot;
`python tools/mia/pipeline/mia_pipeline.py deactivate --root <root>` disables
the pilot pointer without deleting receipts or changing global hooks.
