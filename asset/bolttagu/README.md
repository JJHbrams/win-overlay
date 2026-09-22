# Bolttagu art pack

This directory owns the art used by the standalone desktop pet. The application must not read
assets from an Engram installation at runtime.

## Ownership boundaries

- `upstream/engram/` is an immutable snapshot. Never edit, optimize, recompress, or rename files
  inside it without creating a new inventory revision.
- `inventory.json` records the source revision, original relative path, byte length, and SHA-256 of
  every upstream file. `asset-build verify` treats a mismatch as an error.
- `derived/model/` contains reviewed model sheets and generation provenance.
- `derived/model/idle-rig/` contains transparent source parts for the three new idle expressions;
  `derived/model/idle-rig.json` records their per-frame transforms and draw order. These parts
  are composited at build time; the runtime still displays one atlas frame at a time.
- `derived/animations/<clip>/frames/` contains individual 512×512 transparent RGBA frames.
- `build/` contains deterministic runtime outputs. It can always be rebuilt from `derived/`.

The upstream repository does not currently declare redistribution terms for these character
files. Keep the snapshot local to this project until the rights holder confirms release terms.

The idle-rig sources are new bitmap assets generated with OpenAI image generation using the
project's existing `idle_breathe/frames/000.png` and approved expression previews as visual
references. Prompts requested the same character's head expressions (dazed, proud, pout) and a
transparent six-part cutout sheet; `source-sheet-v1.png` is retained beside the mechanically
cropped `parts/` images. No external emoji or character artwork was copied into the rig.
The `*_jacket-v2.png` parts correct an early cutout that accidentally treated the open jacket
front as fabric attached to each arm. The active rig now keeps the short front panels on the
torso and uses separate fitted sleeves. The original cutouts remain as unused source history.

## Art contract

| Rule | Value |
|---|---|
| Canvas | 512×512 transparent RGBA PNG |
| Coordinate origin | top-left |
| Ground pivot | `(256, 480)` |
| Clip naming | lower `snake_case` |
| Frame naming | zero-padded `000.png`, `001.png`, ... |
| Outline | dark violet, visually stable between frames |
| Silhouette | round head, bob hair, halo, right-side ribbon/ears, short open jacket over green shirt |
| Palette anchors | charcoal `#262633`, violet `#4B3868`, teal `#4E8E88`, magenta `#F22BD6`, skin `#FFD6C6` |

Animation frames must keep the pivot fixed unless locomotion metadata explicitly says otherwise.
Generated art is a draft until its model metadata says `approved`; bulk animation production must
not begin from a `candidate` model.

### Canonical capture boxes

- Grounded clips use a 420px canonical-idle silhouette height and ground anchor `Y=480` on the
  512×512 canvas. Each `animation-recipes.json` clip declares a `calibration` source rectangle;
  the compiler takes its alpha bounds to derive that clip's common scale and bottom baseline.
  The calibration cell is metadata and is not emitted unless `calibration.emit` is explicitly
  `true` for a terminal idle-return clip (and that extra frame is also declared in `pack.json`).
  New source sheets should place their canonical idle pose in the final cell for visual review.
  Production recipes should point `calibration.source` at the shared pixel-identical
  `canonical-idle-calibration-v1.png`, so separate sheets cannot quietly redefine head/body scale.
  Legacy sheets may use the shared `turnaround-v1.png` idle rectangle as a compatibility bridge;
  this does not mean the legacy sheet itself contains an idle cell.
- Rope/free climbing prepare and loop cells use a rear view so hands, feet, rope, and implied wall
  share one contact direction. The final action cell may use a rear three-quarter top-out pose;
  only the emitted canonical idle calibration frame faces front.
- `drag_held_idle` and `drag_pulled` use a top-aligned scruff anchor at `Y=104`; they are reviewed
  separately from the grounded foot pivot. The held loop keeps the body centered, while the pulled
  loop sends the body and every limb in the same trailing direction and mirrors at runtime.
- Six-frame generated sources use isolated 512×512 cells in a 3×2 grid. Every cell keeps a
  four-pixel transparent gutter; the asset test rejects visible pixels on a cell boundary before
  neighboring art can leak into a compiled frame.
- Every build writes `build/review/contact-sheet.png`, `scale-audit-sheet.png`, and
  `frame-metrics.json`. The scale audit samples one representative frame per semantic action on
  the same 512×512 capture box with center/pivot guides and visible-bound dimensions.
- The grounded standing reference is about 420px tall. Held drag uses a 404px top-aligned
  silhouette, directional drag keeps its 376px diagonal silhouette, and fall uses a separate
  centered 396px frame so compact poses are not perceptually enlarged.

## Action completeness gate

An action is implemented only when all four parts land together:

1. the semantic action and clip mapping in `PetActionClips`;
2. a distinct source strip and generated RGBA frames (static reuse is allowed only for fallback);
3. timing and pivot metadata in `derived/animations/pack.json`;
4. catalog validation plus an action-to-art completeness test.

Adding code behavior without its art makes the asset test fail. Generated strips remain
`candidate` until a human animation review promotes them to `approved`.

## Build

From the repository root:

```powershell
.\.dotnet\dotnet.exe run --project .\tools\Bolttagu.AssetBuild -- all
```

The command verifies the immutable snapshot, creates every declared clip from its model source,
validates frame dimensions/alpha/timing/pivots, and packs `build/atlas.png`. Re-running
it with unchanged inputs must preserve the `buildHash` in `build/build-manifest.json`.
