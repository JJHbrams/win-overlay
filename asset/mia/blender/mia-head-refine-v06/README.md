# Mia Head Refine v06 — integration contract

Input is exactly the v04-mapped `MIA_V06_FACE_SKIN` (Face44) and matching
`MIA_V06_BODY_SKIN` source-derived cap. Call `refine_head(face, body, rig)` once
after source fitting and after the cloned rig is parented with **keep world**.
The source Face and Body have Rz 180° object frames while the new rig may
legitimately be identity-world; do not bake another 180° rotation into geometry.

`refine_head` preserves UVs, vertex indices, Face42 prefix and all Face44 keys.
It also applies the required identity guide keys:

- `MIA_FaceArt_EyeProportion = 1.0`
- `MIA_FaceArt_OwnedBrowPlacement = 1.0`

The public `set_mia_neutral(face)` may be called again after any animation
preview reset. It sets the identity keys plus the tired neutral expression
guide. During blink, mouth and gaze proof, only `Face.*` / `EyeExtra` expression
keys may be reset; the two identity keys must remain 1.0.

After a builder has configured its scene, use the review output color settings:
`Standard`, `Medium High Contrast`, exposure `0.0`, gamma `1.0`. These are
recorded in `head_refine_report.json`; they are display settings, not texture
conversion instructions.

Final lookdev: Face slot 7 is active UV pigment image × normal-toon-ramp.
Body receives no facial UV image; it uses the same ramp response with a
constant multiplier sampled from unpainted forehead/temple pigment pixels
(Non-Color). The owned brow corrective delta is scaled to 0.55 while its key
remains 1.0. Clay keeps full Body plus temporary Face slots 0/7 only; blink,
mouth and gaze retain both identity profiles. Stored torso context is v04;
integration body is v12.
