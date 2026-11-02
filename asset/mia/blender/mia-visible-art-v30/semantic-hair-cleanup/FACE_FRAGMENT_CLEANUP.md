# Confirmed facial fragments retained inside canonical hair

`replay_face_fragment_cleanup.py` is a separate minimal cleanup. It does not
import B16, B23, their fringe rebuild, a hairstyle candidate, or any material.
It deletes only the 1,216 independently classified raw source polygon IDs in
`source-face-exclusion-plan.json` from `MIA_V17_PIXAL_DetailedHair`.

The exact plan SHA and canonical C main-hair geometry/UV fingerprint are
required. Missing IDs, altered input hair, shared mesh data, unexpected custom
normals, and missing real forelocks fail before deletion. Real-hair raw IDs
`82525` and `93291` must remain. There is no giant-component deletion or spatial
mask. The plan's B23 split of 688 main + 528 fringe belongs to B23; all 1,216
IDs are still in the single canonical C main hair used by Eye M.

## In-memory integration

Open the intended fresh Eye M + face target first. Its main hair must still be
canonical C. Add this directory to `sys.path`, then:

```python
from replay_face_fragment_cleanup import apply_face_fragment_cleanup
report = apply_face_fragment_cleanup(report_path="<NEW report.json>")
```

The caller controls save/review. The function never opens a model, saves a
native, changes a rig/pose, or adopts other hair candidates. Reapplying the
exact cleaned result returns `already_applied` and removes zero faces. A
partially cleaned/otherwise modified owner is rejected rather than guessed.

## Background diagnostic and reopen

```text
blender --background --threads 2 --python replay_face_fragment_cleanup.py --
  --target <source-eye-face.blend>
  --report <NEW report.json>
  --output <NEW diagnostic.blend>
```

`--output` is optional. Existing output natives are refused. Input native bytes
are checked unchanged. The save disables path remapping so existing image
reference metadata remains exact. Reopen the diagnostic with the same script:

```text
blender --background --threads 2 --python replay_face_fragment_cleanup.py --
  --target <diagnostic.blend>
  --report <NEW reopen-report.json>
  --expected-preservation-report <first-report.json>
```

## What is verified

- The BMesh operation is exactly `FACES_ONLY`; no vertices or edges are deleted.
- Every surviving face retains its winding, material index, smooth flag,
  face/corner attributes, and both UV-map values. All point/edge values,
  vertex coordinates, vertex groups, active UV selection, material slots,
  transforms, parent, visibility, constraints, and modifiers remain exact.
- Every other actor, all shape-key coordinates/values, material node graph,
  old packed-image bytes and metadata, world, camera, light, and scene settings
  are hashed before and after. The target hair's material graphs are included.
- The in-memory result is verified before committing to the existing mesh ID.

These checks establish bounded cleanup and preservation only. They do not
approve the hair's source likeness, reveal every possible remaining source
fragment, validate collisions, or establish animation/ART PASS.

## Eye M CPU verification

The saved diagnostic is `Mia_EyeM_CanonicalHair_FaceFragmentCleanup_Diagnostic.blend`.
It is a diagnostic artifact, not a newly selected complete character model.
Detailed evidence is in `face-fragment-cleanup-EyeM-report.json` and
`face-fragment-cleanup-EyeM-reopen-report.json`.

The canonical main goes from 122,129 to 120,913 polygons, retaining 100,383
vertices and 219,828 edges. All 1,216 planned IDs matched; zero were missing
before the first application. Both known real forelocks remain. The protected
state includes 593 other actors, 84 material graphs, and 109 old images,
including existing face/eye actors with all 42 expression keys.

No render/GPU, live Blender operation, source candidate edit, Git command, or
rig binding was used for this helper.
