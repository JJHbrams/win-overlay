# Astra Mia head checkpoint v09

Native: `Mia_Astra_Head_v09.blend`.

SHA-256: `63523417f451b5bc193d6cb2ef8940f4a0004f0db0e89f713d01f486cb408232`.

This is the actual Blender modeling pass requested with `gpt-6-astra`. It is a
body/head foundation checkpoint, not an approved final Mia face, finished
hair/garment model, or event-animation set. Independent art review remains open.

The input was the frozen v12 body/native, SHA
`54e2ea0843f67e400863ef4df3aee83eab27fb934e6442d8a080fc173ab5474d`.
The immutable original remains SHA
`9ef40cabbd2dd73f67e14e38fd54713d4c5ac0ceaf1ce4aa32b64af33f3830a6`.

Changes:

- Whole head and derived Head/eye rest pivots use the same 0.82 proportion map.
- Iris depth follows the existing X/Z 0.82 and owned 0.74 transforms. This
  corrects oblique surface slope instead of pushing cards in front of skin.
- Nose/mouth relief and mouth width are transported through all 44 shape keys.
- Thirty-six nearby Body Head boundary vertices are matched without welding or
  deleting source geometry; the maximum handoff correction is about 1.61 mm.
- Narrow lower-lid ink is generated on existing UV triangles and packed as a
  separate mask. Original pigment pixels and UV coordinates stay unchanged.
- A smooth orbital/bridge map raises evaluated iris height by 9.38 mm; the
  chin-to-crown ratio changes from 41.43% to 47.06%. Crown/chin and total head
  scale remain fixed. Eye/brow/bridge/ear and rig rest points move coherently.
- Neutral Close is 0.48; both owned identity keys remain 1.0 during tests.

`fresh-reopen-verification.json` records unchanged Face topology/UV/key order,
4,249 protected Body vertices with zero displacement, identity-preserving
blink/gaze, and exact neutral restoration. `landmark-comparison.json` records
the evaluated orbital change. Preview PNGs are native renders, not concept-art
regeneration. Source files were not saved.

Production integration uses both files:

```text
tools/mia/blender/refine_mia_head_v06.py
tools/mia/blender/astra_mia_fatigue_v08.py
```

Call `refine_head(face, body, rig)` once after the existing v04 Face44 fit on a
fresh derived source copy. Call `set_mia_neutral(face)` after transient tests.
The main body builder is the canonical reproduction path; old one-off study
scripts are not the production entry point.

Low-poly skull contours and final facial art/texture resemblance still need
art review. The structural fixes and animation smoke tests do not certify
final character likeness.
