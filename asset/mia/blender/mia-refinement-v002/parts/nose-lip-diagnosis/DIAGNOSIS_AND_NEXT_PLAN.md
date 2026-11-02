# R3 nose and lower-lip surface review

Diagnosis and plan only. No new paint, material variant, render, native save, live/Git/settings or canonical edit was made. R3 rendering exposed a separate PresetTotal range bug during this task; its confirmed cause and successful root-fix parity test are recorded under `mia-expression-refine-v003/audit/`. That controller issue does not explain these neutral surface defects.

`current-active-routes.json` independently opens frozen integrated R2 SHA `eed408b82e9a6160377e92e97fe94ce9619a51393e1ec1d4c928f4a4fd498d82` read-only. All three active slot0 materials are the expected `MIA_v002_{owner}_RefinedD2`. Root reports R3 retains these neutral maps. The R3 source package itself was not re-rendered or relabelled as new evidence here.

## Exact active route

Owners: `MIA_V27_SharedHeadBody`, `V28G_InnerLid_-1`, `V28G_InnerLid_1`, slot0 only. `V30_ActualFaceUV` explicitly uses `UVMap`. Its output directly samples the following images; no mapping transform or V flip is inserted.

| Input | Active image/node | Packed SHA256 |
|---|---|---|
| Nose B art | `MIA_v002_Nose_B_sRGB`, 1254 square sRGB / `V002B_NosePaint_sRGB`, Linear | `b34942233d1da6576b657588c947f5fc12cbb35e83b78f7622874bd1ed8071a0` |
| Old feature controls | `V30_ActualLid_FeatureControls_RGBA.exr`, 2048 square Non-Color, CHANNEL_PACKED / `V30_ACTUAL_LID_FEATURE_DATA` | `09b4bf935a2b60b3ca977575a87ef7d281c386e7eb5b0e2b4ae0abbe789e0919` |
| D art | `MIA_v002_SmoothFatigueLip_D_sRGB`, 1254 square sRGB / `V002D_PaintedSmoothFatigueLip_sRGB`, Linear | `fe89c84c093186c37e1f7eb51abfcefa49f3ed042c51324ef734faf731cf80a0` |
| Actual32 lip controls | `MIA_v002_D_Actual32LipControls`, 2048 square Non-Color, CHANNEL_PACKED / `V002D_Actual32Mouth_Data` | `fe66cab9f5b0a73e3893947e9a752a8085c23cf5bd65a4e451ba12ec39690c36` |

Nose: B RGB is mixed over retained A/original pigment by `V002B_NoseOnly_AEyes_OriginalLip`. Ownership is UV rectangle `[.455,.30,.545,.45]` times old feature Alpha. D2's `V002D_Paint_KeepBNoseAndAFold` retains that nose signal. It enters `V30_DirectSourcePigment_NoCleanup` Color2. The direct mix still uses the original feature gains, including `V30_NoseLipGain=1`.

Lip: D RGB is divided by the measured blank lip skin color, then multiplied onto `V29_OriginalVsSurfaceBypass` by `V002D_AuthoredLipContrastOnPrior`. Darkening is retained; brightening is permitted only by Blue/Alpha in `V002D_HighlightOnlyOnActualLowerEdge`. `V002D_Actual32LipOverFatigue` supplies the selected color. Within the lip replacement domain, direct pigment ownership is precise Alpha times NoseLipGain and original root fade. C's broad pale lip route is bypassed.

Green is the actual32 boundary seam support. Blue is a tapered lower-edge trace displaced 0.0032 UV below the raw lower boundary. Alpha=max(Green,Blue). Blue core radius is 0.0008 UV with 0.0012 UV feather. The raw mouth boundary spans U .461277..538723 and V .242762..244692. These are numeric selectors, not the authored white accent itself.

Production: selected color → `V30_PigmentTimesActualLight` × `V30_GraphicLightVsOriginal` → restrained specular addition → `V30_IllustratedDiffusePlusSpecular` → `V30_CompleteSurfaceBypass` with SurfaceEnabled=1 → Emission strength1 → active Material Output, target ALL. `V30_GraphicNosePlaneLight` is a ramp of actual white Diffuse→ShaderToRGB luminance/4. Its gain remains 0.6. `V30_SpecularRelativeToC=0.3125` remains unchanged.

## Nose: evidence and likely cause

The existing selected-color nose is already fragmented into a weak bridge patch and isolated nostril flecks. Production retains those same accents. The old NoseLip=0 actual render largely removes them while retaining the same geometry. `existing-nose-evidence-crops.png` contains only cropped existing atlas/render pixels and shows that comparison. The selected-color ancestry contains UV/image/color operations and no Geometry, BSDF or ShaderToRGB node. Thus the accent layout is primarily a pigment/UV-projection result; actual scene lighting is not its sole cause.

