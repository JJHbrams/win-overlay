# V24 rear gathering work

Active bounded geometry: `sculpt2/Mia_HairStructure_v24.blend`, SHA-256
`d146427b39895e834cb86a307799b586b454356648bdb7463e8e1927800fd402`.

Root reviewed the preceding actual curl form as a useful local structural
improvement, then requested shallower, unequal broad hair banks. `sculpt2`
implements that change. This is permission to continue pigment work, not art
acceptance or whole-hair completion.

The original detailed Pixal hair stays unchanged. Three existing small
Fold_Left/Fold_Right/Binder owners are retained hidden, and three new closed
gathered-hair meshes replace their visible role. Each new owner is static,
unparented, with identity world matrix and no modifier or shape keys. The
longitudinal UVs have no zero-area triangles. The source native and failed
ear-lock experiments remain immutable.

`sculpt2/paintplate_back.png` and `paintplate_profile.png` are actual isolated
1024px geometry renders. `paint-projection.json` records their exact cameras.
Generated pigment inputs must follow those masks; they are never model evidence.
`export_paint_mesh.py` records the actual mesh UV triangles, camera projection,
and BVH visibility for baking a genuine connected material channel.

Rejected material/geometry probes:

- Root-level first ring and smooth oval: inappropriate even rim / badge read.
- Root-level direct low-resolution source-art projection: dark, blurred and
  useful only to test the projection route. Not the selected material.
- `boundary1`: local boundary relaxation does not reconstruct the full ear/nape
  cut-out lobes and worsens some dark triangular layer edges. Explicitly excluded.

Remaining AC5 failure: main hair extraction boundaries around ear and neck are
not repaired. New bun pigment does not replace that structural work. No final
rig, physics, garment or all-expression claim is made.
