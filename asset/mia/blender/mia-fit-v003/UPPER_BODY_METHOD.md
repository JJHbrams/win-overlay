# Source-constrained upper-body reconstruction

Latest user scope expands this to the complete body below the head. The torso method is a subset of one neck/arm/hand/pelvis/leg/foot scaffold, not a standalone chest wrap. Original v06 remains the whole-height anchor.

The prior C field improves mass width/height but does not settle the pectoral/axilla/shoulder relationship. The user identified this missing integrated design. Original key/UV preservation and smoothing are not substitutes for a correct target.

## Construction to execute

1. Register the exact user-selected v06 front/profile/back/oblique at one whole-height scale. Separate observed skin silhouettes, cloth edges and shaded/inferred internal transitions.
2. Pick consistent height stations from lower ribcage through supported mass, lateral root/axilla, upper chest and shoulder. Use corresponding width/depth bounds to build actual3D section curves. A projected silhouette constrains an extremum, not an arbitrary interior vertex.
3. Connect those sections into a low-density control surface with a rounded ribcage behind the soft mass and continuous lateral support toward the upper arm. Include the anterior pectoral fold, posterior axillary fold and deltoid/trapezius support. Do not clip the root field at an arm-weight threshold.
4. Inspect the scaffold over the model and source projections, then high/low/rotating views. Where reference drawings disagree or are obscured, record the inference rather than fitting one view at the expense of another. Sparse drawings cannot provide CT-style unique reconstruction of internal tissue.
5. Fit the current body's coherent upper-region target and paired rest-joint placement to that scaffold. Preserve accepted internal facial form and lower-body regions; keep the narrow neck-join exception explicit. Test bounded arm movement before fitting the source underwear pattern, UV and neck/clavicle appearance.

## Pose-space prerequisite for whole-body fitting

Actual frame1 low-A pose and raw/rest T-pose controls are different coordinate stages. The fullbody guide exposed that the initial blue context used rest bone endpoints. Do not fit source-world limb guides directly to raw T-pose coordinates, even if their object matrices are identity. Read actual posed endpoints and build a posed working target first; map corresponding limb-local stations rather than equating image-y across different illustrated poses. Profile hands and back feet are explicit pose/correspondence limits, not instructions to shorten fingers or widen feet.

Transfer a selected posed target back through the actual Armature deformation. Do not assume a guessed linear-blend inverse if preserve-volume/dual-quaternion deformation is enabled. A small three-axis evaluated control-probe Jacobian can establish the actual fixed-weight affine response; verify a nonuniform-delta round trip. Rest-joint retargeting likewise needs a posed-aware strategy after coarse shape fit. Original face, raw key/UV data and rig pose remain protected until a declared, verified change.

## Primary artist evidence checked

Stan Prokopenko, [How to Draw Breasts – Form & Motion](https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/): public Lesson Notes, Form/Motion sections read2026-11-02; video not watched in this check. Describes the rounded ribcage, gradual pectoral-to-soft-mass transition toward the armpit, and shoulder-dependent change. Mia uses its own illustrated proportions and bra support; this does not prescribe a universal angle or realistic average shape.

Stan Prokopenko, [How to Draw Pecs – Form](https://www.proko.com/course-lesson/how-to-draw-pecs-form/): public Lesson Notes read2026-11-02; video not watched in this check. Describes skeletal placement, a curved front plane, clavicular/sternal portions converging toward the arm, and the lateral fold's shape/thickness under arm movement. Apply its structural continuity, not a muscular male surface design.

These references support a construction hypothesis. They do not prove Mia's new mesh, guides, underwear or animation acceptable. Actual source comparisons remain mandatory.
