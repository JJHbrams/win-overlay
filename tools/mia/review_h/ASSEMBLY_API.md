# H assembly handoff

`assemble.py` exposes a CPU-only API; import and `assemble(...)` do not write,
save, render, or start Blender. It directly reads the canonical immutable inputs.

```python
arrays, rows, report = assemble(
    actual_h_guide_path,
    cuts=CutSpec(guide_neck_z=ROOT_SELECTED_SAFE_CUT),
    neck_guides=observed_neck_guides(),
)
# Only after root's explicit candidate-output grant:
export_assembly(arrays, rows, report,
    CANONICAL / '.mia-cache/body-h/shape/assembly')
```

The critical guide cut has no default. The API rejects a nonmedial boundary
or any guide cap roof outside `|X|>.085` above the cut. A global1.37 cut can
amputate shoulders; choose the lowest safe plane from actual H geometry.
The initial root direction is identity donor/head, no head scale or global AP
motion. Source185 is excluded because jaw height/pose makes it unreliable as
the same neck station. The actual195/205 visible-guide observations are soft
elliptical construction constraints with their recorded uncertainty. Guides
outside the free collar are explicitly reported omitted, never called fitted.

The neck uses at most4mm row spacing (minimum8bands), actual neighboring guide
sections, and donor samples no higher than the cut+4mm. One row-bending solve
keeps endpoints/adjacent rows fixed and fairs endpoint displacement around the
physical ring. It reports the actual row residual and centerline slope.
This is a finite-row construction, not a promised C2 surface or anatomy PASS.

Waist and arm interior rows are the exact E float32 rows. Before reuse, the
actual E collar boundary/frames/resampled endpoints and row count are compared.
The comparison allows200nm float32 packing error at endpoints, reported rather
than falsely called byte-exact; interior row values are exact.

An optional later `headneck_delta(points)->(delta, Jacobian)` callback supports
an explicitly approved cervical edit. Explicit protected donor vertex IDs are
mandatory; their displacement is zero. Everything at/below1.34 is unchanged.
Only X/Y displacement is supported by this planar-cut API. It transforms WORLD
corner normals by the inverse Jacobian. Unretained cervical donor samples just
below the1.465 cut may move so the cut interpolation has a true neighborhood;
masking only retained source vertices would produce partial boundary movement.
No such callback has been adopted or run in the initial RAM test.

`atlas_h.export(geometry_path, assembly_path, output_dir)` is a separate,
explicit Blender operation. It unwraps only body faces, retains all3 old head
UV arrays, transfers donor hand/forearm ownership by the original source_face,
and labels unchanged lower guide arms using actual original component fields.
H collars are labeled from actual new ranges. A generic physically submicron
collapsed-fan repair uses shared(worldvertex,cornerUV) keys and reports every
changed face; no E-specific IDs are encoded. Normal-sized/line-like degeneracy
fails rather than being painted over. The final baker must still check overlaps
and map seating. No actual H unwrap or texture bake has run in this worker.

## Actual checks

- AST/import of both modules: PASS in existing Python/NumPy environment.
- Actual original11/E RAM assembly at historical1.445cut:8.45s,
  137917vertices/275476triangles, no new open seams. E waist/arm row reuse
  matched; maximum endpoint packing differences19.1/55.7/56.1nm.
  Both source195/205 stations were outside that short diagnostic collar and
  correctly reported omitted. No NPZ/native/PNG was exported by this check.
- Generic shared two-face submicron UV repair fixture: PASS; no fixed IDs.
- Actual H assembly, actual Blender UV, gray6, source comparison, material/native,
  orbit and animation: UNVERIFIED. Neither source code nor RAM success is ART.

No model/native/rig/UV/image source was modified. Engram reminder/activity tools
were not exposed, so no Wiki synchronization or activity call is claimed.
