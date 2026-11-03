# H floor boundary — no solve or model output

Read canonical inputs directly; no NPZ or native copy. The only generated
records are in canonical `.mia-cache/body-h/shape/`, outside Git. Code remains
in this sparse author worktree. No optimizer, mesh, Blender, GPU, native or
bake ran. Capacity `inspect(10MiB)` passed before both small JSON outputs.

## Measured conditional floor

The source file has37 raw points (13front-left/13front-right/11back-left),
with33 at absX>=50mm, matching the prior G set. There was no31-point input.
Smaller-X neck/head visibility is handled separately; no point was silently
relabelled. The same whole-height uniform registration and original pixels
are used. Figures below are conditional on nominal front0/back180 views and
the2px reading interval. They do not prove conflict over all pose uncertainty.

| True accumulated union | Nominal intervals exceeded | Maximum excess |
|---|---:|---:|
| Frozen11 |33/33|46.287mm|
| Remove cap/trap, original thorax |32/33|26.843mm|
| Fixed breast/arm/fan/wall only |15/33|15.213mm|
| Same fixed union plus radius-profile endpoint limit |15/33|15.213mm|
| Same limit plus cap/trap zero-scale point fields |15/33|15.213mm|

The positive nested thorax profile limit RX34mm/RY33mm gives the same33 roof
roots as deleting thorax. It is a roof-domain relaxation, not a demonstrated
whole-body construction with protected core matching and finite smooth joins.
Zero-scale cap/trap fields raise five inner roots by up to21.888mm; those roots
remain below their source intervals. Therefore the same15 constraints fail,
but it would be false to call all point-limit and removed roots identical.

Every fixed component remains inside any accumulated union containing it:
the fixed smoothminimum is monotone in both arguments. Thus the sampled true
zero at a particular Y is already a lower bound on maximum projected roof;
missing a higher Y maximizer cannot invalidate a positive floor violation.
MaxY coarse/fine refinement changes heights by at most0.257mm across cases.
No field value was interpreted as geometric distance. OldZ0/1.395/halo were
not imposed on the floor; they were implementation choices, not anatomy.

## Declared whole camera box and2D trace propagation

`pose_floor_bounds.py` then projected the fixed ellipsoids analytically and
bounded their exact upper ellipse intersection with outward interval arithmetic
over each ENTIRE panel yaw/pitch box. Front yaw[-4,4],back[176,184] and
pitch[-6,6] were unchanged. The original2px tracing precision is propagated in
both horizontal and vertical coordinates; the rectangular box conservatively
contains a2px trace neighbourhood. No pose or parameter grid was used.

Two front points remain certified outside their upper trace bands for every
camera/trace value in those declared boxes:

| Source pixel | Fixed witness | Minimum excess |
|---|---|---:|
|(323,235)|anterior fan R|6.104005mm|
|(328,238)|anterior fan R|1.998743mm|

Therefore the initially authorized four-shape-variable solve stopped BEFORE
optimization, as the contract requires. Cap/trap/thorax cannot remove a fixed
fan volume. This certificate concerns the declared camera and trace boxes,
not arbitrary unmodeled arm articulation or drawing deformation. No source
uncertainty was widened after seeing the result, and no fixed component edit
has been authorized or applied.

The provisional vertical-only trace report had larger bounds8.804/6.550mm
and a third small back claim. It is superseded by the2D-trace report; the back
claim does NOT survive horizontal tracing uncertainty. Keep the raw reports
distinguished rather than promoting the first result.

`verify_floor_math.py` independently lifts768 deterministic projected ellipse
boundary samples to the actual frozen3D fan. Maximum frozen field residual
8.05e-17 and normal/view-depth tangency2.76e-16; every sample is enclosed by
the interval bounds. An outside-column negative case is refused. Sampling is
implementation QA only; the all-camera certificate is interval arithmetic.

Independent reviewer `/root/body_h_acceptance` confirmed the projected
formula, actual frozen field and tangency, and the two6.104/1.999mm bounds.
This is a fixed-family feasibility failure under the declared inputs, not an
impossibility claim for anatomy or other construction methods. H shape,
materials, saved native and GIF remain unverified.

Worst nominal witness: source front(323,235),X=.155053125, interval upperZ
1.363939174. Fixed accumulated roof1.379152539 gives15.213mm excess. At the
same X, the individual raw arm and fan roofs are1.370908561/1.377688013,
already6.969/13.749mm above that interval. Wall alone is below it. Removing
one fixed group at a time does not resolve all nominal conflicts. This does
**not** authorize changing any fixed group before shared-pose interval review.

