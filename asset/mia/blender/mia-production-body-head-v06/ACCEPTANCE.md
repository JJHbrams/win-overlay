# Mia body-head v06 acceptance contract

## Scope

This checkpoint is a native Blender body-and-head foundation derived from the
immutable 02:40 source and evaluated against the v06 body turnaround and the
confirmed expression sheet. Hair, garments, accessories, secondary motion and
event clips are deliberately out of scope.

## Acceptance criteria

| ID | Requirement | Required evidence |
| --- | --- | --- |
| AC1 | Keep v06 turnaround and visibility guide as non-rendering references; preserve separate body, face, and facial-part ownership, with no hair or clothing merged into skin. | Fresh-reopen owner manifest and native file inventory. |
| AC2 | Preserve Face42 topology, UV layers, key names/order/index correspondence and useful expression structure; preserve the source archive byte-for-byte. Source coordinates are immutable. Derived mesh positions may change to fit v06 only when that edit is transported consistently to Basis and every preserved shape key. | Source before/after SHA-256, derived topology/UV/key audit. |
| AC3 | Fit slender waist/abdomen, lower/outer chest form, restrained shoulders, pelvis/thigh emphasis and slimmer calves across front/profile/back/three-quarter. | Actual, clay, and wire multi-view renders plus landmarks. |
| AC4 | Show a mature Mia eye/jaw/neck direction in close views without using hair to hide defects. | Hair-free face/head close renders. |
| AC5 | Prove blink, mouth, gaze and arm-raise/forward, torso-yaw and knee-bend poses on the actual rig. | Pose render set and pose log. |
| AC6 | Reopen the generated native blend in a fresh Blender process and regenerate audit evidence. | Fresh-reopen audit report and proof render. |

## Non-pass conditions

This checkpoint cannot claim approval merely from a script completing. Any
unresolved visual mismatch, clipping, unavailable pose control, or missing
fresh-reopen proof remains explicitly recorded as a failure or follow-up.
