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

## Drag dangle strip v3

- Generator: built-in image generation tool
- Output: `drag-dangle-strip-v3.png`
- Status: candidate pending human animation review
- SHA-256: `404C9689E5B338A42EAE8AA4345C79D1F8E5DEB54DD483B3DE103AFB6D3EDC62`

```text
Redesign the canonical Bolttagu dangling loop into exactly four ordered full-body frames. Hold
the character from one fixed point at the back of the hoodie collar/scruff, with a small gathered
fabric fold but no visible hand, cursor, hook or rope. Keep both complete arms and hands away from
the anchor: left arm up/right arm down, center pass, right arm up/left arm down, center recovery.
Let the body and legs trail below the fixed collar point with a slow weighty pendulum motion.
Preserve identity, outfit, palette, scale and transparent background; avoid missing or duplicate
limbs, overhead gripping, crop, labels, UI, motion marks and watermark.
```

## Drag dangle strip v4

- Generator: built-in image generation tool
- Output: `drag-dangle-strip-v4.png`
- Status: candidate pending human animation review
- SHA-256: `B479153F78B08EDD64BE55800CFC9E05722CB074C5799590785BE983F64114F0`

```text
Expand the canonical scruff-held dangling loop into exactly eight distinct ordered full-body
frames: left extreme, left return, center crossing right, right approach, right extreme, right
return, center crossing left, left approach. Keep one identical top-center gathered hoodie anchor,
both hands away from it, and both complete arms visible. Preserve identity, outfit, palette,
scale and transparent background; avoid missing limbs, overhead gripping, crop, UI and watermark.
```

## Click huff strip v1

- Generator: built-in image generation tool
- Output: `click-huff-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `5274ED70F861D07214619B4E3BCC65084BAFAFE9108B40CF032D834F361DE89F`

```text
Create exactly four ordered full-body aftermath frames of the canonical Bolttagu briefly huffing
after a click: tense >_< with clenched fists, stronger puff, cute >3< with inward fist shake, then
an easing >3< pout. Preserve identity, front-facing scale, outfit, halo, bow and shared foot line.
Use a transparent background and no impact stars, injury, tears, crop, UI or watermark.
```

## Drag held idle strip v1

- Generator: built-in image generation tool
- Output: `drag-held-idle-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `251B6B23D0303B71A13A814C31584C1182E1227AB285AAED6464B65FF1D5C443`

```text
Create exactly six frames of canonical Bolttagu held stationary by a fixed gathered hoodie scruff
point. Keep torso and anchor centered while arms and feet alternate small frustrated waves and
kicks. Preserve identity and transparent background; avoid directional lean and missing limbs.
```

## Drag pulled strip v1

- Generator: built-in image generation tool
- Output: `drag-pulled-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `3B93FC266C638FA0ACA6AC5ED7381BC48867DAD02102CE1F6E076B5630B55158`

```text
Create exactly six frames of canonical Bolttagu pulled toward screen-right from a fixed scruff
anchor while the complete body and limbs trail toward screen-left. Make a smooth struggle loop
that can be mirrored at runtime. Preserve identity, scale and transparent background.
```

## Drag pulled strip v3

- Generator: built-in image generation tool
- Output: `drag-pulled-strip-v3.png`
- Status: candidate pending human animation review
- SHA-256: `03E7B8C3C2B32728AD24F833B663A0FCD017BE1AE8F29FDC2F277F09E7AEFD79`

```text
Draw exactly six cells with the scruff anchor at top-center and the head, torso, both arms, both
hands, hips, legs and shoes all trailing diagonally down-left from it. Keep hands and shoes on the
same side of the anchor in every phase, changing only bend and stretch. Preserve canonical identity,
large transparent cell gaps and a mirrorable loop; avoid opposing limb directions and upright poses.
```

## Spawn in strip v1

- Generator: built-in image generation tool
- Output: `spawn-in-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `6DAC05173BBF0F8458744A6B9ACCC6E37A150FFFD29E8E52E9F5400F28BF2BD2`

```text
Create exactly six startup frames: glowing halo and sparks, faint head, head and shoulders, full
body materializing above ground, soft landing squash, then cheerful settled pose. Preserve the
canonical identity and shared final ground baseline on a transparent background.
```

## Despawn out strip v1

- Generator: built-in image generation tool
- Output: `despawn-out-strip-v1.png`
- Status: candidate pending human animation review
- SHA-256: `DD09CEDFE3427DFA02FADCD6647DBFB48A91C5F225EF91970E302C066FCDDF7A`

```text
Create exactly six friendly shutdown frames: small wave, backward glance and crouch, body
dissolving downward, head and halo remaining, fading halo with sparks, final faint glint. Preserve
canonical identity and transparent background; avoid injury, death imagery, text and UI.
```

## Cell-isolated animation grids v2

- Generator: built-in image generation tool
- Layout: 1536×1024, 3×2 grid, six isolated 512×512 cells
- Status: candidate pending human animation review

| Action | Output | SHA-256 |
|---|---|---|
| drag held idle | `drag-held-idle-grid-v2.png` | `3092FB43250B85FC478F4AD8021D0D83B4CA60E8E4097F8E6D1B2DF7E7FA527E` |
| drag pulled | `drag-pulled-grid-v5.png` | `AEA116821ADCC78F0EDCB821488B3D838D684C285D394FCF6DD70B2BA64D3DF6` |
| spawn in | `spawn-in-grid-v3.png` | `945CE2882EA706FA959995223A4312E6A710592D1F24F106FC0ED0A38389E1FC` |
| despawn out | `despawn-out-grid-v2.png` | `D4BDC2C7ED2A2D2B7954EC64C36FFE206087D45520D2C9D09F4984E20CE69F8B` |

```text
Rebuild each six-frame animation in reading order on a transparent 3×2 grid with exact 512×512
cells and generous empty margins. Keep every character part, halo, effect and particle inside its
own cell so no neighboring sprite can be cropped into a frame. Preserve the canonical identity,
scale and anchor. For drag-pulled, keep all limbs trailing in the same direction. For despawn,
keep every character pose front-facing: wave, lower hand and bend, then dissolve from the feet
upward without a turn-around pose.
```
