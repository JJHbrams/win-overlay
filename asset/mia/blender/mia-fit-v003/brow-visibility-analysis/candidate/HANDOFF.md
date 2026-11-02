# Partial brow display: gate-corrected A

Use the three files listed in `handoff-manifest.json` together. Apply to the CURRENT scene in neutral head pose. The helper opens no scene, saves no native, edits no original owner and replays no old material or whole-scene data.

```python
import importlib.util
from pathlib import Path
entry = Path("C:/Users/antio/.codex/worktrees/mia-v002-face/win-overlay/asset/mia/blender/mia-fit-v003/brow-visibility-analysis/candidate/partial_brow_display.py")
spec = importlib.util.spec_from_file_location("mia_partial_brow_display", entry)
display = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)
report = display.apply_to_current_scene(strength=0.60)
# Reversible display control:
# display.set_strength(0.0)
```

The helper requires unchanged Main raw coordinate/topology hashes and the existing V31 `BrowParamUV` convention. It reads actual current evaluated brows and Main, including their current deformation modifiers. New rear actors can coexist. Re-evaluate ownership after any Main topology/fringe form or brow parameter-UV change.

Only new owners are created: a head-following frame/control, an unrendered live-sampling fringe proxy, two procedural ink actors, three Geometry Nodes groups and small new stock-node ink materials. Original face, eye, crease, brow, hair, body, keys, UV, weights, maps, rigs, cameras and light data remain unchanged. There is no shared Main material edit. New visible actors are tagged `mia_component='hair'`, so the existing semantic hairOFF diagnostic also hides them.

The proxy contains 4,648 triangles selected from the inherited Fringe-weight1 family. It samples the corresponding CURRENT Main evaluated vertices. This family is a spatial hint, not certified named-lock topology. Projection additionally requires a real foreground hit 0.5..40 mm ahead of the actual brow, a non-tangent surface, a valid component ID and a source-supported U span. Misses, cross-component faces, excessive depth jumps and stretched bridges are removed. Original forelocks/raw source IDs82525/93291 are preserved, never edited.

Source spans are conservative observed portrait runs: left X410..455 gives U0.229856..0.718935; right X520..551 gives U0.022267..0.349073. Tails hidden by the source are not displayed as complete invented brows. Each projected point sits 0.15 mm off the actual fringe surface. Source `BrowParamUV` width coverage and tapered U ends define the ink. The actual brow material is not copied; a small new charcoal/Transparent shader supplies the display.

Projection is head-relative, not tied to a review camera. CPU tests cover 13 expression/head states and confirm exact original-data preservation, current-Main proxy sampling, head follow, nonempty strips, valid hits, no cross-component faces and submicron offset arithmetic errors. Shader Incoming is transformed into this head frame; dot against −Y gives frontal display, with a smooth0.40..0.85 angular fade. Profile/back angular appearance is not actually rendered yet. CPU head-follow is not a live viewport acceptance claim.

The first A four-frame proof was a real FAIL: zero changed pixels. Its +Y gate was reversed. The exact wrapper-context audit demonstrated alpha0 with the actual front/oblique camera, while front ink geometry lay ahead of Main. `history/A-wrong-incoming-axis` preserves that helper and report; `review/A-front-oblique4` preserves its actual images. The corrected helper differs by **only the dot-axis sign**. No source span, strength or geometry design changed.

Corrected actual proof is `review/A-gate-corrected-front-oblique4`. It uses four actual512 frames, matched before/after camera/pose, exactly three source lights and clip0.1..10 m. All PNG hashes match. Front changes603 pixels/max40 RGB255; oblique520/max39. Every change above1 RGB is confined to the brow region. Low-level outside changes reach only1 RGB. The producer inspected both actual views: partial strokes now read over the bangs while some oblique portions remain naturally occluded.

Source and detail boards are under that proof's `paired` folder. They contain actual native pixels; there is no candidate PNG draw-over. Original source aspect is preserved. The comparison is for brow visibility, not a new facial proportion fit. Overall source ART, actual expressive-pose appearance, profile/back behavior and same-file live EEVEE/sprite integration remain root-owned checks.

GPU is released. No full native snapshot was created. Root owns selection/integration. Braided source form remains deferred behind face/body, not dropped. No rear-hair, color/UV or broad face redesign is included.

Root reviewed the actual front source board and provisionally selected the partial display, pending actual expression, profile/back and live integration. `crease-diagnosis` is a separate CPU-only path proposal; it does not alter this brow helper or its rendered proof.
