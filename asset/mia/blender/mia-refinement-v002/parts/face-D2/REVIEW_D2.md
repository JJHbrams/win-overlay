# D2 actual source4 review

D2 is the chosen producer challenger for a bounded fatigue cleanup. It improves the independently failed C paint by removing scratchy/granular lower-eye blotches and retaining a dark immediate rim with a smooth muted mauve fade. The broad pale perioral patch is removed. Lip lower light and B nose remain WIP. Overall ART is unapproved and needs fresh independent review.

The producer inspected actual normal512 source/front/profile/left-oblique/right-oblique production comparisons, selected-color eye/lip crops, selected-color/neutral comparisons, the feature toggles and actual moved-key response. Source aspect is preserved. The source portrait nose is partly hidden by hair and cannot be fully inferred. The low-resolution profile shows a pointed bridge gesture that still differs from the current tiny B plane. Nonfront registration excludes absolute proportions and roll; front uses frozen IPD scalar/translation with zero extra 2D roll. All cameras clip 0.1 to 10.

| View | Observed improvement | Residual |
| --- | --- | --- |
| Front | Darker immediate rim and smooth mauve fatigue; C granules and first-D pale ovals absent. | Source contact accents are more broken. Thin lower-lip light remains too weak; nose is WIP. |
| Profile | Smooth fatigue survives the angle without a new paint boundary break. | Source is only80x72 and partly occluded. Pointed bridge gesture and lip light remain unresolved. |
| Left oblique | Smooth contact/fade persists with hair on and off. | Source contact is less uniform and partially occluded; gaze and registration limit identity conclusions. |
| Right oblique | Granular fatigue is absent; no broad pale mouth patch. | Source has open mouth/upward gaze. Exact fatigue distribution, nose gesture and lip light remain WIP. |

The actual D_Fatigue toggle changes 6096 normal512 pixels, with maximum RGB255 difference61. D_Lip changes137 pixels, maximum23, confined to the narrow traced support. The lip effect is small and does not justify a completed lip-refinement claim. The numeric masks come from the actual32 mouth boundary; they are not a broad uniform painted patch. Mouth cavity and teeth are untouched. Later expressions must be inspected on root's current deformed geometry.

In the fixed/moved-light face rectangle, production changes by mean31.15 RGB255 while the selected-color signal changes by mean0.00016. This supports retained actual light response with the pigment path held fixed; it does not prove every painted tone is intrinsic source albedo. The old GraphicNose light branch and all original light controls remain unchanged. Feature toggles are diagnostics that expose retained fallback signals, not a substitute for authored paint.

All41 render artifact hashes are current. All four neutral-geometry pairs are RGB bit-exact. Baseline/candidate cameras and declared light states match per view. The canonical review-package validator reports evidence_valid=true, errors=[], ART=NOT_EVALUATED. Fresh native preservation and portable replay guards pass. Those checks establish scoped integrity, not visual acceptance.

D2 uses the same imagegen D artwork as rejected first D. The native contrast transfer fixes that output's pale blank-skin background without blurring the image, moving UVs, changing lighting or reducing the work to opacity adjustment. Fatigue is darkening only. Lip light is allowed only along the actual lower-edge trace. C coarse paint is bypassed; B nose and A fold remain separate. Original457 and all original geometry, UVs, keys, weights, maps, drivers, brows and lashes remain unchanged.

Full evidence: `review/D2-source512/paired/reference-review.json`. Exact portable invocation, native/art/control hashes and dependency rules: `HANDOFF_D2.md` and `audit/D2-portable-manifest.json`. First D and C rejection history remain preserved. No new paint or GPU batch is pending from this producer.
