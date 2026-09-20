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

## Click hit strip v1

- Generator: built-in image generation tool
- Output: `click-hit-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `81A5E56A699BAD55E8FEF1DC8AFAB2B0CF76A25B78DB05225AF2935ED99BA6BD`

```text
Create exactly four transparent, evenly spaced, front-facing full-body frames of the canonical
Bolttagu receiving a cute light bonk: neutral anticipation, slightly compressed head, peak
reaction with clearly readable > < eyes and a small w mouth, then soft rebound. Preserve the
approved character, outfit, palette, outline, scale, baseline, halo and ribbon silhouette.
Keep everything visible; no hand, cursor, labels, UI, watermark, background or extra character.
```

## Drag dangle strip v1

- Generator: built-in image generation tool
- Output: `drag-dangle-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `95A9CAA88C5E3DB4C42517D8680DA5692AB23D7ECCDAD48C192C7D3CB5129C9A`

```text
Create exactly four transparent, evenly spaced full-body loop frames of the canonical Bolttagu
dangling from one fixed invisible grab anchor above the head/hood and cutely struggling in air:
body swung left with a right-leg kick, center stretch, body swung right with a left-leg kick,
center recoil. Preserve identity, outfit, palette, outline and scale. Feet never touch ground;
no visible hand, cursor, rope, hook, labels, UI, watermark, background or extra character.
```

## Drop land strip v1

- Generator: built-in image generation tool
- Output: `drop-land-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `C41043A86FBFE6A5933B9A922E8ABABA8CA18BCF2DF730A9F8D07F3C0EA32BD4`

```text
Create exactly four transparent, evenly spaced, front-facing full-body frames of the canonical
Bolttagu released from a drag: short airborne drop, soft squashed impact, small upward rebound,
settled crouch recovering toward idle. Preserve identity, outfit, palette, outline and scale;
use a shared landing baseline and readable squash-and-stretch. No hand, cursor, rope, labels,
UI, effects, watermark, background, debris or extra character.
```

## Walk strip v2

- Generator: built-in image generation tool
- Output: `walk-strip-v2.png`
- Status: candidate pending human animation review
- SHA-256: `17FD1917725AD0BF3DAFD249ADD8E581F39A819AD703DA75666D70D2427E985E`

```text
Correct the canonical Bolttagu right-facing walk into exactly four ordered phases: contact,
down, passing and up. Keep head and torso scale fixed, one sole planted on the shared baseline,
and swing both clearly visible arms opposite the legs. Preserve the approved identity, outfit,
palette and sprite rendering. Avoid repeated leg poses, crossed-leg ambiguity, sliding feet,
missing arms, crop, motion marks, background, UI and watermark.
```

## Drag dangle strip v2

- Generator: built-in image generation tool
- Output: `drag-dangle-strip-v2.png`
- Status: candidate pending human animation review
- SHA-256: `E8EB378FA265EF402FC84275A6E4C83A6366E28AB2DBD300ACC1BDADC0EE1012`

```text
Correct the canonical Bolttagu dangling loop into exactly four slow, weighty poses around one
fixed invisible grab anchor. Both complete arms must remain visible from shoulder through sleeve
to hand, with both hands gripping the gathered hood above the head. Sequence slow left swing,
center stretch, slow right swing and center recoil. Preserve identity, outfit, palette and scale;
no cursor, external hand, rope, missing limbs, motion marks, background, UI or watermark.
```
