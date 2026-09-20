# Turnaround v1 generation record

- Generator: built-in image generation tool
- Role of source images: visual references, not edit targets
- Output: `turnaround-v1.png`
- Status: candidate pending human approval

## Prompt

```text
Use case: stylized-concept
Asset type: game character production model sheet for a Windows desktop pet
Primary request: create a clean full-body turnaround concept for the Bolttagu character shown in the references, suitable as the canonical guide for later sprite animation.
Input images: Image 1 establishes outfit, hair, halo, ear-like ribbon silhouette, colors, and pixel-accent identity; Image 2 establishes the simplified round-cheek chibi face and proportions.
Subject: one consistent small chibi character with an oversized round head, rosy cheeks, purple-to-teal bob hair, magenta halo, dark oversized hoodie with purple trim, green SYS ADMIN shirt, short simple legs and compact shoes.
Composition/framing: one production sheet containing exactly four evenly spaced full-body views of the same character: front, three-quarter, profile, and back. All views at the same scale, feet aligned to one baseline, generous spacing, nothing cropped.
Style/medium: crisp 2D game concept art with clean dark outlines, flat cel shading, restrained pixel-art accents, designed to translate into 256px transparent RGBA sprites.
Scene/backdrop: transparent background.
Color palette: preserve deep violet, muted teal, charcoal, magenta neon accents, pale skin, rosy cheeks.
Constraints: preserve character identity and outfit across every view; hands and feet simple and animation-friendly; no props; no effects; no speech bubbles; no UI; no labels; no text; no watermark; actual transparent alpha background.
Avoid: extra characters, mismatched costumes, detailed fingers, photorealism, 3D rendering, complex perspective, cropped ears/halo/feet.
```

## Walk strip v1

- Generator: built-in image generation tool
- Output: `walk-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `78EB77823BBC34B4FE629E19E59C7D8A43039DD683AAA3C3C278E8502DBD9A58`

```text
Create one transparent production sprite strip for this exact Bolttagu character, using the
approved turnaround as the identity reference. Show exactly four evenly spaced, right-facing
side-view walk-cycle key poses at the same scale and on one baseline: contact, down, passing,
and up. Preserve the halo, purple-to-teal bob hair, ribbon/ear silhouette, charcoal hoodie,
SYS ADMIN shirt, simple legs, palette, outline weight, and cel shading. Full body in every cell,
no crop, no text, no UI, no effects, no extra characters, true transparent alpha background.
```

## Turn strip v1

- Generator: built-in image generation tool
- Output: `turn-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `84B791060AFCC4338A12CF096046C4A4118348916BAB10CDEA78416E36395023`

```text
Create one transparent production sprite strip for this exact Bolttagu character, using the
approved turnaround as the identity reference. Show exactly four evenly spaced full-body poses
that turn in place from front-facing to right-facing profile: front, slight right turn,
three-quarter right, right profile. Keep feet on one baseline and keep the same scale, outfit,
halo, hair, ribbon/ear silhouette, palette, outline weight, and cel shading in every frame.
No locomotion, no crop, no text, no UI, no effects, no extra characters, true transparent alpha.
```
