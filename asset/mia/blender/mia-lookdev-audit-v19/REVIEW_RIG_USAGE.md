# Persistent v19 review copy

Open Mia_LookdevReview_v19.blend (SHA256 `f4b9e6096fe620977fd92528cc467d658a1b77a9bcbd50209bbefa4b13e2abc8`). Saved active camera:V19_Head_Front. Saved selected/render-enabled layer:original ViewLayer. Source87334607 remains unchanged. Build exit0; four fresh-open layer/camera combinations rendered successfully.

Cameras:V19_Head_* (ORTHO.29) and V19_Hair_* (ORTHO.48). Each has Front,Profile,Back,ThreeQuarterL,ThreeQuarterR,Elev20. All target(0,0,1.555),radius2,1000²,square pixels,zero lens shift. Head is close facial inspection; Hair is head/hair context and does not promise full-length ends. No per-view model fitting occurred.

Layers:
- ViewLayer:existing production materials unchanged,shown under controlled review color-management/world. It is still emission toon,not physically lit PBR.
- V19_DiffuseClay_SkinOnly:neutral18% diffuse override on linked original body and skin only.
- V19_SpecularProbe_SkinOnly:black-base Principled,IOR1.45,roughness.30 diagnostic reflection override.

Skin diagnostic layers exclude hair,eye/alpha cards and separate liners. Their empty eye apertures are intentional isolation,not deleted eye geometry. Originals are linked into V19_DIAGNOSTIC_SKIN_LINKS without copying or modifying mesh data. Source source-layer memberships are retained. The original world is preserved as a fake-user datablock; active world is V19_NeutralReviewWorld.

Neutral setup:Standard/None,exposure0,gamma1. White Area key60W,size1 at(-.6,-1,2.2);fill15W,size1.5 at(.8,-.8,1.8);edge8W,size.8 at(0,.9,2.05). World Background(.18,.18,.18),strength.10. Original lights are render-disabled in this review copy. Original production look was Standard/Medium High Contrast; comparisons must state which look is used.

The actual tested mode switch is:
```python
scene = bpy.context.scene
name = 'V19_DiffuseClay_SkinOnly'
for layer in scene.view_layers:
    layer.use = layer.name == name
bpy.context.window.view_layer = scene.view_layers[name]
scene.camera = bpy.data.objects['V19_Head_ThreeQuarterL']
bpy.ops.render.render(layer=name)
```
Use ViewLayer and V19_Head_Front to return to the saved starting mode. Layer render-enable flags matter; selecting a layer alone is not an assertion that all other render layers are disabled. No hypothetical add-on/UI control is required.

Preservation checks:156 source mesh coordinate/UV/key/material-slot/world-matrix records match exactly.59 packed image hashes match exactly. Production shader graphs were not edited. All setup changes are camera,lighting,world,view layers,diagnostic materials and additional collection links. No rig/motion/model/map changes. Recorded renders did not resave the native,so it opens in the saved front/beauty state.

Known finding remains:skin and hair production shader synthetic light vectors have opposite X signs,and Area lamps do not control their emission tone. Diagnostic clay/specular images expose forehead/cap and facial surface continuity issues; this file deliberately does not repair them. Reference cross-view calibration comes before further modeling/painting.
