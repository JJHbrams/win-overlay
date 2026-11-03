# Surface review12 — static fullbody component checkpoint

E wider joins received bounded bare-surface approval from root and an independent reviewer. Material preflight10 is complete, with bra punctures/strap aliasing under investigation. New user neck/hip proportion feedback is being audited. **No full review native or final64 orbit has been saved/rendered.** The save gate remains closed.

The joined surface uses selected11 upper-body geometry, exact saved R3b head/face, and retained posed R3b lower body/arms. It replaces the old torso with real closed collars; there is no transparency-mask overlap. This is a static review assembly, without production weights, shape keys, retopology or animation certification. The source rig/data remain present for saved head/hair context; the new body is unweighted.

## Current E component

- Full joined geometry: `joined-expanded-E.npz`, SHA256 `4ddfc843920f11b3d8e49efff0f36794684f3ab6505ee8812b17b76e4f653bc0`; 139005 vertices/277652 triangles.
- Body-only portable appearance payload: `surface-v10-expanded-E-source-branches.npz`, SHA256 `e8d4d505e661a752ca3c1f9f7841d2109add1835b9e5ea333ac047a6fb759130`; 240195 body triangles. Original head faces are excluded from that payload.
- New actual per-corner atlas: `atlas-E.npz`, explicitly selected by installer/config. Body shader names `MIA_Review12UV`; original head active/render-active `UVMap` is preserved, along with all three old UV channels.
- Waist transition: actual planes Z1.145→1.005, 35 bands at4mm. Arms: 20mm proximal/45mm distal expansion along the actual25° arm section axes, 27 bands at3.969mm. Physical loop centers and adjacent sections retain the bent limb path. D3 neck rows remain exact.
- First/last actual row displacements derive from measured geometric sections, receive one periodic physical arc-scale regularization, then the remaining rows minimize discrete bending. No parameter sweep or absolute-ring shrinking.

`CPU-static-E-proof.json`, `installed-source-E-proof.json`, `discrete-section-proof.json` and `expanded-E-protection-proof.json` distinguish physical/attribute guards from actual appearance decisions.

## Exactness and numerical scope

All37273 original uncut head triangles retain source world positions, corner-normal inputs and old UVs. The complete head includes37457 triangles after cut interpolation. V27 POINT blend values and30 saved hair/eye/lash/mouth actors are preserved. No `compose_selected` provisional components or head scale are applied.

Custom-normal readback is not byte exact: uncut/protected head max0.041959° matches the unchanged-topology API roundtrip; the changed interpolated neck cut has76 corners above0.05°, max0.409875°. The strict0.05°/8e-4 bound applies to uncut/protected head. Cut-neck output is localized and reported, not labeled exact look.

`retained-correspondence-E.npz` covers every112061 old D3 point outside the declared expanded collars:111861 through strict vertex-coordinate matches and200 obsolete forearm subdivision points through the **same original source_face** triangle/barycentric representation. Those old source_vertex=-1 points came from the previous artificial Z1.035 split. The original donor triangles/vertices remain exact; maximum old float32 rounded-point residual is36.493nm, normal-plane residual29.329nm. This is representation change, not a nearest-surface exemption. All2992 D3 neck-row points are exact.

Two submicron new guide-waist triangles collapsed to one float32 UV point during SmartUV projection. Root authorized one-ULP connected-fan UV restoration, max below1e-7UV, with positive final areas. Raw atlas and exact IDs/pre/post areas/unchanged neighbors remain in `atlas-E-raw.npz` and `E-UV-microtriangle-restoration.json`. Geometry and old head UVs did not change.

The source has320 open edges and4 valence-four hand edges. They retain their exact physical source meaning; the new joins add zero open/nonmanifold/winding edges or intersections. These inherited features are not a global closed-manifold or visual approval claim.

## Actual evidence and failed predecessors

`seam-preflight8` is failed B; `seam-preflight-C4` is failed C; `seam-preflight-D3-4` is failed D3. Initial D and D2 were CPU-unselected: D2 produced no actual frame because its pre-render normal guard stopped. Their math statistics are not rendered ART results.

`seam-preflight-E-4` contains the four actual bare views supporting bounded E join approval. `material-preflight` contains ten actual E material/diagnostic views, all hairOFF to expose the body. The BODY ColorOnly neck image leaves the original face lit and is not a global pure-pigment comparison. All these are explicitly **unsaved component** actuals opened from immutable R3b4dc1; they must never be relabeled as images rendered from a future saved Review12 native.

The body appearance worker owns `../surface-appearance12`: real UV PNG maps, source-relative fixed3D garments/clavicle fields, binding evidence and material API. `maps-E` binds the E v10 payload/new atlas. Earlier maps B/C/D2/D3 cannot be substituted on this repacked atlas. Semantic-only E v9 had wrong hand labels; v10 inherits retained arms/hands/fingers through validated D3 SAME-source-face ownership. `source_branch_ownership.py` carries this policy forward.

## Gated saved-native/capture preparation

`selected-review.json` records E bare approval and keeps material approval false. `build_review_native.py` refuses to save until both gates are true. It prepares two named scenes, `Underwear` and `SkinOnly`, with two object instances sharing one mesh/UV and independent OBJECT-linked body slot12; old head slots remain DATA-linked. Five images per new material are packed with original PNG SHA verification. The planned single file is `native/Mia_v0.0.3_SurfaceReview12.blend`, default `Underwear`.

`verify_review_native.py` is prepared for fresh CPU reopen, exact geometry/UV/source-head correspondence, two-state/material/packed-image checks. It has not been run because no review native exists yet.

`render_review12.py` has explicit `prefly`, `orbit`, `diagnostics` and `baseline` modes. Root controls GPU grants. Final plan:32 angles×2 material states, same camera/world/lights; additional hairOFF source front/profile/back/oblique and original savedR3b baseline4 use0/90/180/30°, respectively. The32-angle orbit itself retains11.25° increments. Records include actual source-native hash, state, geometry/UV/map hashes, camera matrix/viewframe/target, pose/shape keys and lighting. Root owns source boards/GIF/presentation composition.

Only the authorized new surface-review12 folder is changed. Original R3b native SHA `4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1`, source images, old47 keys, canonical/live state and other workers' files remain untouched. No live settings, installs, uploads or push were performed.
