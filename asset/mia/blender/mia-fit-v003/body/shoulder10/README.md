# Shoulder10 — rejected one-map construction test

**ART FAIL, S10-AC1/AC2; not selected.** Root and the fresh reviewer rejected the
new cap lips, shoulder shelf/bar and profile neck-to-cap depression. The actual
source height mismatch decreases, but the new surface does not retain the
source's soft continuous shoulder. CPU and evidence checks are separate passes.
No further geometry variant or GPU batch was made.

The user explicitly designated tied-hair v06 as the exposed shoulder reference.
`source-rails.json` records original1536x1024 pixels, visible skin runs, omitted
strap crossings, source hash and the frozen wholeheight uniform registration.
`source-rails-overlay.png` is a numeric annotation, not new source artwork.
The front fit uses the actual projected roof maximum acrossY, not midplane hits.
The core front excess was46.24mm; one32mm hypothesis deliberately left residuals.
No source aspect/width or shoulder normalization was used. Oblique display
translation uses independently estimated pelvis/crotchX1326±8px and yaw40±10°;
its assumed world centreline is not a recovered3D point or camera calibration.

The map is `(x,y,z) -> (x,y,z - .032*Wx(abs(x))*B(z))`, with quinticC2 pieces.
X ramp.025..065m, plateau.065..150m, fade.150..195m; Z rise1.360..1.445m and
fade1.445..1.465m. It acts on final09, including competing thorax/trap/cap
surfaces, and is common acrossY. It preserves all67992 vertex IDs and135980
triangles, X/Y point coordinates,52448 vertices belowZ1.36,2398 aboveZ1.465,
and the11962-point/23520-triangle supported E breast envelope exactly. The
measured09 passage hits remain exact, including9.32353mm main lower opening
and the already-closed local roof slices. Original09/E/source files are held
by individual hashes. The failed08 offset/Taubin and old posed-row fits are
not inputs. Static09 does not contain originalR3b's rig/47keys; no production
native or original body owner was opened or changed in this test.

11348 vertices/23312 triangles move; maximum31.989mm. Analytical map det≥.294118,
sampled vertex det.294118..2.13122, max condition4.133, minimum transported-normal
dot.993398. No element flip, degenerate triangle or new tested nonadjacent
intersection was found. These facts do not certify form. Volume decreases
586.827mL, a substantial change. Actual normal change reaches54.98°.
Physical fixedZ sections change despite X/Y point coordinates being exact:
atZ1.40/Y0 outer width336.19→223.53mm; atX.08/Z1.40 AP span97.77→54.85mm.
Fixed-coordinate vertex holds do not claim continuous-plane cross sections
are bitexact at the boundary through straddling triangles.

`map-cause.json` isolates the actual failure: restoring height through the outer
X fade creates an outward slope term. AtY0/X.160..1625 the old slope−.914 becomes
+.103, with chain-rule terms−.352 and+.458. The roof rises about.584mm across
X.1575..165 instead of continuing downward. AroundX.170 the actual2.5mm tangent
turn grows4.15°→17.47° atY0 and5.25°→18.51° atY+.025. C2 displacement and a
positive Jacobian do not prevent a new cap ridge or concentrated slope.

## Actual saved-native evidence

The baseline is the saved small09 native, SHA256
`7bc207b804775b9637858fed8e9faf5d831f6ae034d62da6792522fe1e9c4158`.
The one small10 native was saved **before capture**, SHA256
`920f68dc3477db3c0a51fc7c22f2e086602f341f85daf183eadf9e1866167cf4`,
2,845,768bytes. Its NPZ SHA256 is
`cedb2844033eff973f82f3c45853c2a12fcd2c1dc44d6fc753f1d077eeb0a79d`.
`native/fresh-reopen.json` verifies raw/world coordinates and triangles exactly.
The native contains one headless static upperbody mesh, ten ORTHO cameras and
three lights. It is a rejected diagnostic guide, with no UV, weights, rig,
shape keys, actions, head/lowerbody integration or animation readiness.

`render_saved_pair.py` fresh-opens saved09 and saved10, then captures8 states
each: source front/profile/back/oblique gray, high/low gray and front/back
GeometryNormal. Both actual runtime fixtures use the same simple gray route,
lights, world, display and ORTHO camera (.4m, targetZ1.33, clips.1..10).
The changed crop is recorded and preserves the frozen uniform source metric.
There is no R3b context and no later-export relabeling of image provenance.
The16 actuals, four source boards and eight paired boards are recorded under
`actual/`, `reference-review.json` and `board-records.json`. The required
`reference-review-validation.json` passes evidence integrity only; ART is FAIL.

## Reproduction and integrity

Blender5.2.3: `C:/Program Files/Blender Foundation/Blender 5.2/blender.exe`.
With this folder's absolute path as `$folder`:

```powershell
python "$folder/build_candidate.py"
& $blender --background --python-exit-code 2 --python "$folder/audit_cpu.py"
& $blender --background "$native09" --python-exit-code 2 --python "$folder/export_candidate.py"
& $blender --background "$native10" --python-exit-code 2 --python "$folder/verify_native.py"
& $blender --background --python-exit-code 2 --python "$folder/render_saved_pair.py" -- --cpu-only
& $blender --background --python-exit-code 2 --python "$folder/render_saved_pair.py"
python "$folder/compose_review.py"
python "$folder/diagnose_map.py"
python "$repo/asset/mia/blender/mia-reference-finish-v22/validate_reference_review.py" "$folder/reference-review.json"
python "$folder/verify_saved.py" --root "$repo"
```

Build/export/render refuse overwriting their one-candidate artifacts. Do not
rerun frozen evidence producers. `verify_saved.py` is read-only and remaps
recorded `asset/mia` paths to an optional repository root after integration;
it never rewrites proofs or manifest. Two retained CPU setup-error logs record
the corrected Blender import path and NumPy2 batched-solve API; neither created
a geometry variant. No live UI/settings, full native, source-image edits,
upload/install, head scaling or push. Engram tools are unavailable; no sync claim.