The B atlas itself still contains a narrow triangular plane and two small dark nostril marks. Their projected native512 footprint is small. Authored shape/contrast and native projected sampling are more plausible first targets than a new nose sculpt. Exact aliasing versus paint-design contribution has not been isolated by a matched higher-resolution or single-branch test.

No UV seam was found in 74 shared raw skin edges wholly inside the nose ownership rectangle, using the preserved actual UV chart. The CPU image buffer's old Alpha is uniformly1 across that rectangle. Fragmented alpha islands or a broken UV seam are therefore unsupported explanations for this region. This does not certify every boundary or GPU texture derivative.

The existing NoseLip toggle is aggregate: it changes selected pigment ownership and its retained fallback. It does not isolate B art alone from its selector or the independent GraphicNose light branch. The latter can amplify contrast, but a duplicated-lighting cause has not been proved by an actual gain0 comparison. Source portrait nose coverage is partial; the profile reference is only80×72. Hidden bridge planes cannot be inferred as a complete target.

## Lower lip: evidence and likely cause

The source lower accent is crisp and bright. The existing selected-color lip crop is already pale and soft, before the actual-light branch. Production adds skin shading but does not recover the missing graphic edge. This points first to authored contrast/edge placement and its constrained sampling, rather than a lighting-only defect.

The actual D_Lip on/off proof changes137 native512 pixels, max23 RGB255. It proves the amendment reaches visible skin; it does not establish correct highlight placement or finish. The prior optional Blue gain0.12 probe changes80 pixels, max7 RGB255. That small actual effect was kept OFF and is not a completed refinement.

A CPU bilinear sample of the unchanged sRGB art, converted to linear RGB, across 724 Blue-core control texels gives median luminance ratio1.043 versus its measured blank-skin reference; about45.4% exceed1.05. The sample is approximate texture-space analysis, not a GPU mip or screen-pixel measurement. It supports weak contrast under the present support. It does not distinguish insufficient paint contrast from the Blue trace missing the brightest painted ridge.

The Blue trace was offset from the raw32 boundary. It was not proved to be the exact actual128 evaluated lower-lip highlight line in every view/expression. UV continuity and the actual80-pixel gain response rule out a wholly inactive branch, but registration, feather width and projected subpixel coverage remain open. Four D2 neutral-gray baseline/candidate pairs are RGB exact, proving D2 changed no geometry; inherited lip geometry can still differ from source and is not declared accepted.

## Bounded next-edit plan, not yet executed

1. Measure the existing B plane and D lip ridge against actual evaluated UV-to-surface projection in the current integrated neutral scene. Register the Blue support to the actual128 lower border and inspect the current grin/small-mouth endpoints. Change a selector only if that measurement shows an offset; keep its support narrow and attached to the actual lip.
2. Before painting another nose, isolate B selected pigment and GraphicNose gain independently in a minimal matched actual comparison when root grants a future GPU slot. The existing aggregate toggle cannot resolve that interaction. Do not remap UV, enlarge a polygon wedge or stack another shadow from assumption.
3. If the isolated pigment remains the defect, author one tightly bounded nose/lip atlas amendment through the built-in imagegen workflow, using the inspected actual atlas and source crops. Preserve all coordinates and every fatigue/fold texel. Target only the observed concise oblique nose gesture/tiny contact accents and a restrained crisp mouth seam with a short lower light edge. Do not infer a hidden full bridge, use a broad pale mouth patch, blur the whole map or substitute a gain-only change.
4. First review actual normal512 front/profile and selected-color comparisons with identical pose/camera/light. Continue to the required source views and moved-light/expression checks only if those two defects improve. Preserve fatigue, true opening, brow/lash geometry, Mouth C anatomy and original source aspect. No new whole-face design or model variant is authorized by this plan.

Existing proof paths:

- `review/D2-source512/paired/front-lip-source-color-production-crops.png`
- `review/D2-source512/paired/front-lighting-feature-toggles-normal512.png`
- `review/D2-source512/paired/D2-visual-diagnostics.json`
- `review/D2-source512/paired/reference-review.json`
- `../mia-mouth-rig-v002/review/C-styled6-lip2/paired/D2-lip-edge-toggle-crops.png`
- `../mia-mouth-rig-v002/review/C-styled6-lip2/paired/proof-diagnostics.json`

Those are historical actual renders with unchanged hashes, not new R3 renders. No ART acceptance follows from the route inventory, map resolution or hashes.
