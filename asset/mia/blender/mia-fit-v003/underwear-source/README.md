# v06 underwear and neck graphic source pack

Source preparation only. Exact user-confirmed v06 SHA256:
`6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1`,
1536 x 1024 original pixels. No body, garment, UV, shader, live scene or native
was changed. Body/garment art acceptance remains open.

`source-paths.json` supplies 41 original-pixel polylines with view crop, role,
confidence, pixel uncertainty and observed limits. `*-pattern-board.png` compares
each unmodified crop with the diagnostic traces at the same uniform 2x scale.
`source-overlay-original-aspect.png` keeps the complete original 1536:1024 aspect.
Trace points are manual visible-pixel samples; no hidden arcs are fabricated.

The charcoal bra has a **scoop neckline**, short visible strap fragments, a shaped
cup-to-band transition, a distinct band lower edge, and small side returns. The
internal cup/band line is a drawn construction cue, not a confirmed anatomical
root or uniquely established sewing seam. Hair hides almost all rear bra design;
only two tiny visible lower-edge fragments are provided.

Briefs have a dipped upper waist, high curved leg openings and narrow visible
crotch turns. Front, profile, oblique and actual rear coverage remain separate.
The back center fold is labelled a low-confidence illustrated cue; underside
gusset and hidden seams are unobserved. Front triangle coverage must not be
copied onto the rear.

Neck/clavicle records distinguish thin graphic cues from soft illustrated
under-chin shadow boundaries. `appearance-samples.json` contains 10 bounded
source patches with exact XYXY coordinates, encoded RGB/sRGB medians and ranges.
These are **illustrated appearance**, with lighting and pigment mixed; they are
not physical albedo, calibrated reflectance or a medical model. The thin-line
patch intentionally includes antialiased skin/line mixture.

The existing body `scaffold-D/source-contours.json` was read and hashed as coarse
context. New garment-specific traces refine visible boundaries and split the
band into its upper transition and lower edge. Generated 8-view/E2F2 supplements
contributed no dimensions, points or color samples.

After the FINAL POSED body target is selected, seat scoop, strap, side-return,
band, waist, leg and visible crotch paths on that surface using corresponding
source projections and local surface constraints. Store each seated point by
mesh triangle and barycentric weights, then transfer through that correspondence
to final UV. Use path-relative surface coverage; do not use world-height masks or
raw T-pose coordinates. Neck/clavicle graphics follow final shoulder/trapezius/
neck fitting. Current underwear UV and active material routes were not audited
by this source-only task and remain an integration check.

Reproduce and verify:

```powershell
python asset/mia/blender/mia-fit-v003/underwear-source/prepare_source_pack.py
python asset/mia/blender/mia-fit-v003/underwear-source/verify_pack.py
```

The verifier recomputes source hashes and all patch medians and compares every
board's actual original panel against the exact uniformly enlarged source crop.
Actual four-board visual inspection is recorded in `visual-review.json`.
Engram KG/activity tools were unavailable; no synchronization is claimed.
