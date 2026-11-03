# Whole-head proportion correction — queued after body form

The user's latest 2026-11-03 request is to compare the completed body with the original art and enlarge the head above the neck if needed. Accepted internal facial form stays intact. This file records a read-only ownership/implementation plan; **no head transform has been applied**.

## Comparison and decision

Use original-aspect v06 whole-height front/profile/back/oblique, retaining one uniform crown-to-sole registration. Compare baseline scale1.0 against provisional1.075 and1.08 only after the body form is valid. Neither test factor is an adopted dimension. Record head-height/body-height, head-width/shoulder-width, chin/clavicle/neck gap, profile depth and hair extent separately. Do not normalize by eye distance or resize the body to conceal the mismatch.

2026-11-04 continuation: actual unchanged-hair/D-body source-camera front/profile/back/oblique now exists in `.mia-cache/body-h/ratio-baseline/`. A crown-fixed enlargement may lower the chin excessively; the prior neck audit found a smaller chin-height discrepancy. After body selection, test ONE uniform affine fitted jointly to corresponding crown and chin intervals, allowing its pivot near the mid-head rather than fixing the crown by assumption. A nominal scale around1.085 is only a preliminary hypothesis within uncertain hair-tip/pose traces, not another grid or selected dimension. Source-v06 long-hair differences are not a substitute for checking v22 grooming authority. No whole-hair scale or side extension has been adopted.

Fresh R3b read-only measurements put the Head-bone origin near(-0.000392,0.004743,1.491665)m and the previously recorded crown atZ1.692881m. Remeasure actual crown/hair bounds after body selection. Earlier chin predictions belong to an older registration and are not current targets.

## One coherent transform, explicit ownership

Transport the jointly reviewed reference pivot by the current Head-bone delta. For the fully head-owned surfaces use the same world affine `q' = p(t) + s * (q - p(t))` exactly once, preserving internal proportions, existing rest/pose and object parenting. The old crown pivot is historical, not an immutable anatomical constraint. Do not independently scale the facial features.

| Surface group | Ownership and order |
|---|---|
| Head/face/neck | Explicit head region of `MIA_V27_SharedHeadBody`, accepted Face690, and retained oral geometry of `MIA_V27_Foundation_Face`. Full uniform head plateau; smooth broad neck transition into the selected body. Place after shape-producing deformation and before outlines. |
| Eyes/lids | Bilateral `V28G_Sclera`, `V28G_Iris`, `V28G_InnerLid`; retain gaze and pigment. Normal transfer follows the affine. |
| Lashes/brows | Bilateral `V30_UpperLashes`, `V30_LowerLashes`, `V31_SourceBrow`, including selected lower-lid correction. Brow width precedes the affine; final Shrinkwrap follows, with any clearance departure recorded. |
| Oral attachments | `MIA_v002_EvaluatedLipCollar`, `UpperDentalCrowns`, `LowerDentalCrowns`, after existing jaw deformation. Do not also scale MouthAnchor/DentalJawHinge. |
| Upper hair | Both RootLining actors, Crown donor and three Gather actors already follow `MIA_V002_HeadHair_Carrier`. Transform evaluated surfaces once without double-scaling that carrier hierarchy. |
| Mixed head/body hair | Main, braid Lane0-2/Tail/Tie, `RimFlow_near_ear`, `RimFlow_far_neck`. Move complete logical scalp-root/backing families with the head and blend along strands toward body-draped lengths/contact envelopes. Head/Chest weights are only an ownership prior. A world-height cutoff or whole-Main object scale is insufficient. |

Initially disable projected BrowInk when proving real geometry. FringeTarget already samples evaluated Main, and ink samples evaluated brows/target; do not add another affine to those proxies or HeadFrame.

## Portable implementation and checks

The later helper must consume the **then-current selected body**, explicit head/neck masks or verified correspondence, reference/current pivot and scalar. Do not replay stale body targets, infer evaluated IDs from a prefix, replace parents, or clear unknown keys. Installation must be reversible and idempotent; retain UV/material/source-ID streams.

Check continuous neck sections, upper-hair root continuity and long-hair/body contact. Then actual neutral/blink/grin and modest head-turn checks must verify eyes, brows, mouth, neck and hair. Crown anchoring changes the effective anatomical pivot relative to the unchanged rig, so static proportion success does not establish dynamic correctness.

The read-only ownership study changed no model/native/GPU state. No source-scale, anatomy, deformation or overall-Mia approval follows from this plan.
