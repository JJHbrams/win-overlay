# Mia v45 bounded rig draft

The v45 source is the already-bound isolated seam-weight repair trial. The
original binder was not rerun; mesh geometry, UVs, materials, and packed
references were preserved.

- The repaired-weight provenance is `weight-repair-provenance-v3.json`.
- The bounded Click proof uses only 0..5 degrees on `DEF_UpperArm_R` and
  0..14 degrees on `DEF_Forearm_R`. Rendered frames 0007, 0015, and 0022 were
  checked; this narrow arm range is not evidence for larger arm motion.
- Rest-neutral body delta from the repair trial is `5.364418e-7 m`; its coat
  hem diagnostic reports zero arm-weighted hem vertices.
- Face, Blink/shape keys, finger articulation, collision, and full-range
  animation have not passed. The painted face is rigid-head-turn draft only.
- The pre-existing shoulder-pin overlap is source fidelity debt and was not
  edited by this bounded weight correction.