## Chosen upper window is an independent artifact

The actual retained head boundary has123 edges atZ1.465, bounds:
X[-.027106037,.026285514],Y[-.025888462,.037065070]. Width53.39155mm,
AP62.95353mm. The old guide cut1.445 and frozen guide field at1.465 are not
that boundary. Original donor head coordinates/materials/UV must stay exact.

With the SAME rejected G parameters and only its upper fade removed in RAM:

| Plane | G faded transverse/AP | Unfaded transverse/AP |
|---|---:|---:|
|Z1.435|102.542/86.680mm|92.240/81.176mm|
|Z1.445|92.305/82.216mm|80.998/75.781mm|

These are Y0 transverse and X0 AP roots, not maximum-over-Y widths. Above the
tentative guide cut, unfaded numbers are diagnostic only. They must not become
head geometry. A newly measured tangent/finite-row neck loft must connect a
source-fitted guide cut to the actual held head cut, including its AP centre
offset. The source guide profile may fit up to the new guide cut; forcing old
guide-field identity at1.465 is an artificial restriction. Cut1.445 is still
a tentative construction boundary, not an anatomy landmark.

## Proposed next analysis — floor obstruction requires root review

Use four common shape variables: cap scale, trap scale, RX-profile shift,
RY-profile shift. Keep logical inferior-medial anchors and fixed definitions
initially. Profile weights stay active through the chosen guide cut; derive
the lower transition from protected exposed breast/core and real corridor,
not from the former arbitrary slab. A fresh collar supplies the unchanged
head interface. Do not add an old-guide-field head-height pin.

Compare TRUE accumulated zero/tangent silhouettes and visible neck section
roots to source intervals. Minimize worst normalized interval violation first,
then summed residual/minimal parameter change. No HALF factor. Preserve both
observed sides rather than averaging them into a symmetric target.

Use one shared yaw/pitch pair per panel: front0+/-4, back180+/-4,
profile85+/-8 degrees, pitch0+/-6, as declared estimates. Keep whole-height
uniform scale/translation and projection fixed. All points in a panel share
the same camera variables; no per-point poses, image warp or source refit.
The active body is one3D shape for all panels. Trace2px is not a complete
pose interval. A numerical local optimum alone is not a global impossibility
proof; only a certified fixed-floor bound over the allowed pose interval can
justify a required domain extension.

If such an all-pose floor conflict remains, the smallest implicated domain is
at least the upper/lateral anterior-fan support, not an arbitrary all-body
warp. Only the fan is currently certified across the full camera/trace box;
the arm's nominal conflict is not an all-box certificate. Root must review
whether a bounded fan-root extension or explicitly justified source-pose
disposition is appropriate. No broad primitive edit follows automatically.
The posterior wall, breast support, arm definition and open corridor stay
protected. Actual high/low, source4, real joins, surface maps and final
full-body deliverables remain open.

If a fit is authorized after resolving this obstruction, root's revised
positive-part is the1-Lipschitz C2 hinge: eps*(2.5q^4-3q^5+q^6) for0<q<1,
zero below, and d-eps/2 above. Its derivative is smoothstep5 in[0,1]. eps1mm
leaves an explicitly reported radial offset up to0.5mm. The earlier polynomial
with derivative maximum1.512 must not be reused. Outer construction is
Fold+Wnew*(FH-Fold), Wnew0 below1.34/full1.365, with FH>=Fhom11 and
Wnew>=Wold required; no old partial-trap delta is stacked.

## Provenance

Actual transitive C files were read and match canonical D bytes:

- E field SHA256 `6bd907200a1ed082daf81fd2abde77e229890ecce405b415e3ca5b8e1e76f20d`.
- Base field SHA256 `94ff4d29ec7629de017281aef6fc63e3d681fd2da0dd7d9c6f6583b265f34bd0`.

Full paths/hashes, immutable parameter/source hashes, roots and capacity receipt
are in canonical `.mia-cache/body-h/shape/`: `competitor-floor.json`69390bytes,
`upper-window-diagnostic.json`8702bytes,
`fixed-floor-camera-box-2d-trace.json`118343bytes and
`floor-math-verification.json`. The final interval report SHA256 is
`1e04c4b06ff1bf6b1b83a278396cbd0948f398bf31b854d64e73fd13baa2b4d1`.
These ignored local files are not promised present in a fresh clone. Scripts
refuse to overwrite frozen diagnostics; rerun requires an explicitly reviewed
new output name/path. No raw cache is staged into Git.
