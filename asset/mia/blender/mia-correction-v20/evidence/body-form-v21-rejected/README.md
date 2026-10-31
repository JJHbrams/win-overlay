# Mia Body Form v21 — bounded loop sculpt, WIP

Selected for independent review: candidate2. This is a visible form correction candidate, not body art approval. Candidate1 is preserved but rejected for excessive inferior extension/pointed shadow. Exactly one initial sculpt and one visually justified revision were performed. Existing v20/r2 outputs remain unchanged.

## What changed and why

Actual source edges were traced into 16 radial spokes and four concentric breast rows plus their chest bridges. The concentric organization itself is valid. The problem was the compressed lower/outer return band and its abrupt transition into much sparser trunk rows. Instead of another spatial offset field or smoothing pass, the sculpt directly redistributes named B/C/D/E rows along cross-sections from the preserved principal-volume row A to observed torso anchors. Lower chest endpoint F positions receive small explicit corrections in candidate2. Actual connectivity is asserted for both mirrored chains. No topology was added or removed.

The first sculpt spread the inferior bridge too far down the rib surface, producing a long pointed shadow. Candidate2 brings those endpoints back near the existing fold while retaining more even band spacing. In fresh profile/oblique views, the former thin shelf-like attachment is broader. The lower/outer shadow band and some independent oval reading remain. No further sculpting occurred after this revision. Pelvis, groin, neck and the other previously open body issues were not addressed by this breast-only pass.

The apex and principal-volume control row remain unchanged; the detailed snapshot also finds identical evaluated breast apex. This does not prove every local volume is conserved, exact unclothed anatomy is approved, or the full reference body identity passes. The lower/outer form was deliberately redistributed. Reference bra borders are not modeled as skin borders.

## Artist anatomy source and access level

[Stan Prokopenko — How to Draw Breasts: Form & Motion](https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/), official Proko page, accessed 2026-10-31. Read the public Lesson Notes, especially Form and Motion. Did not watch the video or access premium materials. No private human reference was used or retained.

Applied construction principle: treat the mass as sitting on the curved rib surface, flowing gradually toward the pectoral/armpit region, with an upper plane and a returning lower plane whose fold varies with mass and pose. Those principles guide the loop placement; they are not an imposed numeric anatomy for Mia. See `anatomy-source.md`.

## Review these actual outputs

- `candidate2/review/close_front.png`, `close_profile.png`, `close_back.png`, `close_three_quarter.png`.
- `candidate2/review/clay_body_front.png`, `clay_body_profile.png`, `clay_body_back.png`, `clay_body_three_quarter.png`.
- Before close views: unchanged sibling `../mia-body-surface-v20-r2/before/close_*.png` from the same aa02 source and same diagnostic setup.
- `actual-sections-and-cage.png`: source control/evaluated sagittal section vs candidate2 evaluated section, unchanged pelvis section as a control, and actual source/candidate2 front cage edges. Each panel uses equal physical scale on its X/Y axes. These are mesh triangle intersections, not redrawn anatomical curves.
- `candidate2/control-loop-map.json`: all source ring IDs, per-sector verified chain IDs on both sides, cubic sculpt handles, sampling positions, actual before/target world positions and mirrored ID mapping.
- `candidate2/vertex-delta.json`: source hash and exact traceable local/world changes for integration.
- `candidate2/sections.json`: measured native control/evaluated triangle intersection segments. Source segment data is immutable sibling `../mia-body-surface-v20-r2/source-sections.json`.
- `actual-sections-candidate1.png` and `candidate1/review/` preserve the first attempt and its regression.

## Native, reproducibility and protection

Native: `candidate2/Mia_BodyForm_v21_candidate2.blend`
SHA256: `f6327eac832172ec18bf699da067d771f415eb79a51389176c64ab28b16ab220`
Source: canonical `mia-correction-v20/integrated/Mia_Corrected_v20.blend`
Source SHA256: `aa02b736452bc876abf6f81a09b94bad71eb15c5ced35834b6fde17b90f8b5a6`
Exact recipe: `sculpt_form_v21_revision.py`; initial recipe is `sculpt_form_v21.py`.
Blender command form: blender.exe -b --python sculpt_form_v21_revision.py -- --source ABS_SOURCE --output-dir NEW_OUTPUT_DIR

88 body vertices changed, all below world Z1.46. Body 3906 control vertices, no shape keys, 63505 evaluated vertices. Vertex IDs, topology, UVs, weights, vertex groups and modifiers preserved. The proof is `candidate2/protected-owner-audit.json`, backed by source and final independently opened snapshot files. All other objects' control/evaluated surfaces, matrices, pose, materials/packed image content and protected body control/evaluated points are exact. Every source material/image datablock is retained. Per explicit task instruction, use_fake_user was enabled on materials/images; those authorized lifetime-flag changes and derived user counts are distinguished from material node/parameter/content changes. There are no removed datablocks. The audit is a technical preservation check, not art acceptance.

Saved-native review uses copied canonical neutral diffuse rig, frame1 and unchanged pose. Standard/None, exposure0 gamma1, neutral world and white camera-relative key/fill/edge. Whole-body ortho1.8894209113 targetZ0.8397017428; close ortho0.70 targetZ1.12; all1024 square, yaw0/90/180/45, zero elevation. `candidate2/review/review-evidence.json` records all eight views. Review material/light overrides were never saved to the candidate. No image generation, 2D paint, warping, live Blender edits, source save, Git mutation or other-owner edits were performed.

## Status

Producer preference: candidate2 is the better bounded candidate for independent review. Remaining lower/outer tonal band, some oval separation and all other body art issues remain open. No garment or final-animation advancement is justified by this work. Source and both new candidates are frozen; hash inventory is `frozen-artifacts.json`.
