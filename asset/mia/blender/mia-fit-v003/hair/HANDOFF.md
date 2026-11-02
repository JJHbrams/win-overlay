# Selected v003 hair producer checkpoint

Root provisionally selected **A+B color checkpoint**, not the eleven-lock geometry C and not whole-hair ART. Four actual views000/006/012/018 compile without errors; source-profile/front were checked after rear/opposite. Current normals remain unchanged. The lower rear/nape and source fine ink remain unfinished.

## Apply exactly once to the current scene

Required runtime files are `apply_baked_v29_crown.py` and these files under `v29-pigment/`:

- `current-UV-boundary-report.json`
- `baked-report.json`
- `rear-guide-report.json`
- `fallback-baked-payload.npz`
- `RecoveredStaticCrown_4096_RGBA.png`
- `RecoveredRearCrown_4096_RGBA.png`

```python
import sys
from pathlib import Path
hair_root = Path(".../asset/mia/blender/mia-fit-v003/hair")
sys.path.insert(0, str(hair_root))
import apply_baked_v29_crown
report = apply_baked_v29_crown.apply(hair_root / "v29-pigment", mode="combined")
```

The replay does not open any old scene or save a native. It accepts unrelated new face/body keys and actors, while requiring the guarded current Main hair coordinates/topology/source IDs, original six UV hashes and original owned slot0. It appends one UV/material, copies the current R material and preserves original POINT fields, weights, keys, actual corner normals and all original shader graphs. It never replays old v29 geometry/Fresnel/normal/light nodes. Images are packed into memory for root's single eventual native save.

`combined` means recovered old static pigment in the existing fallback across the owned Crown, plus a bounded rear Crown guide-art override. The live current guide remains outside that override; the fallback base can still change there. The conservative rear mask holds2651 front-visible Crown faces. Fringe/bang geometry, true forelocks, bun, braid, face and body are outside ownership.

Do **not** apply the rejected unbaked static graph or geometry C. Their saved PNGs/closure counts are not acceptance evidence. The failed live graph wrote PNGs despite EEVEE's explicit attribute compilation errors. A one-image bake reduced the load and actual one-frame probes succeeded before the four-view checkpoint.

## Evidence and limits

- `v29-pigment/combined-CPU-guard.json`:618 original owners protected except Main UV/material append; original six UVs/POINTs/corner normals exact and exactly4999 owned material indices changed.
- `v29-pigment/combined-probe-{000,006,012,018}/`: actual raw PNG/record, fixed source3lamps, finite0.1..10m clips and recorded pose. `combined-crown-*.log` has no shader errors.
- `v29-pigment/combined-checkpoint-012-018.png`: historical v29/current/selected comparisons. Historical geometry/normal/light contribution is explicitly separated.
- `crown-strip-A/on-model-flow-DATA/`: actual front/back numeric field on a temporary exact Main copy. It is not source-approved grooming or new paint.
- `READOUT.md`: full cause/candidate ledger and held lower-hair geometry owners.

The slate Crown sectors and rear paint continuity improve. Dark scuffs on held-front Crown and non-Crown/nape remain; v29 still reads cleaner overall. Lower folded/flat/torn geometry and the U-loop are not fixed. Body/face approval, garments, braid cleanup, secondary motion, final events, loops and30fps bake remain separate gates.

The model source gate remains **open for root integration**: no full candidate native was saved here, so this producer package must not impersonate an integrated saved-native `reference-review.json`. Root must form the integrated source/baseline/candidate package and run `validate_reference_review.py` before ART promotion. Preserved technical data and successful compiler probes are not that approval.

## Reproduction scope

The selected runtime is self-contained in the seven files above and a guarded current scene. Source extraction scripts read the retained v29 native with SHA`d7e2f7d...`; source scene bytes are not duplicated. Numerical baking uses frozen exact per-face old UV correspondence, current geometry input and the unique UV payload. Extracted source images are reproducible from that retained native and are not runtime dependencies. No new artwork was generated for this checkpoint.

No canonical/live/native/Git remote state was changed by this producer. Root owns merge/native/live/push. Engram activity/Wiki tools were unavailable in this child; repository evidence is recorded without claiming a Wiki update.
