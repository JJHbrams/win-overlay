# v29 evidence and adaptations

## Creator tutorials already inspected in this conversation

- ChiChaArt, [head modeling](https://www.youtube.com/watch?v=6xuWKIplo7Q): prior selected actual frames/public timed transcript, not full continuous viewing. Relevant59:56 separate lash construction and1:02:34 thickness;54:17 inward lid return. Apply separation of skin, ocular carriers, lashes and cosmetic lines; do not copy the example's facial proportions.
- ChiChaArt, [eye outline](https://www.youtube.com/watch?v=b7WP4VdWZsw): prior public related transcript/chapters and selected frames;02:41–02:56 Solidify/vertex-group outline control. This is structural guidance, not proof that existing ink ribbons already reproduce Mia's upper/lower lash silhouettes.
- Canonical `../mia-orbit-thorax-review-v28/ANATOMY_SOURCES.md` and the existing Wiki export `D:/intel_engram/docs/_inbox/mia-reference-mcp-review.md` retain access levels and prior actual production observations. Wiki tools are absent in the current catalog, so no new Wiki synchronization is claimed.

## Official Blender support, checked2026-11-02

Search-result excerpts were accessible for the following primary manual/source pages. Full manual opens returned proxy402/403; do not describe those as full-page reading. Actual Blender5.2.3 runtime node/socket inspection and actual material-output tracing govern this implementation.

- [EEVEE supported nodes](https://docs.staging.blender.org/manual/en/latest/render/eevee/limitations/nodes_support.html): ShaderToRGB is an EEVEE-specific way to convert BSDF lighting to color. Current f0dead already uses this for diffuse lighting; this feature is preserved, not invented anew.
- [Image settings](https://docs.staging.blender.org/manual/en/latest/editors/image/image_settings.html): data images such as normal/stencil maps should not receive color conversion. Native scalar RGB controls are Non-Color; generated art PNG is sRGB and existing float pigment is explicitly stored scene-linear Non-Color.
- [Principled specular controls](https://docs.blender.org/manual/en/4.0/render/shader_nodes/shader/principled.html), [official source declaration](https://github.com/blender/blender/blob/main/source/blender/nodes/shader/nodes/node_shader_bsdf_principled.cc): roughness changes the specular lobe separately from reflection intensity. Actual v29 reflection branch/API is verified in Blender, not by copying an old socket name. This is controlled NPR rendering, not an assertion that ShaderToRGB/Emission is an energy-conserving physical skin material.

## Direct local findings

f0dead face has active Diffuse→ShaderToRGB→BW÷4→common warm ramp×packed2048pigment→Emission. No active texture-controlled specular branch exists. Body/head/neck share parts of their light routing; referenced node groups are not deep-copied by a material copy. Preserve or explicitly clone them before any edit and compare unchanged non-face dependencies.

Medial A is a real bounded skin/return correction. Its tiny lower fringe artifact was narrowed by actual no-iris/no-sclera/isolation renders and alpha-aware pixel rays to an alpha-zero iris exterior within micrometers of skin/wall. A depth-offset B did not clear it; C trims that invisible exterior using the active UV alpha boundary with all42-key barycentric remapping. Fresh native remapping/protection checks and actual images, not a construction formula identity, determine acceptance.

Generated pigment A/B are art candidates only. B is1254square; any2048 native bake has that art-detail provenance and does not become4K artwork. Procedural numeric controls are Blender-native UV/EMIT bakes. Layer masks prevent a generated background or painted eye-hole outline from substituting for geometry or changing the head/neck base color.

Actual v29 lash work adds a useful measured distinction: endpoint root contact does not guarantee intermediate contact, and a manifold tube can still invert. E's lower roots float during half closure. F fixes proximity but folds short tufts because independent root deltas fade into a remote fixed tip. G transports each whole short lower component by a proper local triangle frame; actual per-component signed volumes and quarter/half/three-quarter intermediates are checked separately from contact and images. This is a bounded implementation choice, not a claim that rigid whole-component motion is the right deformation for every hair or garment.

The paired dark strokes inside the white are attributed by actual layer A/B, not by shader-node guesswork. New lashes OFF and SharedSkin outline nodes OFF leave them unchanged; master OFF removes them. White is an active constant Emission receiver, and master has no geometry-node outline modifier. A reversible master mask removes superseded transparent ocular cards from evaluation while preserving all raw source data and active mouth/brow polygons; the strokes disappear. The renderer's exact internal transparent-layer mechanism is not claimed to be proved by this isolation.
