# Face surface v29: actual audit and staged proposal

This is preparation only. No model, shader, image pixels, scene settings or saved native were changed. CPU scripts reopened canonical `Mia_Foundation_v28_G2L.blend`, SHA256 `f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2`; the before/after SHA is exact. Geometry/medial-canthus and independent upper/lower lash gates precede application. Eye-worker final UV/owner bindings must be re-audited on its accepted native. Body L and its shader remain protected.

## Actual current surface

The shared owner has4647 vertices. Slot0 `V28_Orbit_ActualUV` owns1342 face polygons; it samples `V28_ActualUV_OrbitPigment_2048_D`, a packed2048² float EXR, `Non-Color`, through explicit `UVMap`. This is stored scene-linear **pigment**, not automatically pure albedo. Actual pixels already contain broad brown under-eye fatigue, upper-fold arcs, lip and nostril marks. These are flattened together; old Finish8 BasePigment/FatigueMask/FineLineMask datablocks on archived owners are not independent working layers on this current face.

The actual active route is:

`white Diffuse BSDF → ShaderToRGB → BW ÷4 → MIA_CommonSkinLightRamp`

`packed pigment × that light ramp → Emission(strength1) → active output`

Thus the current face **already responds to actual scene lights**. It is not the old fixed normal-dot-light shader. There is no connected skin normal/bump map, specular branch, roughness texture or displacement. The Diffuse BSDF roughness is a constant0. No unused legacy Principled nodes are counted as skin response.

Scene is EEVEE, Standard/None, exposure0/gamma1. Actual enabled area lights are `MIA_REVIEW_Key/Fill/Rim`60/15/8W; the linked world background is linear(.18,.18,.18), strength.1. Other stored light rigs are hidden. These exact actual settings are in the inventory; no GPU probe was run.

Slot1 `MIA_V23_Body_CommonLight` owns3894 body polygons with its existing2048 pigment and the same controlled actual-light family. Slots9/10 own72/178 head-neck polygons and mix their body-light branch with `V27_UniformHeadControlledLight` through the stored POINT attribute `V27_HeadMaterialBlend`. The group uses the same ramp with base linear(.82,.63,.55). The original Body prefix has238 nonzero-mask points, including97 transition points; its stored transition spans basisZ1.394..1.496. This is a stored per-point mask that follows deformation, not a shader cutoff in world Z. Existing body materials and the lower blend boundary must stay exact.

Both visible `V28G_InnerLid_*` owners use `V28G_ActualFaceUV_InnerLidSkin`, sampling that same face pigment/UVMap and light family. Face pigment replacement must bind there deliberately. Actual sclera is constant emission(.80,.82,.80); iris is a procedural UV/ramp emission route; lid ribbons and the current lash fans use charcoal emission(.015,.013,.017). They are distinct owners and outside the facial skin reflectance change. A surviving mouth-card Principled route is not evidence that the face skin already has specular.

`active-surface-inventory.json` contains all80 material routes assigned anywhere in the native, including archived owners. **Only22 materials are assigned to render-visible polygons**, across26 meshes; the authoritative scope is `actual-visible-surface-scope.json`. Zero-polygon shared slots and fully transparent ocular archives are not active facial surface channels.

## Art and map strategy for the parent decision

Preserve the original packed image as the baseline. Do not rename its flattened fatigue/crease marks into new layers. After the eye gate, author a new source-based pigment plus independently controlled fatigue and fold signals aligned to the accepted eye/inner-wall UVs. The reaffirmed portrait and confirmed expression sheet govern hue, mark placement and expression behavior. Dark-circle coloration remains distinct from light-dependent shadow; a painted fold must not stand in for the newly modeled medial/lid structure.

The existing2048 layout is adequate for a first controlled candidate; larger dimensions alone are not a quality gain. Proposed minimum active assets, subject to paint strategy and actual probe results:

| Signal | Intended actual use | Color space / ownership |
|---|---|---|
| New pigment RGB | Source palette, restrained makeup, lips/nose accents; feeds existing pigment×light multiply | Preserve linear EXR/Non-Color convention, or explicitly decode a new sRGB art PNG once. Never silently reinterpret old linear data as sRGB. Face slot0 and accepted inner-wall bindings. |
| Fatigue and upper-fold controls | Separate scalar gains/tints for persistent under-eye pigmentation and fold line; reauthored from source, not claimed as extracted from old flattening | Non-Color channels; may share one control image while retaining separate sockets and ablation tests. |
| Shadow influence, if demonstrated necessary | Modulates the existing controlled diffuse ramp locally while remaining driven by actual light; does not bake a large fixed cheek shadow into pigment | Non-Color signal only if connected and visibly justified. No blanket AO map. |
| Specular weight + roughness | Restrained reflection branch; roughness changes highlight breadth, weight changes its contribution | Non-Color controls may share an image. An actual closure/ShaderToRGB branch must reach the active result. Constant scalars suffice until spatial variation is justified. |

