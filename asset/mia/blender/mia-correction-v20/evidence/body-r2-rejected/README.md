# Mia body surface r2 — rejected bounded experiments

Neither candidate is selected for integration. Keep the body already present in integrated v20 (source aa02b736). Candidate1's visible improvement is insufficient; candidate2 has a sharper inferior breast turn and excessive chest support in profile. Body art/AC2 remain unresolved. No additional sculpt iteration followed these findings.

## Read the actual evidence first

- `actual-sections-and-cage.png`: actual source control/evaluated intersections against candidate1 evaluated intersections, plus the source front cage edges.
- `before/close_front.png`, `close_three_quarter.png`, `close_profile.png`, `close_back.png`: fresh source close views.
- `candidate1/fresh-final-review/`: all four close views and all four whole-body views from the saved candidate1.
- `candidate2/review/`: two close and four whole-body views; profile is the rejection evidence.
- Original source whole-body comparison remains canonical `mia-correction-v20/fresh-review/clay_body_*.png`.

## Geometry observation and limited inference

The actual front cage has concentric radial rings around the breast center. At the inferior/lateral edge several rings converge into a compressed returning band; below that are much more widely spaced trunk edges. This is observed topology, not a claim that an independent ellipsoid primitive was used to make it. The sagittal intersection at X=0.065 shows a shelf-like return at the lower lobe, immediately followed by the steep chest wall. Both the control and evaluated surface retain it, so subdivision is not merely displaying a false cage crease. Candidate1 shifts the section forward but retains the shelf/turn. Its close front/oblique still reads as a closed oval. Candidate2 increases the recessed support but creates a sharper lower endpoint in profile, so it is rejected.

The pelvic coronal section shows candidate1 nearly overlying source across the iliac/upper-thigh arc. Its minor redistribution does not substantively change the high-hip and inguinal structure seen in oblique close review. The groin remains block-like; posterior glute/thigh transition also remains unaccepted. Reference underwear conceals exact anatomy, and its boundary was not copied into the mesh.

Next modeling work should redistribute the inferior/lateral breast attachment loops across the rib surface, with broader, more evenly spaced bridge rows and a continuously turning sagittal section, while keeping the lobe apex/volume. Start by repositioning existing loop rows with actual control/evaluated section review; if sparse bridge topology cannot support that shape, propose a separately owned remesh/retopology and explicit UV/weight transfer. The current fixed-ID integration contract cannot be silently relaxed. For pelvis, redistribute the front/outer pelvic-to-thigh bridge rows in depth as well as width, with frontal, coronal and oblique section checks. These are next-step hypotheses, not completed corrections or proven topology necessity.

## Native / recipe / audit

- Candidate1: `candidate1/Mia_BodySurface_v20_r2_candidate1.blend`, SHA256 `dfb5b33581e26301f7228abf3fd78ae17c03b933213b9c5f4d8a6ca9328ec093`; recipe `sculpt_body_r2.py`.
- Candidate2: `candidate2/Mia_BodySurface_v20_r2_candidate2.blend`, SHA256 `99213a5707bd52e4bddf1c6f0dea50ecf0fa71fef92cee16df3117152269e75e`; recipe `sculpt_body_r2_candidate2.py`.
- Both `vertex-delta.json` files trace source aa02b736 vertex IDs/local/world deltas. Mesh is 3906 control vertices, no shape keys, evaluated 63505 vertices. Existing armature/weld/subdivision/smooth/outline modifiers were not changed.
- Candidate1 deep audit: `candidate1/protected-owner-audit.json`; `source-snapshot.json` and `candidate1/snapshot.json` hold detailed records. Other meshes including evaluated results, head/body points Z>=1.46, matrices/pose/modifiers, topology/UV/weights/keys/groups, active materials and packed images remain unchanged. Breast apex was not reduced.
- **Overall protected-datablock audit FAIL:** saving purged seven pre-existing unused material datablocks (names in audit). No active material slot changed, but strict all-datablock preservation was not met. Initial manifest only checks active material slots and must not be read as this broader audit passing. Next native writer must preserve unused datablock lifetime explicitly before saving.
- Same-process deep audit hit Blender access violation on second open; independent-process snapshots completed and were compared instead. Session-only material `session_uid` is excluded; actual nodes/defaults/links and remaining material settings match.
- First CLI invocation omitted Blender's `--` separator and used the recipe's default v18 source. Its output is quarantined in `invalid-v18-default-run/`, never considered a valid v20 candidate. The two actual candidate directories both derive independently from aa02b736.

## Review conditions and limits

Fresh saved-native reviews use copied canonical neutral diffuse rig, frame 1, unchanged saved pose, no key writes; Standard/None exposure0 gamma1; white camera-relative lights and neutral world. Full-body ortho1.8894209113 targetZ0.8397017428, close ortho0.70 targetZ1.12, all 1024 square, yaw0/90/180/45 and zero elevation. Hair hidden only for renders. Review scripts never save their diagnostic material/light modifications. Supplementary profile/back invocation overwrote its small `review-evidence.json`; the complete image catalog in `render-catalog.json`, exact executable review scripts and logs retain full run provenance. No image generation/paint/warping was used. The section figure is a plot of native mesh triangle intersections.
