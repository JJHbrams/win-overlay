# Preferred outer-wrap E — unilateral-aware driver completion

E supersedes D for integration. D's neutral/bilateral/source/owner-ID evidence
and construction history remain in `HANDOFF.md`; do not promote D from its
bilateral-only73-state audit. Direct D unilateral tests found exposed gaps of
0.107914mm at Close_R0.25 and0.280742/0.242688mm at Close_L0.25/0.5.

## Exact final component and tested replay

- `Mia_OuterOrbit_v31_E.blend`:
  `617f89c98141e969637b83a0df3ba0f56510ade7e657e2651855c4b0eb74cc9c`.
- `Mia_OuterOrbit_v31_E_IntegratedBrowsC.blend`:
  `c3a940e12792169a49bff33ce35dd9157a0300159c0aed2ddfd6220e06bfb87a`.
- Test input canonical `Mia_SourceBrows_v31_C.blend`:
  `4fc5504b91c61aef4c48d5e54542fd9add38fd5c6a97b42b8d9b94efbe33ed7a`.
- Input C remains byte-exact; every replay guard is true in
  `Mia_OuterOrbit_v31_E_IntegratedBrowsC.outer-wrap-E-replay.json`.

Use `replay_outer_wrap.py -- INPUT.blend OUTPUT.blend E` with
`outer-wrap-E-portable.json` + `outer-wrap-E-portable.npz`. NPZ SHA256 is
`58f57c8b2f06b456b149e8cf6c734c159ce17fabb677d181926ee978c6b69ae5`.
It is byte-identical to D's coordinate NPZ, because E changes NO coordinates.
The E JSON carries the updated corrective driver variables/expressions.

## Explicit validated mapping

Fresh raw comparisons proved affected wall, sclera and iris endpoint arrays
BIT-EXACT to bilateral Close: Close_R→worldside−1; Close_L→worldside+1.
Independent evaluated tests at0.25/0.5/0.75/1 also proved affected outer skin and
rim bit-exact to bilateral. The opposite rim is exact neutral. Do not claim
the whole opposite face is exact: inherited opposite broad skin drift reaches
0.050068mm and one opposite sclera shift2.354µm, with contact still embedded.

Each of the seven existing D corrective drivers now uses
`max(global_Close, matching_unilateral_Close)` as its effective value. All
original42 drivers/keys, all49 wall coordinate arrays, UV/topology/weights/
materials/maps and every other owner are bit-exact D. No new key or master
control is added by E. Max prevents doubling the correction, but does NOT
certify arbitrary simultaneous/additive controls.

`unilateral-E.json` independently evaluates64 states, each R/L at n/32 through
full1. Both sides are densely inspected in each state:

- Exposed positive end-gap samples:0.
- Missing ocular hits anywhere:0; exposed missing coverage:0.
- Worst exposed margin including the opposite side:−0.00368059mm.
- Affected R least overlap0.281710mm at0.21875; L least overlap0.00648387mm
  at0.03125.
- Saved E hash unchanged. D's bilateral73-state results remain applicable:
  E's additional side variable is zero for those single-control states, and
  all coordinates and original drivers are exact D.

## Actual evidence and camera depth precision

`unilateral-E-proof/records.json` records the actual E+FaceA+browsC proof:
front and affected-eye grazing for R/L at0.5 and1. Camera clipping is EXPLICIT
0.1..10m and recorded for every image; no native is saved after overrides.
Independent reviewer actually read all8 and supports the bounded unilateral
outer-seam handoff: no background slit, detached ocular carrier or temporal
opening; opposite eye remains visibly stable. Large closed grazing hooks/
crescents and blocky half-close upper fans remain OPEN style issues. This is
not full deformation or source-face ART acceptance.
Parent independently demonstrated that its default review-camera end1000m
caused tiny pale brow flecks at unchanged geometry/shader; changing only end
to10m removed them. The child first-hit diagnostic found zero opaque brow
occlusion in1330 camera subrays and supports that distinction. It did not
claim a CPU nearest-distance check proved renderer coverage.

D's older child source4/critical/ID records used a new camera's default far
clip1000m. Treat them as historical scoped evidence, not a claim that they
used10m. E neutral/source geometry and bilateral motion are exact D, so the
parent is generating its final common baseline/candidate source package with
explicit10m clip rather than redundantly regenerating child source4.

The tested outer background seam is a bounded integration result. Existing
Extra pinched skin/deep return pocket, small neutral pucker, closed outer lash
hooks/profile crescent, global likeness/lower-face/paint/brow style/hair and
broader deformation/head-follow/final animation remain OPEN. An opaque wall
instead of background does not approve the pocket's appearance. No full
AC1/6/character ART PASS is claimed here.
