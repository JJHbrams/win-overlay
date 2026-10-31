# Face6 continuous lower-cheek candidate

Frozen LOCAL WIP for independent review; not a full face ART pass. Face5 a5ec86 remains immutable. First b5e97 trial in candidate/ is NOT selected: broad boundary protection limited visible outline effect to2–3px.

Selected-for-review native: continuous-candidate/Mia_FaceFinish6_v22.blend
SHA256 f5d17264e07f492983e7e075d5a3213b2bd14a4adaead82072899e9b3e15d98a

## Source basis and result

Original fixed uniform source registration is retained for portrait FRONT, small v22 SIDE, expression04 left oblique and expression03 opposite subtle angle. No candidate feature refit, anisotropic warp or global head scale. Source camera pose, hair coverage and expression uncertainties remain in reference-review.json. Measurements refer to visible hair-framed skin, not full skull width.

Front lower-cheek visible skin widths change315→299px at panel y400(source276) and277→264 at y420(source240). Near lower jaw y440208→205(source207). The reduction is visible in front/oblique and does not introduce a new observed orbital ledge in neutral A/B. It is a partial reduction, not complete identity matching. Profile central nose/lip/chin shape is retained.

One local X field tapers the lower lateral cheek and the matching Body headcap surface. Maximum Basis displacement2.4mm, actual neutral evaluated skin2.39965mm. No Y/Z displacement on evaluated face. Actual Basis support z1.48011–1.52557, with smooth vertical/lateral/front-back attenuation. Eye and oral boundary control rings are protected. No aperture or iris enlargement. Actual evaluated ocular boundary delta0.

## Ownership and preservation

Changed owners: MIA_V14_SculptedSkin coordinates and24 MIA_V06_BODY_SKIN headcap vertex IDs only. Body vertex changes are explicitly in body-headcap-deltas.json; sourceBasis worldZ>=1.46 restriction verified. All Body Basis vertices below1.46 unchanged. Additional evaluated Body movement below1.46 is7.64e-8m (0.000076mm), numerical precision scale. Previously inherited source headcap/jaw effects remain baseline and are not erased.

Identical pervertex delta applied to every relative shape key and independent vertex cache. All original UVs, topology, weights, material assignments, eye/lash/hair meshes,69 packed image bytes/fake-users and other owners preserved. Manifest saved-native reopened snapshots verify this. Relative key error max is reported below.

34 actual lower seam samples: maximum nearest Body surface distance1.78955→1.77263mm; largest increase7.44e-9m. This preserves, rather than fully fixes, the inherited imperfect join. Coordinates/nearest-surface distances do not prove perfect smooth normals. No new visible gap observed in neutral comparison.

Existing Close.5 and Fun.25 static A/B and explicit original UVMap checker were rendered and viewed. No new severe regression seen. Inherited static-eye/lash/expression limitations remain; this is not a final expression rig pass. Checker retains existing density distortion and does not certify optimized UVs.

## Nose and remaining limitations

Production triangular peach nose patch and vertical side stroke persist in albedo-only isolation. They are fixed UV pigment, not solely scene light or a seam. Inspected nasal edges are manifold, zero crease and not sharp. A source SIDE yaw bracket does not justify blindly reducing nose projection further. No nose/material change was made in Face6. Broad upper temple/side plane, graphic nose treatment, mouth/jaw identity and source pose mismatches remain FAIL.

Narrowing lateral cheek can expose more of the existing old hair's jagged inner edge in profile. Hair was not changed; review with current integrated hair before selecting overall appearance. Do not claim source-faithful finish from the width numbers.

## Exact recipe provenance

build_continuous_lower_cheek.executed-before-report-fix.py is the original executed recipe that saved this native. After save/reopen, its report accessed stale Blender Object references and stopped. Geometry/native save and reopened mesh/packed assertions had already succeeded. build_continuous_lower_cheek.py repairs only post-save report names and adds --verify-existing. It re-applied the same coordinate recipe in memory from Face5, opened the saved candidate, and asserted exact snapshot equality; native was NOT overwritten. This corrected recipe is suitable for future builds.

replay_continuous_lower_cheek.py changes only the snapshot-helper dependency path to the identical archived dependencies/legacy_snapshot_apply_interp.py. Use --source ABSOLUTE_FACE5_COMPATIBLE_NATIVE --output-dir NEW_EMPTY_OUTPUT. Do not replay onto already-Face6 skin. Root can compose full cap coordinates with separately owned body below1.46 using vertex IDs.

Command:
blender.exe --background --python replay_continuous_lower_cheek.py -- --source INPUT.blend --output-dir NEW_OUTPUT

Root evidence validator passes required4views and equal camera/light/display records; it does not grant ART acceptance. Native, source and all prior outputs remain immutable.

Relative key max error(m): 3.725290298461914e-09
