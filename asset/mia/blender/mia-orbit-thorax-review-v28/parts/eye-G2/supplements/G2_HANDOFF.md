# G2 bounded orbital correction

Native: `Mia_Orbit_v28_G2.blend`, SHA256 `77a992872c2b1590e9266f01767e0236e95507b644fe96de21fe20070cc7acfb`.

This is a reviewed eye/orbital working component, not complete Mia or full ART approval. Body, hair, broad facial style and final animation remain separate. F stays immutable as the contour/key correction; G1 is rejected for visible white/iris intersection. G2 is the clean structural continuation.

## Actual cause and correction

The inherited R2 recipe widened eye X while retaining the old curved Z paths, then used a Catmull–Rom/sinusoidal ink band. That explains the rounded crescent despite acceptable width/IPD figures. The source has shallow superior and broad inferior runs with localized rounded end turns. F corrects that contour, redistributes a crowded lateral depth station and preserves supported malar/front-cheek mass. The actual source trace and evaluated opening comparison are in `source-contour-trace.json` and `evaluated-contour-source-e9-F.png`.

The orbital problem was separate. The old white carrier is a curved open cap, not a flat card: after coincident-vertex welding it has37 geometric controls,48 faces and24 boundary edges. An open flattened carrier is compatible with the reference tutorial. However, its center is about8.7mm behind the iris center along world Y, and there was no inward skin wall at the actual open lid boundary. The isolated skin, alpha-aware/front-facing contact audit and high/low/diagonal production views demonstrate the missing relation. Merely making a full sphere, filling a7–10mm curtain or hollowing the cheek would not address it.

G2 adds six owned meshes: two513-vertex curved white caps, two469-vertex smooth iris carriers and two576-vertex rounded inner-lid returns. Each retains42 driven keys and Head follow. Each key is rebuilt against its actual evaluated rim and ocular state; the outer seam coincides with the skin. The dense white cap sits behind the actual iris with a continuous backing-depth field and clearance constraints. The iris retains its projected x/z and UV mapping, with a smooth concave fit and modest depth seating. The original source ocular geometry is archived in the master and hidden through an explicitly active Transparent output. It is not deleted.

The return uses a tangent roll at the skin edge, bends inward and reaches the ocular region. Its outer UV corners come from the actual Face `UVMap`; the existing packed scene-linear Face pigment route remains active. The outer F skin/master coordinates, all42 keys and hair coordinates remain bitwise unchanged by G2. No healthy cheek or jaw is hollowed. Dense ink bands and small fan silhouettes receive0.20mm actual side thickness; no individual-hair rig is claimed.

Root verified selected public transcript/frame evidence, not the complete video: [flattened open eye carrier,22:11](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=1331s), [concave iris center,24:42](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=1482s), [hide the eye and sculpt the socket,27:35](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=1655s), [inward lid wall,54:17](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=3257s), and [lash thickness,1:02:34](https://www.youtube.com/watch?v=6xuWKIplo7Q&t=3754s). These are paraphrased structural principles, not a literal realistic-eye target.

## Actual evidence

- `reference-review-G2.json` pairs original-aspect source art with freshly rendered corrected-rig e9 and G2 in front, profile and the two unequal subtle-angle views. Every board includes hair ON/OFF. `reference-validation-G2.json` checks integrity, not art acceptance.
- `full-orbit-audit/G2-continuous-yaw-pitch.gif` and `G2-orbit-contactsheet.png` use73 actual production renders, yaw0..360 and pitch-35..45, hair hidden, neutral pose. Raw frames and exact camera/native records are preserved.
- `trial-G2`, `wallproof-G2` and `deform-G2` contain actual high/low/low-right production, physical gray, skin+wall, wall-only, wire and world-normal views. `skinONLY` includes SharedHeadBody plus both inner-lid meshes; wall-only proves the opening is an annular return, not a filled plane.
- `renders/candidateG2` includes actual bilateral neutral/.5/1 at all source4 cameras, unilateral R/L at front/oblique, and Head±12. HalfClose contains half the corrective delta; it is not described as unchanged.
- `G2-actual-structure-audit.json` verifies source F master/skin42-key coordinates and hair exactly, component drivers, evaluated seam/contact and sampled head follow. The isolated high head-yaw normal corner is located in `G2-seam-corner-visibility.json`.

Independent review of the73-frame sequence, macro returns and limited deformation supports this bounded contour/orbital/lash component. Full42 combinations, motion loops, physics and a final rig are unvalidated.

## Honest limits

The wall/cap relation is sampled visible coverage, not a watertight weld: visible contact offsets span approximately-0.366..+1.958mm in neutral and reach+1.654mm at halfClose. Median contact is about0.12mm. No visible slit or exposure was found in the inspected rotating/high-low/deformation samples.

Seam positions agree within0.0004mm. Median normal error is about0.002degrees, but side+1 lower station50/evaluated vertex26858 reaches19.2–19.6degrees at Head±12 from nearest-normal transfer sampling. The evaluated dense lower ink covers that exact point by0.153–0.309mm in those captured views. It remains a recorded limited-rig residual, not zero all-pose normal error.

The first temporary diagnostic shaders had inactive second Outputs because default node names were Korean. Their actual world was.05/1 and matte was default.8/.5. Old images remain preserved and their metadata is audited separately; alpha-hidden geometry in the old opaque helper must not be used as visibility proof. The final corrected renderer clears node trees, sets active Outputs explicitly, preserves actual iris alpha and records actual lights/world. Fresh strict source4 uses actual60/15/8W and World.18/.1.

## Compact replay

1. Run `replay_patch.py INPUT_E9_OR_DISJOINT_BODY.blend F_OUTPUT.blend F` with the F payload files.
2. Run `replay_orbit_G2.py F_OUTPUT.blend G_OUTPUT.blend` with `v28G2-components.npz` and `v28G2-components.json`.

The G stage recreates the six meshes, per-corner UVs,42 drivers, named Head groups, Armature and seam-normal transfer, then hides the archived ocular materials and adds side thickness. It asserts unchanged input master/skin keys and hair, so a disjoint Body-prefix correction survives. The authoritative dependency hashes are in `final-patch-manifest-G2.json`. Root owns canonical integration, final live review, Git and Wiki updates.
