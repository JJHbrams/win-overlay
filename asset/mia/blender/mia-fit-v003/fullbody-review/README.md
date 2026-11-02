# Complete below-head scaffold review

`Mia_v003_BelowHead_Scaffold_R4.blend` is a small standalone construction-only
file (186,220 bytes):207 curves and17 hidden control nets, no production body
and no armature. It opens with an orthographic fullbody orbit center and
0.01..10m viewport clipping. The original selected R3b was not resaved or
replaced. `guide-scene.json` records its exact hash and fresh-reopen counts;
`save_guide_scene.py` reproduces it in a private factory-startup process.

`actual-R4-neck/front.png` and `oblique.png` are actual Blender5.2.3 renders of
the combined R4 fullbody and explicit neck guides: 207 actual 3D curves. They contain no
rendered production body, no construction control-net faces and no generated
replacement illustration. Camera matrices, orthographic scale, clipping,
native/guide hashes and image hashes are in `render-records.json`.

Colors retain the producer guide semantics: cyan observed skin constraints,
gold garment envelope, pink inferred sections, gray occluded limits and blue
structural core. The explicit blue neck supplement follows current posed skin
and a proposed clavicle/trapezius connection; it is not a newly observed naked
neck trace from the illustration. The mostly pink limbs are inferred3D rings
constrained by source silhouettes and the editing pose, not measured scans.

The guide covers the neck under the chin; shoulder/thorax/axilla; both arm/hand
branches; waist/pelvis fork; and both thigh/knee/calf/ankle/foot branches. A fresh
read-only reviewer inspected both images and passed **regional construction
coverage only**. Open section ends at wrist/hand, ankle/foot and pelvis/thigh
corridors are not connected production topology. Continuous surface, inferred
hidden anatomy and canonical pose correspondence still need checking.

The real fitted-surface hypothesis is separate:
`../body/posed-target/target-01.npz`. Its eight actual images and source/front
profile boards were reviewed and **rejected as a finished form**. Inferior
breast shelves persist with shadow disabled and in actual normal emission;
connected evaluated sections show a narrow tangent overshoot/reversal. The
old compressed rows were only partly redistributed, leaving a second return
at adjacent root rows. A smooth displacement field is not proof of smooth
final skin. All accepted face, original keys/UV/materials/rig and baseline
native bytes remain protected. No rejected surface is promoted by these guide
images or the independent coverage PASS.

Reproduce in a separate Blender process after the producer body checkpoint is
integrated:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' --background --factory-startup --python-exit-code 2 --python asset/mia/blender/mia-fit-v003/fullbody-review/render_guide.py
```

The renderer is append-only and refuses to overwrite its evidence images.
`--body-root` can explicitly select a producer checkpoint before integration;
that path was used for the first run. It does not open/save the live scene or
change source/native assets. The static garment boundary and hidden parts in
the guide retain their declared uncertainty; this is not CT reconstruction.
