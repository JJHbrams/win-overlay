# Facial pigment D2 handoff

Current challenger is D2. C independently failed for granular fatigue and a broad pale lip patch. First D was rejected for pale under-eye ovals. D2 is a producer-observed improvement in actual front, profile and right oblique quick views; overall ART remains unapproved. Read `REVIEW_D2_QUICK.md` and `C_INDEPENDENT_FAIL.md` before integration.

Frozen v0.0.1 remains the canonical `mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Brows_Lashes.blend`, SHA `4572616f3457eb76707af19993b862b9711ad5ca303c097475021e3054b0216a`. No canonical, live Blender, Git or settings mutation was performed. Root owns integration and acceptance.

Current packed native is `native/Mia_v002_FacialPaint_D2.blend`, SHA `8b150df1eac3144aa496f5b57fea125c390eb19daa102fcd25f2afcdc44b1657`. The logical `native` directory is a junction to `D:/MiaArtifacts/v002/face-native-20261102`. Native C and rejected D remain intact. Do not remove A/B natives until root decides which historical native proofs to preserve; portable apply does not depend on opening them.

Authored D art is `art/Mia_SmoothFatigue_TracedLip_D.png`, SHA `fe89c84c093186c37e1f7eb51abfcefa49f3ed042c51324ef734faf731cf80a0`. It is the original 1254-square built-in imagegen output, not a resolution upgrade. `art/provenance-D.json` records prompt, actual image inputs and hashes. Numeric `controls-D/D_Actual32Lip_FatigueControls_RGBA.exr`, SHA `fe66cab9f5b0a73e3893947e9a752a8085c23cf5bd65a4e451ba12ec39690c36`, preserves the original fatigue support and traces narrow seam/lower-edge ownership from the actual 32-vertex mouth aperture. It is a selector, not painted artwork.

D2 transfers the authored D contrast relative to measured blank skin onto retained prior pigment. It does not transfer pale blank background. Fatigue is darkening only. Authored light is allowed only along the actual lower-lip edge support. The C coarse paint route is bypassed. B nose and A upper fold are retained. Only slot 0 on `MIA_V27_SharedHeadBody`, `V28G_InnerLid_-1` and `V28G_InnerLid_1` changes. Mouth cavity and teeth materials remain untouched.

Fresh CPU preservation is in `audit/D2-fresh-reopen-guard.json`. `audit/D2-portable-replay-guard.json` also proves that replaying A through D2 on a fresh 457 reproduces the exact actual D2 material graphs, while preserving all mesh coordinates/topology/UVs/keys/weights/drivers/modifiers, original maps/graphs, and scene/pose/camera/light/world/color. The replay test did not save a native. Technical preservation does not establish source appearance.

Root can apply the delta to its current scene with this exact Python invocation inside its own integration script:

```python
import importlib.util
from pathlib import Path
entry = Path("C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-facial-maps-v002/portable_face_delta.py")
spec = importlib.util.spec_from_file_location("mia_face_D2", entry)
delta = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delta)
new_materials = delta.apply_to_current_scene()
```

The function opens no native, saves no scene, and copies no old geometry/body/hair/rig. It requires the original three active V30 skin/wall graphs and exact UVMap hashes. It deliberately rejects changed face UVs. New shape keys or unrelated mouth materials are not replaced. Current driver state must match graph preconditions. Root must independently compare its current owners before and after applying and re-render after any face form or UV change.

Keep `portable_face_delta.py`, `guard_helpers.py`, the four replay modules (A material, B nose, C eyes/lip, current D2 smooth), their required art files, `audit/baseline-guards.json`, A/B/C material-precondition JSON files, and the D control/trace/background-sample files together. `apply()` does not open historical A/B/C natives or deleted old-face snapshots. Packed final natives have no runtime dependency on those external files.

Full actual D2 evidence is `review/D2-source512/paired/reference-review.json`. All 41 PNG hashes are current; all four neutral pairs are RGB bit-exact. The source4 production boards, selected-color/neutral boards, front eye/lip crops, feature/moved-light board, `D2-visual-diagnostics.json` and `evidence-validation.json` are in that paired folder. Validator evidence is valid with no errors; ART is NOT_EVALUATED. Producer actually inspected source4, selected-color crops, neutral comparisons, toggles and moved-light response. Read `REVIEW_D2.md`. GPU is released. The separate quick9 package retains source/457/rejected-C/D2 comparison history.

`audit/D2-portable-manifest.json` lists exact paths, byte sizes, SHA256 values and roles for all 17 required portable files. Full render records separately retain renderer/native/image hashes and actual camera/light state. Do not re-run immutable render tags. After integration, use a new tag for the changed current scene.

Observed D2 improvement is a dark immediate lower rim and smoother muted mauve fade without C scratchy granules or first-D pale ovals. The pale perioral patch is absent. The thin mouth seam is restrained, but the source lower light edge remains too weak. Lip ART stays open. B nose also stays WIP: the original portrait is partly hair-covered, and the observed profile pointed bridge paint still differs from the tiny current plane. Later mouth deformation must be inspected using actual expressions; a static neutral pigment result does not establish deformation quality.

All original references preserve aspect. Front uses frozen IPD scalar and translation with zero extra 2D roll. Nonfront absolute proportions and roll remain excluded by the provisional frozen registration. Raw actual normal512 renders are retained. Cameras use clip 0.1 to 10. Original navigation coordinates and origins are unchanged.
