# Read-only parent-requested brow fleck diagnostic

Exact native C SHA4fc5504b91c61aef4c48d5e54542fd9add38fd5c6a97b42b8d9b94efbe33ed7a,
actual source front ORTHO512, BRW_Angry0.5. No GPU, live or native edits.

`brow-C-AngryHalf-first-hits.json` records1330 ordered forwardcamera subrays in
ROI(197,238)..(216,252), five subpixels per pixel. Actual directTransparent
legacy surfaces are skipped and actual BrowParamUV edgeOFF SmoothStep is
evaluated. This is not a universal evaluator of every arbitrary material node.

There are0 cases where another opaque surface precedes an intersected brow.
The first opaque owner is either the new `V31_SourceBrow_-1` or skin where the
brow footprint does not cover the pixel. Pale fleck pixels(200,245),(201,245),
(202,246) all have the new brow as first hit in all5 subrays, with edgeOFF
coverage1 and UVv0.239/0.223/0.380. Their actual image RGB values are
(162,144,136)/(198,175,165)/(158,140,132). Thus these samples do not support
legacy-card/skin depth occlusion as the cause of their pale rendered pixels.

Parent independently then demonstrated actual clipping ablation: unchanged
C pose/geometry/shader loses the flecks when a newly created review camera's
far clip changes1000m→10m. Child's final E proof explicitly records0.1..10m.
The ray diagnostic does not by itself prove a renderer-depth-precision cause;
the parent's actual ablation provides that causal evidence.