A metallic map, displacement, SSS map or generic skin normal map is not automatically needed. The modeled fold/eyelid surface comes first; a normal/bump signal is optional only if a specific remaining fine detail warrants it and it is not counted twice.

Image generation can assist **art pigment/style studies**, if the parent chooses it. Its result should be registered/projected to the actual UV surface and reviewed, rather than accepted as seam-safe UV, normal or roughness data. UV masks, island-aware dilation, per-owner bindings and native bakes should be deterministic/native. No new paint or data-map pixels have been authored in this audit. PIL was used only to display unchanged packed pixels and draw diagnostic graphs/wires.

## Shader prototype recipe after the geometry/paint gates

1. Reopen the accepted eye/lash native and verify protected body L, UV corner arrays, material assignments and the head-neck attribute. Copy only allowed face/inner-wall/head-region materials to the new candidate.
2. Preserve the working actual-light diffuse branch and its baseline output. Add new pigment/feature controls before its multiply; make each persistent feature independently bypassable. Preserve the existing head-neck base/ramp continuity.
3. Prototype a low-weight neutral glossy/specular closure sampled by actual light, with explicit roughness. Bound its displayed contribution before adding it to the toon result. Record the exact active sockets and light rule. This is a proposal, not an already implemented branch. Fade the new head-only contribution through a compatible anatomical mask without changing body shader or redefining its light rig.
4. Pack only consumed map signals. Record each image's actual color space, UV node, owner/slot and linked channel. Generate island/owner-aware gutters; verify eyelid margins and inner walls in close views under minification. Recheck alignment despite any unchanged UV hash, because geometry moves the feature footprint.
5. Use separate pigment-only, diffuse-only and specular-only modes. Compare feature masks enabled/neutral, spec0/enabled, roughness low/high and fixed versus moved light. A visible response in the active native is required; file/node existence is not acceptance.
6. Inspect neutral, half/full blink, unilateral closures, head-follow, source front/profile/both obliques and high/low. Preserve source aspect and common registration. Final source/rotation suite follows small probe acceptance; no GPU run was used for this preparation.

## Readable evidence

- `actual-pigment-UV-thumbnail.png`: unchanged actual packed pigment beside its actual face UV wire.
- `actual-active-route-thumbnail.png`: schematic of actual traced links, not an implementation render.
- `actual-head-neck-mask-thumbnail.png`: actual stored mask samples on the Body-prefix head/neck.
- `thumbnail-provenance.json`: packed/pixel hashes and diagnostic display transfer.
- `active-surface-inventory.json`, `actual-visible-surface-scope.json`: exact node/socket/image/scope facts.

Engram tools are unavailable; prior workflow/protocol notes were read and repository provenance is retained. No Git operations, native saves, live MCP or GPU work occurred in this preparation.

## Preparation completed after parent plan gate

Built-in imagegen edit A was rejected for an extra rim-like line. Targeted B is staged at `art-pigment-B/Mia_UVPigment_Art_B.png`, actual1254² sRGB, unscaled. Parent selected it only as a masked cosmetic art source; its drifting background must never replace the original linear pigment. Prompts and all input/output hashes are retained. No further AI iteration is planned.

`native-control-maps-v02/` contains two actual Blender-CPU EMIT-baked2048² float EXR controls with16px UV gutters. These deterministic selections are not AI-painted numeric maps. Makeup ownership excludes fatigue/fold cores to support independent gains. They are provisional data, not a claim that active native layers already exist. The older `native-control-maps/` is superseded.

`apply_surface_after_eye_gate.py` prepares the material-only candidate after an accepted eye/lash path+SHA is supplied. Only copied face/wall flat graphs are extended; every original nested material/group graph, original image/colorspace and mesh geometry is guarded. Native API construction and key drivers were checked in an unassigned temporary material without saving or rendering. The renderer reuses exact source-camera/light metadata and starts with three small clinical views. Actual spec/roughness response, blink-fold behavior and source alignment still require those probes after the eye/lash gate. See `STAGING_STATE.json`.

## Read-only peer-review correction before application

The first recipe faded only the new art weight; old-accent cleanup still changed deep-wall color. This was a real algebraic blocker. The corrected native graph computes the complete cleanup-plus-art result first, then mixes that entire result once against original pigment using the wall-root fade. A CPU-native EMIT point-sampling bake of192 actual wall-root UV stations plus8 feature/outside samples verifies fade0 equals original, fade1 equals Face, and half fade equals their complete linear blend, all with exact zero max RGB error. Diffuse factor returns1 and spec scale0 at depth; root controls equal Face. The proof records the builder SHA and original face/wall graph hashes, and application now rejects stale proof or a changed shader route. This is graph validation, not final material art acceptance.

Probe preparation additionally includes separate fatigue/fold/makeup gain pairs, native spatial spec/roughness controls versus individually flattened atlas-mean comparisons, and actual head-follow±12 degrees in front/oblique. Neither first native application nor GPU probes have run; the parent eye/lash gate remains the dependency. Final packed numeric EXRs should use losslessZIP with exact float round-trip verification; uncompressed master bakes remain staged until packaging.
