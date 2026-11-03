# Face and hair: expand after the body pilot

Honor the latest user acceptance of the face in CURRENT_STATE. Earlier wide-face
complaints are historical, not authority to rebuild an accepted face now. Work
only on current open items, with the user's annotated source separating the eye
opening, lash silhouette and makeup. Hair occlusion does not prove a missing brow.

## Confirmed professional source

Motomura / Arc System Works, original modeling slides:
https://www.docswell.com/s/ASW_Academy/5D2VY6-GG-Modeling

Public slide text read on 2026-11-03; video not watched in this side task.

- 27–31: tracing front/profile does not determine a coherent oblique face.
- 35: the oblique cheek silhouette merits deliberately placed supporting edges.
- 38–39: mouth corners have depth/thickness; avoid a single pinched endpoint.
- 42–47: brow/forehead depth; tilting the entire flat eye creates other-view
  failures. Receding the outer corner gives a more volumetric interpretation.
- 49–52: cheek/chin contours define oblique width; crushing depth to narrow it
  can produce a mask-like face that fails at high/low angles.
- The talk uses polygon modeling and vertex-normal editing, not sculpting or
  normal-texture baking. Do not confuse edited normals with a painted normal map.

These are shape principles. Mia's actual aperture, proportions and expression
remain the target. Do not apply an identical posterior displacement to every eye.
Keep lid/eyeball contact, orbital depth and cheek support coupled; smoothing must
not erase the needed cheek mass. Separate silhouette, shading and graphic ink.

## Production-process sources and limits

- Fusako, official public curriculum:
  https://coloso.jp/products/3dcgmodeler-fusako-jp
  Introduction/outline read, NOT paid footage. Lists rough face sculpt, retopo
  with lashes/brows, temporary projected face texture, hair part organization,
  final UV/paint and expression keys. This supports early look feedback, not
  claiming mastery from the outline. VRM runtime setup does not validate a
  Blender-to-sprite bake pipeline.
- ChiChaArt user-supplied head tutorial:
  https://www.youtube.com/watch?v=6xuWKIplo7Q&t=4712s
  Existing research note has selected segment/frame observations; this URL's
  1:18:32 is a user-specified entry point, not a newly verified technique timestamp.

Preserve the good Pixal-derived surface detail where useful. Disentangle semantic
hair parts deliberately: bangs, side locks, rear mass/central closure, gathered
hair/bun, braid and tips. Loose connected components alone do not establish these
parts, and one Blender object alone does not prove fused topology.

Before new high-resolution paint, diagnose inherited hair flecks with neutral
geometry, color-only and target shader views, UV islands, material output and
normal orientation. Avoid repainting a lighting/depth artifact. Refine fringe
gaps from the source before moving eyebrows just to make them visible. Verify
rear central closure in back and obliques, not a front-only hair approval.

Use blink/gaze/small mouth tests while topology is malleable. Stable shape/UV
precedes final expression combinations and hair physics. Existing bones, key
counts, transferred weights or static renders alone do not prove deformation.
