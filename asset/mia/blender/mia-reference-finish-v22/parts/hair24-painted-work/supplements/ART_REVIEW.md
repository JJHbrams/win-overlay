# Rear gathering: useful partial improvement, not source approval

Native `Mia_HairStructurePaint_v24.blend`, SHA-256
`d3b230a52eb775a6b03fbeb5e690c7e2873761617deb85a36922b722ab3e2315`.

The actual saved-model rear/profile renders now show a closed, attached,
asymmetric gathered curl with broad unequal hair banks and connected pigment.
It replaces the small thin Fold/Binder appearance. Original detailed long hair,
face and body are unchanged. The painted close plates are actual Blender
renders; generated image inputs live separately under `../sculpt2`.

## Explicit view judgment

| View | Judgment | Observed result / residual |
|---|---|---|
| Front | UNVERIFIED overall | New rear gathering mostly occluded; no meaningful forward silhouette change. Existing extraction/surface problems remain. |
| Profile | FAIL source match | Bun is visible and attached, but inherits an overly high original Fold/Binder position relative to eye/ear and has different side convergence than the art. Ear/jaw/nape cut-out sheets remain visibly damaged. |
| Back | PARTIAL IMPROVEMENT, FAIL overall | Curl structure and strand pigment improve the tiny cord. Source knot sits lower relative to crown, and source upper-side locks converge more clearly. Current back mass remains broader and differently layered. |
| Left oblique | UNVERIFIED overall | Mostly tests preservation; existing temple/layer/neck faults remain. Art yaw is only estimated. |
| Right oblique | UNVERIFIED overall | Exact opposite-angle art unavailable; subtle expression panel is explicitly limited. Unpainted hidden/negative-side bun surfaces retain inherited ash. |

The source boards use the previously recorded hair0d registration scaled
uniformly to the current 760px render. The drawing is not an orthographic
blueprint. Crown-to-covered-nape normalization is excluded from dimensional
validation; it does not make the current bun placement correct.

## Surface and technical checks

- Three new 1024×1024 RGBA maps are packed and actually consumed through
  `V24_GatherPaintUV`, alpha fallback, grazing ink, scene-light toon response and
  bounded sheen. They add bounded bun pigment; they are not pure recovered
  source albedo or full-hair 4K detail.
- Baked coverage of each owner's UV domain: main 36.60%, upper 37.37%, tucked
  return 11.75%. Remaining texels use inherited ash; much of that area is hidden.
- `checker_back/profile.png` show longitudinal continuity and obvious density
  compression around tapered roots/inner returns. Zero-area UV triangles are
  absent, but uniform texel density or final unwrap quality is not claimed.
- `coloronly_back/profile.png` separates pigment from the target shader.
  `opposedlight_*` confirms actual light-direction response. The generated
  pigment still contains drawn tonal structure, so it is not labeled albedo.
- `validation.json`: three closed manifold meshes, no shape keys/modifiers,
  packed connected images, both UV layers nondegenerate, original DetailedHair
  geometry/topology/UV hash unchanged. Technical PASS is not art acceptance.

AC5 remains FAIL because of gathering placement/convergence and ear/nape
extraction boundaries. AC6 remains unfinished for the whole hair. The boundary1
relaxation probe is rejected and excluded. No final physics, rig or pose claim.
