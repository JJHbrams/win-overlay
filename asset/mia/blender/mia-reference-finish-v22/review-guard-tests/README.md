# Provenance rejection checks

Executed against actual saved render metadata from local diagnostic5024. Originals and rendered PNGs were left unchanged; only temporary copies of metadata were corrupted.

1. A copied render manifest had its face source-package hash replaced with64 zeros. Actual Blender `render_integrated_review.py --diagnostics-only` returned exit1 with `Changed source packages require fresh comparison renders`, before writing a dependencies folder or rendering.
2. A copied render-records file had baseline/face/front PNG hash replaced with64 zeros. `compose_integrated_review.py` returned nonzero with `Render bytes changed after capture`, before writing a comparison board.

`result.json` records observed outcomes. These exercise new stale-evidence paths identified by independent code inspection. They do not test art likeness, and no failure image was passed off as an actual model render. Existing five reference-package corruption checks remain in the earlier reference-gate-verification.json.
