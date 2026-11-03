# H brief-border assessment — CPU only

Primary remains the existing fair Cartesian world-space pattern. The optional C2 correction below is **unselected**: a subpixel benefit does not justify installing extra complexity without actual material views. No geometry, UV, input copy, texture bake, native scene or GPU work occurred.

The old same-ray field-height residual was not an image-edge measurement. At source `[535,438]`, the +46.5 mm value measured the field at the first skin hit. The nearest **visible actual 3D garment contour** is only 2.815 original-source pixels away, at a different depth on the curved pelvic surface. This does not prove reference inconsistency or anatomical failure.

| Source profile point | Base visible edge error, px | Optional field, px |
|---|---:|---:|
| 535,438 | 2.815 | 2.815 |
| 545,430 | 0.436 | 0.436 |
| 575,421 | 0.068 | 0.068 |
| 608,432 | 2.089 | 2.089 |
| 617,438 | 4.954 | 4.516 |
| 625,447 | 4.599 | 4.579 |

The first three points belong to P20 (manual uncertainty1–3px); the last three to P22 (2–4px). Those are qualitative tracing ranges, not calibrated confidence bounds. The actual profile rays at `[524,462]`, `[557,425]`, `[567,422]` are arm-occluded; `[523,477]` and `[528,449]` miss the body. Their large edge distances cannot be fixed by forcing a contour onto an unrelated first-hit sheet. Source pose, body silhouette and hidden cloth return remain distinct uncertainties.

`profile_contour.py` extracts the fixed-world field's actual mesh intersections and checks the nearest projected segment against the whole body's exact foreground visibility, including arms. Its projected AABB acceleration agrees with the original full-body ray test on all11 source rays. The base and optional fields retain23 observed front/back knots exactly and two closed leg openings (266/239 crossings), with no open contour nodes.

`world_field.py` constructs **one** compact Wendland-C2 world correction, fitted only to the excess above P22's stated4px tracing range; all29 observed/inferred closure anchors are hard pins. There is no runtime camera dependence or parameter sweep. Sampled correction reaches2.417mm at triangle centroids; an analytic kernel-Lipschitz/actual-triangle bound certifies less than7.344mm everywhere on the pelvic triangles (budget7.384mm). Extracted contour projection changes are bounded by0.876/0.699/0.876/0.841px for front/profile/back/oblique; these include hidden contours and are not render comparisons. The observed improvement is modest, particularly where visibility changes which segment is closest.

Reproduce with the existing Python/NumPy environment, from this sparse worktree:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python tools/mia/body_surface_h/profile_contour.py
# Optional analysis only; never installed by the main baker:
python tools/mia/body_surface_h/world_field.py
```

Inputs are direct reads from canonical `D:/MiaWorkCache/mia-reference-work/win-overlay`: E surface SHA`e8d4d505e661a752ca3c1f9f7841d2109add1835b9e5ea333ac047a6fb759130`, source-authoring config SHA`bd6d2e14a9da1bc41393e4f249c118e30e6e460b47b0580289584f2d43446225`, and the original v06 camera/SRT. Runtime dependencies on the canonical appearance/source-seating helpers fail rather than silently substituting inputs. The capacity guard inspects100MiB before cache writes; it is not an atomic allocation or a heavy-writer grant.

Raw reports remain only in canonical `.mia-cache/body-h/appearance/` (84,271bytes at this checkpoint): baseline SHA`3a1fec1bcd1bb5dae5fd87f6c6bf025cecb37b13ce7d91b88b546edd3bb3c363`, optional candidate report SHA`a46bb08c2e65bcbcbe5cef9ca2044ed608af26577460c497518efc604d99cf23`, bound report SHA`ae77defc268e9afa9304e003fde59371dd4085bb2c39493fefb3b446633db87f`. They are not committed or copied into this worktree. Clone alone does not contain these raw reports.

Fresh H-surface seating, actual source|baseline|candidate four-view materials and independent judgment are still required. Reuse the verified bilinear-support4K baker, fair straps, actual source graphic clavicle support atZ1.37778 and actual head-boundary pigment; none of these are replaced or ART-approved by this CPU assessment.
