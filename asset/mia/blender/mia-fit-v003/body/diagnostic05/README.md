# Rejected05 pose/operator diagnosis

R3b `4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1` remains the selected scene. No new anatomy, garment, native save, live edit or motion-rig approval is part of this checkpoint. Historical target01 manifest remains frozen and describes that earlier rejected checkpoint.

## Retained failures

- 02: finite connected fairing improved sternum smoothness, but ten hard pole anchors made cones; inferior shelf remained in actual gray front/low views.
- 03: ordered interior resampling broadened the apex but retained old-shape seed assumptions and an invalid axillary chart; neck-branch normal reversals failed the CPU gate. No actual images.
- 04: actual source JSON was consumed, but old inferred height knots contradicted new source bands, producing upper-root reversals. No actual images.
- 05: conflicting knots removed, broad source support consumed, CPU orientations/contact bounded checks passed. Actual E2/F2 still showed a boxed lateral lobe, deep vertical wall and thin lower lip. **Rejected as finished form.** Its cloth-envelope and source-arm-pose correspondence remain limitations.

## Normals and pose facts

`../posed-target/private-normal-audit-05.json` compares source, q0 bake and05 with freshly rebuilt geometric automatic normals. Raw/evaluated custom normals are absent. Actual body corner-vector differences are exactly zero, ruling out stale corner normals as the cause. Smooth-vs-face-normal differences are ordinary interpolation, not that test.

Current upper/lower rig frontal angles are approximately25.46/27.88 degrees. E2 visible skin directions are approximately14/19 degrees; those are different landmarks. The source-like diagnostic uses14/19 degree bone axes as a labelled hypothesis while keeping camera and corrected05 key fixed. It is not an exact pose registration or a way to accept the shape.

## Reproduction and operator test

Run `verify_diagnostic.py` in Blender5.2 background with `--python-exit-code 2`. It opens the exact current native read-only and clones both mesh/key data and rig. The frozen empirical Armature inverse converts the05 posed control field into one private additive key. All original47 arrays remain exact. Full evaluated05 reconstruction has a measured floating-point tolerance, separately from the bit-exact accepted head. Rest bones are copied; no edit-mode/rest operation is used.

Four states cross current/source-like pose with original/body-scoped post-Subsurf Smooth. A new private group neutralizes Smooth in the chest/shoulder/axillary region with a boundary feather; the original group and all other modifier settings remain untouched. Face690 receives no mask change. CPU checks cover all620 original owners, all47 copied arrays, accepted evaluated head and exact private pose restoration.

The initial reset through `matrix_basis` decomposition introduced0.000239mm roundoff on the private copy. Reset now restores the original authored transform channels exactly; its CPU restoration guard is bit-exact.

`render_diagnostic.py` requires root's exclusive GPU token. It emits exactly four F2 gray frames using the existing05 camera matrix, clip range, resolution, material values, three-light fixture and color management. The completed four actuals record pose and light energy/size/color/matrix, but omit actual use_shadow. The recipe copied use_shadow from05; independent actual shadow-state equality is therefore unverified. The recorder now includes use_shadow for future runs, without retroactively filling old observations. Every image remains a diagnosis of rejected05, not an anatomy improvement.

## Checkpoint scope

`curate_checkpoint.py` validates selected image hashes, parses Python recipes, checks the completed CPU/actual guards, and creates the new `checkpoint-02-05-files.json`. It does not alter the historical01 manifest. New evaluated caches are regenerable using the included verification producers and are excluded, as are full natives, transcripts and logs.

Actual interpretation and next connected anatomical construction await root's visual diagnostic review. No additional radial-field correction is selected.
