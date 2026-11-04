# Refine a shaped character without destroying neighboring work

## Observed artist practice

Read on 2026-11-04: the public HTML bodies below, not continuous videos. No
confirmed video timestamps, paid lessons, asset downloads or installations.

- Julien Kaspar, Blender Studio, [Fine Control on a Single Object](https://studio.blender.org/training/blender-fundamentals-45-lts/fine-control/):
  the joined-arm example explicitly addresses a brush also moving the nearby
  torso. Lock the torso with a mask, edit the arm locally, expand/invert and
  soften masks as needed. Face Sets and visibility isolate hair clumps; a
  local finger posing example uses a bounded selection. Collections retain
  versions for immediate comparison. This directly addresses Mia's c9 failure.
- Kaspar, [Detailed Sculpting](https://studio.blender.org/training/blender-fundamentals-45-lts/detailed-sculpting/):
  repeated remeshing/smoothing can lose details; stable major forms and suitable
  base topology precede finer Multires work. This does not establish that Mia's
  dense triangle mesh can accept Multires safely.
- Kaspar, [Rain, File 6: Posing](https://studio.blender.org/training/stylized-character-workflow/5d66506078d6dda492f2814a/):
  public description lists proportion-test posing, refined posed versions,
  corrective Shape Keys and Workbench silhouette settings. Description only;
  no claim to have exercised its native or watched the posing sequence.
- Blender manual, [Auto-Masking](https://docs.blender.org/manual/en/latest/sculpt_paint/sculpting/controls.html)
  and [Face Sets](https://docs.blender.org/manual/en/latest/sculpt_paint/sculpting/editing/face_sets.html):
  combine the appropriate region and boundary controls. Topology auto-masking
  means connected geometry, not an anatomical arm/body distinction. Joined
  arm and torso therefore still need a mask/region boundary. A Face Set label
  alone does not force an arbitrary Python operation to respect it.

These are concrete professional techniques and official tool capabilities,
not proof of a single mandatory industry pipeline. Exact ID/hash checking
below is Mia's automation of part preservation, not a claim that the artist
uses numerical hashes while sculpting.

## Procedure for the current Mia surface

1. **Choose one visible defect.** Use the actual retained mesh and reference
   views. Distinguish local shape, proportions, pose, material and occlusion.
   A whole-character request is a sequence of coherent local edits, not
   permission to replace every vertex during every subtask.
2. **Isolate actual anatomy before editing.** Declare editable faces/vertices,
   the necessary blending collar, and named fixed neighboring parts. Use
   actual selection/Face Sets or a reviewed sculpt mask. Show the selection
   from the defect and neighboring/back angle so hidden influence is visible.
   A coordinate box or distance radius is only a selection aid, not evidence
   that the selected region has the right anatomical ownership.
3. **Preserve and edit locally.** Keep one recoverable original and one pending
   delta/RAM copy. Mask fixed parts; hide occluders temporarily. Use native
   polygon/proportional/sculpt/pose tools or a scoped numeric operation suited
   to the defect. Proportional/elastic/ARAP operations must respect the same
   domain; their smooth falloff is not a substitute for masking. Avoid global
   remesh, smoothing, UV rebuild or full mesh replacement during local finish.
4. **Check immediately, then proceed.** Inspect actual matte/wire and early
   toon output at the defect and adjacent angles before allocating a full
   render batch. Compare source/baseline/candidate with one fixed camera/light/
   pose and original source aspect. Make an explicit keep or restore decision
   before another part. Then complete the existing source4, opposite/high/low,
   pose and saved/reopen gates for a surviving candidate.

For the present arm problem, thorax, shaped breast surfaces, posterior lats,
head and waist are fixed during the first arm-only edit. Hand/nail shape may
be rigidly transported. Arm length/position, arm girth/axillary join, and waist
contour need separate diagnoses and scoped edits. This is a current operation
boundary, not a permanent ban on later source-supported torso corrections.

Do not solve a too-tight mask by silently releasing the torso. If a required
attachment cannot move naturally within the chosen collar, report the exact
boundary conflict and re-scope the interface before editing. Do not force old
whole-girdle targets into a newly fixed arm root.

## Execution and limits

Bind a scoped delta to the actual object, topology and starting coordinates.
Editable/transition IDs and named fixed IDs must be explicit. Check proposed
coordinates before installation; every point outside that domain and every
fixed point must be exact. Protect UV/material/key/modifier/normal data as
appropriate to the operation and verify actual readback. Reject stale inputs
and unsupported topology changes rather than enlarging the domain implicitly.

The scoped edit helper permits one pending edit and preserves an exact restore
path. A recorded decision and images, not a numerical test alone, justify keep.
For UV/material-only work use equivalent target-object/channel protection;
do not demand a geometry delta when no geometry is being changed.

The supported data-only MCP dispatch is `tools/mia/review_h/lab_mcp.py call
--tool execute_blender_code --mesh-edit-job <cached-job.json> --report
<live-report.json>`. Its `mesh_edit_job.py` bridge binds reviewed source/selection
files and NPZ arrays by SHA, then the live guard binds actual coordinates,
topology and explicit IDs before making a RAM copy. The job contains data,
not a candidate Python program. Missing/stale inputs and outside-region
coordinate changes are errors, not invitations to use the raw route instead.
Nonzero geometry quality/collision/source review is still a separate stage.

The existing SessionStart/PostCompact/Stop hooks are advisory and runtime
activation has not been proved. They are not a pre-mutation lock. The supported
scoped MCP route rejects invalid deltas, but full bpy/raw MCP access can bypass
that route; mandatory skill use remains necessary. Neither hashes, collision
checks nor hook output judge anatomy, source likeness or artistic completion.

The c9 bulk carrier is retired after actual source review: reach improved,
but outer breast/root, shoulder and lat shape regressed. Its exact695 restore
is verified. Do not replay that retired candidate after compaction.
