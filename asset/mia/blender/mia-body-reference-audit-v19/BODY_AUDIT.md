# Fresh body reference audit v19

**BODY ART: FAIL.** This assessment does not inherit any earlier body-fit/subdivision/rig or topology PASS. No model edits were performed. Four actual diffuse-clay views and the4-row paired reference figure support the findings below.

Read first: body_reference_comparison_4rows.png. Each row contains canonical v06,visibility guide v06,and actual model. The native87334607 and diagnosticf4b9 remain unchanged; exact full hashes are in body-render-evidence.json. Render exit0. The existing lookdev protocol remains persisted in ../mia-lookdev-audit-v19/REVIEW_RIG_USAGE.md; this audit extends it to full-body framing rather than replacing it.

## Registration and limits

All four model views use the same whole-body scale:orthographic1.8894209113m,targetZ.8397017428,1024². Camera azimuths0,90,180,45degrees,zero elevation. Model foot minimumZ.0389120206 and mean posed upper-arm jointZ1.3784819245 are mapped to reference soleY946 and approximate shoulderY220. All reference/model panels retain their original1024px height; the contact sheet only crops and centers horizontally. No anisotropic target warp,body-part shrinking or independent per-view scale was used.

This is approximate shoulder-to-sole registration,not a calibrated anatomical overlay. The upper-arm joint is below the visible acromion contour,so shoulder-surface alignment has a systematic uncertainty. The illustrated views are not exact orthographic projections. Model arms are more abducted and hands/wrists differently oriented; the model is bald and skin-only,while the visibility guide still has short visible hair,bra and briefs. Do not infer skull height from the illustration hair top,or convert small screen offsets directly into required centimeters.

The saved neutral pose was retained without bone/key writes. Neutral Standard/None,exposure0,gamma1,18% diffuse override. The head-review light rig was uniformly broadened for whole-body coverage: white key200W,size2 at(-1.8,-3,2.5),fill70W,size2 at(2,-2,1.7),edge30W,size1.8 at(0,2,2.3). These positions rotate with camera azimuth,with identical powers/sizes,to keep the same relative illumination for every direction. The model itself is not rotated or reposed. World stays neutral(.18,.18,.18),strength.1. This explicit camera-relative rig is a diagnostic extension,not a claim of identical world-space illumination between orientations.

## Specific findings

| Region | Fresh finding and evidence | Gate |
|---|---|---|
| Breast upper/outer root and lower transition | clay_front and clay_three_quarter show separate oval lobes with nearly complete lower/outer borders and abrupt attachment into upper chest/axilla. clay_profile shows a suspended oval projection with a narrow chest connection. Smooth surface subdivision has not created a coherent broad breast-to-ribcage transition. | FAIL,high confidence in model transition defect |
| Breast exact size/projection vs concept | Reference profile/3Q bra creates a supported broad envelope; it does not reveal the underlying complete skin base or natural underside crease. The model's isolated-lobe reading differs visibly,but exact unclothed volume/underfold cannot be derived from the garment edge alone. | UNVERIFIED exact anatomy; do not copy bra outline into skin |
| Upper pelvis / hip | clay_front and3Q show an abrupt waist-to-high-hip corner and flatter bands across the upper pelvis,followed by straightened upper-thigh runs. Reference front/guide uses a more continuous waist-to-outer-hip-to-thigh curve. The back/profile show that the issue is volumetric transition,not only front width. | FAIL |
| Groin / inner upper thighs | Model front/3Q has a planar/block-like central transition and abrupt thigh roots. Reference briefs obscure the exact crotch surface. Therefore the visible modeling quality is insufficient,but the brief's drawn V must not be interpreted as an anatomical cut. | FAIL transition quality; exact concealed surface UNVERIFIED |
| Glute / posterior thigh | clay_back shows a broad,nearly level lower-glute transition; profile shows a concentrated posterior bulge. Reference guide suggests a more continuous curved buttock-to-thigh flow. Arm occlusion and illustrated pelvis tilt limit exact projection measurements. | FAIL cross-view continuity; exact depth UNVERIFIED |
| Neck / clavicle / shoulder | Front/profile/3Q show a narrow relatively straight neck stem joining a sharply turning shoulder/trapezius base; collarbone/axilla surface transitions remain uneven. The guide's base-of-neck/shoulder outline is more continuous. Arm abduction affects shoulder shape,so exact shoulder width is not approved or condemned from a single silhouette. | FAIL transition finish; exact width UNVERIFIED |
| Thigh / knee / calf proportions | Existing calf fullness cannot validate the pelvis/thigh. Knee height/leg curve differs in the registered comparison,but registration and reference pose uncertainty prevent a numerical proportion PASS or a prescribed global rescale. | UNVERIFIED; assess with pelvis repair,all views |

## What this does and does not establish

The main P0 is coherent body form,especially breast roots and pelvis/thigh transitions. A texture change,shader smoothing,or clothing overlay does not resolve those geometric readings. Conversely,this audit is not an instruction to inflate the bust,shrink the pelvis,or force exact illustrated underwear boundaries onto the skin.

The four model views are views of one unchanged3D body. Any correction must improve front/profile/back/3Q together under this recorded framing. A front-only silhouette match is insufficient; clothes made before these transitions settle will inherit the wrong underlying volumes and attachment regions.

Next bounded modeling gate should own breast root/axilla continuity first,then waist/iliac/upper-thigh continuity,then neck/trapezius/clavicle continuity,each with the same four-view comparison. Preserve the source archive and editable production data. Reopen all body art gates; technical validation is separate evidence and cannot substitute for visible reference agreement. No clothing or rig work was performed or proposed as a workaround.
