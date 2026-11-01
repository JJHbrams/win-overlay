# V28 orbital/lid correction

Status: F working correction, overall ART unapproved. Canonical e9 is immutable. A–E retain intermediate evidence; F is the limited correction under final review. No face-height, chin, global skull, healthy cheek, hair or lower-body redesign is included.

## What was actually wrong

The portrait opening is a rounded, asymmetric quadrilateral: a shallow long upper run, short medial descent, broad lower run and a more concentrated lateral rise. The black outer lash wing and tufts extend beyond the bright opening and must be traced separately. `source-contour-trace.json` records manual visible-opening points in the original portrait coordinates, with 1.5px uncertainty; `source-traced-eye.png` is a crop and uniform enlargement, not a transformed reference.

The retained R2 recipe widened eyelid X by 1.27, scaled the iris and thickened the upper ink, while explicitly leaving lid Z unchanged. That preserved the inherited superior bulge and lower arc. The ribbons were resampled from a Catmull–Rom curve with sinusoidal width; R3 densified and seated the same curve. The actual native does contain four visible separate dense ink ribbons (upper455/lower525 vertices per eye), with42 keys and Head Armature follow. Those are continuous bands, rather than an authored outer fan silhouette.

The lower lateral control path also contains a concrete spacing defect:2010→2009 has only0.270mm X span but2.054mm depth span;2009→2012 then jumps8.402mm in X. Mirrored1800→1802 has the same defect. Under the actual Armature→Weld→SS2→Smooth evaluation, that crowded depth turn produces a narrow inclined under-rim wedge. The original baseline skin-only oblique isolation demonstrates it; simply adding a local pad made it more visible in A. This was not diagnosed by comparing raw coordinates in different object frames.

Earlier comparisons concentrated on width/IPD, iris size and black-core thickness, plus hair-on full-head images. Those measurements do not describe turnpoint placement or curvature distribution, and the hair obscured the lateral contour and socket support. A numerical ratio improvement was incorrectly allowed to stand in for this missing shape assessment. The prior whole-face work nevertheless supplied useful cheek/jaw support; retaining that support does not freeze the orbital region.

## What changed

The opening now uses a shallow upper run and broader inferior run, with rounded transitions and a later lateral turn. The whole spatial map is applied to every key position, rather than changing Basis alone. The sclera/iris carrier receives a coherent0.35mm posterior and0.85mm inferior placement correction; it is an inherited cut carrier shell, not a newly built full spherical eyeball.

Small3D fields add lower-lateral support, a medial upper recess and lateral twist. Connected lower rings are gently faired in Y, retaining the rim, then the crowded lateral station is redistributed with a depth-aware continuous map. D/E skin-only macro views distinguish a coherent narrow lid top-plane from the former repeated scallop/wedge. Supported malar/front-cheek mass remains; no hollow is used to imitate socket depth.

The four ink bands are rebuilt from the actual evaluated eye-hole boundary, including every key. Two separate outer fan meshes supply tapered tufts; their42-key contact is seated against the evaluated skin and they follow Head. F retains E's rounded upper ink width joins and broader/shorter tiny tuft silhouettes. The visible aperture is controlled by skin and actual rim roots, separately from the black wing.

D's actual closed profile/oblique images revealed pinpoint white exposure. Owner/material isolation identifies slot1 sclera, not legacy glints, ink or skin highlight. An actual profile-pixel ray finds sclera0.091mm ahead of skin at world(0.056319,-0.050931,1.539154). E's extra skin-rim overlap did not resolve it and is removed. F restores D skin closure and applies a closed-key-only local carrier-edge tuck, maximum0.70mm inward plus0.10mm posterior, with4mm falloff. This is one3D shape for every camera, with no uniform ocular shrink. Neutral carrier is exactly D. HalfClose includes half the corrective delta; its actual four-view render is reviewed, not declared unchanged. Unilateral corrections affect the moving eye only. F fullClose shows no former white point in front/both obliques/profile.

