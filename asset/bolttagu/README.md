# Bolttagu art pack

This directory owns the art used by the standalone desktop pet. The application must not read
assets from an Engram installation at runtime.

## Ownership boundaries

- `upstream/engram/` is an immutable snapshot. Never edit, optimize, recompress, or rename files
  inside it without creating a new inventory revision.
- `inventory.json` records the source revision, original relative path, byte length, and SHA-256 of
  every upstream file. `asset-build verify` treats a mismatch as an error.
- `derived/model/` contains reviewed model sheets and generation provenance.
- `derived/animations/<clip>/frames/` contains individual 512×512 transparent RGBA frames.
- `build/` contains deterministic runtime outputs. It can always be rebuilt from `derived/`.

The upstream repository does not currently declare redistribution terms for these character
files. Keep the snapshot local to this project until the rights holder confirms release terms.

## Art contract

| Rule | Value |
|---|---|
| Canvas | 512×512 transparent RGBA PNG |
| Coordinate origin | top-left |
| Ground pivot | `(256, 480)` |
| Clip naming | lower `snake_case` |
| Frame naming | zero-padded `000.png`, `001.png`, ... |
| Outline | dark violet, visually stable between frames |
| Silhouette | round head, bob hair, halo, right-side ribbon/ears, oversized hoodie |
| Palette anchors | charcoal `#262633`, violet `#4B3868`, teal `#4E8E88`, magenta `#F22BD6`, skin `#FFD6C6` |

Animation frames must keep the pivot fixed unless locomotion metadata explicitly says otherwise.
Generated art is a draft until its model metadata says `approved`; bulk animation production must
not begin from a `candidate` model.

### Canonical capture boxes

- Grounded clips use a 420px reference silhouette height and ground anchor `Y=480` on the
  512×512 canvas. One reference-frame scale is shared by the whole clip so pose compression and
  rebound remain visible without cross-clip size jumps.
- `drag_held_idle` and `drag_pulled` use a top-aligned scruff anchor at `Y=104`; they are reviewed
  separately from the grounded foot pivot. The held loop keeps the body centered, while the pulled
  loop sends the body and every limb in the same trailing direction and mirrors at runtime.
- Every build writes `build/review/contact-sheet.png` and `frame-metrics.json`. Review these before
  promoting generated strips from `candidate` to `approved`.

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
