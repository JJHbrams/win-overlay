# Independent acceptance audit — Astra checkpoint 817732

Native SHA-256: `81773274ef99152728ad584488ba720a35d783a2cb12acb2b313c0ca14253d10`.

The planner did not implement this model. AC3–5 use actual canonical `final-matrix/` and `final-poses/` images, copied bit-identically from validated v2 outputs. Technical AC1/2/6 use separate fresh Blender 5.2.3 runtime evidence; the planner did not rerun Blender or directly inspect JSON in its restricted role. Root decoded all 75 PNGs, checked nonblank content and input-native SHA binding. Numeric v2 matrix/pose exit codes were not captured and are not reported as zero. Four body frames were subsequently replaced by world-space-corrected renders (exit 0); the other 26 pose frames were retained.

```text
[ACCEPTANCE_AUDIT]
AC1: PASS — separate anatomy ownership, non-rendering packed references, proxy/hair/garment excluded.
AC2: PASS — immutable source/archive, original 42 key-coordinate hashes, ordered topology and UV preserved; derived Face44 prefix valid.
AC3: PASS — slender abdomen/waist, restrained shoulders, pelvis/thigh emphasis and slim calf form remain coherent across views.
AC4: FAIL — iris stability, depth and head handoff improved, but the planner still judges crown/facial-mask balance, eye shape/sclera exposure and profile planes insufficiently close to mature Mia.
AC5: PASS — actual blink/mouth/gaze and arm/torso/knee stress controls deform visible geometry, no major tearing in tested poses, neutral return 0.
AC6: PASS — independent fresh reopen/render exited 0; source/candidate SHA unchanged, refs packed and no missing textures.
overall: FAIL
```

This is a usable body fit and rigged structural checkpoint. It is not an approved Mia face or a completed character. Astra repaired the oblique iris slope, transported nose/mouth relief and orbital lift through all keys, and closed nearby head boundary points without welding. No critical collapse or penetration was observed in the reviewed views; remaining AC4 failures are art differences rather than proof that the prior structural defects remain.

The first technical audit's false `derived_structure_match` came from a comparison-code field-name error. Every shared structural field already matched. Replacing the dict comparison with explicit structural keys and rerunning the same native produced r2 PASS; the first result is retained.

The later world-axis audit corrected mislabeled local-axis tilt/twist tests.
`independent-astra-v09-world-audit` exited 0 with genuine world-Z torso/head
yaw, arm raise world-Z rise 0.087262m, zero quaternion/pivot error and exact
neutral return. The separate four-frame pose patch proves world-front arm
tail movement 0.140809m and torso yaw 0.259999rad. These supersede the old
directional labels without changing or saving the native model.