Final unilateral inspection found a separate inherited key defect: e9 `Fcl_EYE_Close_L` opens the opposite eye systematically, upper boundary+0.39..1.37mm and lower boundary-0.48..3.31mm. In the corrected neutral foundation this becomes13.256mm opening against9.267mm neutral,1.43x. F restores only that key's opposite orbital patch to the actual neutral Basis; the active blink and other41 named keys remain exact. The ribbon/fan Close width factor also now tests closure per eye, avoiding thinned ink on the nonclosing eye. This is an isolated blink-key correction, not a hidden neutral design change or full-rig certification. Exact owner/key guards are in `opposite-orbit-CloseL-F.json`.

The actual2048 Face `UVMap` pigment was rerasterized on evaluated Face-slot0 triangles so lower fatigue and upper crease follow the new neutral boundary. The connected route remains UVMap→V27_ACTUAL_UV_PIGMENT→PigmentTimesControlledLight→controlled-light Emission. F neutral skin is exactly D, so its packed D pigment remains current. Exact scene-linear pixels are exported for replay. No source image was projected or warped into the texture.

## Source evidence and anatomical inference

The original portrait, profile turnaround and two unequal subtle-angle expression panels are used. Their cameras remain front0/0/-6.6, profile80/0/0, oblique25/+2/-15 and near-front-10/-3/-15, not opposing45-degree views. Original aspect is preserved; boards use only crop and uniform SRT. The old common registration is retained identically for before/after and adjusted only for actual768px render resolution. Its normalized eye/chin distance is not independently validated.

The source demonstrates the visible opening, upper ink, outer wing, lower broad segment and nearby cheek transition. Hair obscures part of the superior socket, so upper brow/socket depth is an anatomical inference, evaluated for coherent support and profile seating rather than claimed as a uniquely measured drawing dimension. Public text notes for [Steven Michael Hampton's Proko eye lesson](https://www.proko.com/course-lesson/focus-on-feature-the-eye) support planar/slightly boxy lids, real lid thickness and medial/lateral socket transitions. Only the public text notes were read; the video was not watched. These principles were adapted to Mia's stylized shape rather than imposing a generic realistic eye.

## Evidence boundaries

`reference-review.json` is D's intermediate source4 package; `reference-review-F.json` is generated from final F views. Every matched review includes source|baseline hairON|baseline hairOFF|candidate hairOFF|candidate hairON. Bare matte, skin-only and carrier-only macro views, low-front/opposite-angle views, actual neutral/.5/1Close, unilateral Close and small head follow are additional evidence. Initial quick matte settings/records were superseded: final records state actual768square resolution,15/3.75/2W lights, world.18/.1 and Standard/None, actual master key values and Head matrix_basis. Matte replaces all visible skin slots with linear.23, roughness.85. The ear cut in production under this rig exists in the matching e9 baseline; it is not a new eye geometry/UV failure.

These checks do not certify every expression combination, unilateral extreme, motion loop, physics or final rig. Source line/color/style differences, hair and body art remain separate. Valid hashes,42 keys and successful replay are technical checks, not ART acceptance.

## Integration

`replay_patch.py INPUT.blend OUTPUT.blend F` applies controlled key deltas plus dense ribbon/fan coordinates and exact pigment pixels. It accepts pristine e9 or e9 with disjoint original-Body-prefix corrections. It asserts all42 key names, unchanged3957-vertex Body prefix and unchanged hair coordinates. Fresh D and F replay succeeded. No numeric vertex-group remapping or raw-coordinate copy between differently rotated object frames is used.

The exact affected indices, world bounds and payload hashes are in `final-patch-manifest-F.json`. Shared-body edits are exclusively196 appended Face vertices3997..4477; original Body indices0..3956 remain exact across all42 keys. Root owns independent final review, canonical integration, validator/live checks and Git/Wiki updates.
