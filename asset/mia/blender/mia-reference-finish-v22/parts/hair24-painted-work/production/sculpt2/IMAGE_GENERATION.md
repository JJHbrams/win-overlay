# Bun pigment input provenance

Producer: built-in `image_gen.imagegen` through the `imagegen` skill. No CLI/API
fallback. Outputs copied from Codex generated_images into this project directory.
The images are paint inputs, not actual Blender model evidence.

- `generated_back_pigment.png`: first generated output, original 1254×1254 RGBA.
- `generated_profile_pigment.png`: second generated output, original 1254×1254 RGBA.
- `registered_*_pigment.png`: 1024×1024 inputs registered with uniform scale and
  translation only. Exact transforms and alpha IoU are in `pigment-registration.json`.
- Bake coverage uses the intersection of actual geometry-plate alpha, registered
  generated alpha, positive surface facing and BVH visibility. Unseen pixels use
  inherited ash fallback.

## Rear prompt

Use case: precise-object-edit. Texture-paint input for an existing Blender hair mesh, NOT a new 3D design. Image 1 is the exact 1024x1024 orthographic rear-view mesh paint target. Image 2 is approved concept art STYLE ONLY. Paint ONLY the gray isolated curled hair-bun object in image 1, keeping every pixel silhouette, position, size, transparent background, overlap, fold boundary and recessed center EXACTLY unchanged. Do not copy the character, face or long hair from image 2. Add source-style ash-charcoal hair pigment and a small number of irregular tapered hand-drawn strand divisions flowing along the existing broad curved locks. Muted ash gray-brown, midtone sRGB approximately 122,111,110, restrained dark lines and soft thin lighter strand accents. Keep the three major existing curved forms, not a braided rope, not a donut, no concentric uniform stripes. Pigment/base color only: remove dramatic sculpt lighting while preserve subtle source drawn tonal separations; no specular white streaks, no cast shadow, no new geometry. Exact same square canvas and alpha silhouette as target. No text, no watermark. Return a single edited texture-paint plate.

Inputs: `paintplate_back.png`; `../source_back_detail.png`. Transparent output true.

## Side prompt

Use case: precise-object-edit. This is a texture-paint input for an existing Blender hair mesh, NOT a new object design. Image 1 is the exact square orthographic SIDE view paint target. Image 2 is approved character concept art, STYLE ONLY; do not copy its face or long hair. Image 3 is the already painted REAR view of this same object; match its muted ash-gray/brown palette, restrained hand-drawn tapered dark strand divisions and soft narrow lighter accents. Paint ONLY the isolated gray curled hair gathering in image1. Preserve image1 EXACT canvas framing, pixel silhouette, shape, scale, transparent background, all overlap boundaries and every major fold in precisely the same position. It is three broad volumetric overlapping folded hair locks, with broad unequal flow. Add hair pigment strands along their existing curved direction; no braid, no rope, no repeated perfect rings, no new geometry. Midtone sRGB about122,111,110, low contrast cel-painted natural hair. Pigment/base color plate: avoid dramatic lighting, strong white highlights and cast shadows. No text or watermark. Return only the edited SIDE-view square plate with real alpha.

Inputs: `paintplate_profile.png`; `../source_profile_detail.png`;
`generated_back_pigment.png`. Transparent output true.

The side output did not perfectly retain framing; registration reaches 94.16%
soft alpha IoU, versus 98.82% rear. This is a known input limitation. Geometry is
never changed to fit the generated paint.
