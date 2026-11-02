# Whole-body posed construction checkpoint — target01 rejected

This checkpoint preserves the user-requested complete below-head 3D section/branch scaffold and its first actual static surface fit. It is **not an accepted body, garment, animation rig, or finished Mia**. No native was saved and no canonical/live scene was edited.

The exact input native is current R3b SHA `4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`. The user-confirmed primary body design is original-aspect v06 SHA `6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1`. Current facial form is accepted and protected. The old fixed-G3-thorax constraint was revoked by the user's latest body instruction.

## Current reproducible payload

- `scaffold-fullbody/guide-data.json`: R4 canonical frame1 posed whole-body guide;191 curves/16 nets, SHA `0ac66b8704f0cd40fa9922de05dd022b26201a63df4004d387a5df446b9b623d`.
- `scaffold-fullbody/neck-supplement.json`: actual-current neck4 rings/12 meridians/net through under-chin attachment, SHA `d9f0ec8f8b7e2b712bbfb64b42a4c552a1deb899be250665b654686e3b6f248a`. This establishes guide coverage; target01 itself freezes all controls above1.425m and has not fitted that upper neck.
- `posed-target/target-01.npz`: actual posed q0, target, local posed controls, and field. `install_posed_target_01.build()` creates a separate static object from the current scene, removes Armature/keys only on its private copy, and changes no original object. It does not open/save an older scene, inverse-map, or replay the obsolete rest56 patch.
- `inputs/mapping-frame1.npz`: exact frozen empirical Armature-only pose mapping from the separately verified pose-space helper, SHA `c36230677c7491af3ec35f1cd0dce579647ce3bad9e4c5db5495304fbd567045`. q0_local is posed; control_local is raw/rest-like and must not be used as posed.
- `inputs/scene_fingerprint.py`: frozen verification helper copied unchanged from canonical v3.2. No runtime topology/shape code depends on old untracked v002 folders.

Run pure-data generation with Python `fit_posed_target_01.py`; run `verify_posed_target_01.py` in Blender5.2.3 background with `--python-exit-code 2`. `install_fullbody_scaffold.install()` installs R4; `install_neck_supplement.install(parent=R4_collection)` adds neck guides. These are hidden-render diagnostic collections by default. Renderer scripts require a root-allocated GPU slot and deliberately refuse to overwrite existing evidence.

External read-only inputs are recorded in `checkpoint-dependencies.json`: selected R3b native, original v06, source-light records and the existing component-ownership classifier in canonical. No full native or duplicate scene snapshot is included here. Historical A/B/C/D scripts retain their historical dependencies and are unselected; the current target01 replay and verification are the intended checkpoint runtime.

## Actual results and rejection

The first8 actual images are in `posed-target/actual-01`: gray front/profile/high-oblique/low-oblique, no-shadow low-oblique, normal low-oblique, and source-light fullheight front/profile. Source3 actual lights are60/15/8W, gray body3 are110/38/22W, clips0.1..10m, original pixel aspect1. Every pre-render record asserts actual active lights/material and pose. Fullheight comparison keeps the baseline's one sole-to-crown uniform registration; there is no shoulder/waist normalization or aspect stretch. Old gray frames are not automatically equivalent before/after evidence without exact fixture comparison.

Technical guard: all620 original data objects, original47 keys, rig/pose, UV/materials/weights remain exact; Face690 controls and18825 evaluated head vertices are bit-exact. A private q0 bake reproduces the entire baseline evaluated surface bit-exactly. Target01 preserves evaluated polygon/loop connectivity, with0 reversed common-baseline triangles and max evaluated motion27.318574mm. Two adaptive triangle rows switch the diagonal of one quad: this is **not Weld topology damage**. Weld's6micron group has0 eligible coincident pairs; the shared-alias block is a no-op.

Visual form is rejected. The shoulders/thorax are broader and more continuous, but actual gray/no-shadow/normal show a thin inferior shelf/double fold, flattened lower cup, and lumpy upper-inner flow. No-shadow retains the line, and normal emission shows a narrow ridge: cast shadow and pigment cannot explain it away. Existing underwear was inherited only to inspect the target; its V-like neckline, pattern, straps and UV remain unaccepted and must be fitted after useful anatomy.

Independent read-only evaluated sections at X45mm show lower-return tangent oscillation: about−9.6° at Z1195mm,−39.6° at1200,−13.9° at1205,−25.7° at1210; a27° turn over2mm near1203. Raw connected3571→3586→3603→3624 originally compressed/slightly reversed at Z1197.476/1197.186/1197.169/1197.468mm. Target01 opens these to1197.549/1199.549/1202.741/1208.458, while adjacent original-root253/254 stay at1195.126/1187.136 and only0.112mm depth difference. C2 interpolation of a displacement does not establish C2 smoothness of an already distorted final surface.

Next work is a finite connected pole→root→thorax/upper-pole surface patch with ordered arc-length flow, source-supported convex volume and a single natural attachment return. It must redistribute original-root and refined rows together, with boundary/tangent continuity and actual section/normal checks. The uppersternal/clavicular normal ripples also remain visible; a later illustrated clavicle accent must not become a sculpted groove. No further global scalar batch or native promotion is justified by this checkpoint.

The checkpoint-local pose mapping reproduces `target-01.npz` bit-exactly (SHA `939505a12fec4a80e074a40a31ef19ca34e42ccc8e2b5226387ef9895addea6e`). A fresh Blender CPU replay with the checkpoint-local v3.2 helper repeated the full preservation guard and success marker. All8 render files exist with the original successful render marker; the exact native is unchanged. Target01 still lacks source back/oblique, wholebody gray, moved light and bounded motion evidence, so the complete reference-review package is intentionally not claimed or promoted.

Earlier A/B are rejected local fairing; C improved width/height but hard arm masking broke lateral continuity; D's triangle-wise fade and forced inferred posterior made scars/large back bulge. Their small core proofs remain historical failure evidence. D2 changed transfer interpolation only and was never promoted. Upper-body-only and raw-T-to-posed shortcuts are superseded by the current canonical-posed complete scaffold.

Engram workflow was consulted for this scoped commit; no Engram reminder/activity tool is exposed in this child session. Branch/worktree/dirty scope were inspected. Existing same-task untracked v002 files are preserved and excluded from this checkpoint.
