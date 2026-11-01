# WIP5 — local face surface correction

Current integrated/local editor checkpoint, not finished character art.

Native `Mia_ReferenceFinish_v22.blend`, SHA256 `2e52b717f471f93b1d248ff70ac5f9dbadd1f32adc111a79062487d9d9452e8a`.
Inputs: Face7 R19 `5677073262e4`, unchanged Body14 `98f34b4362b4`, unchanged Hair0d `0d7874821981`.

R19 minimizes curvature of final connected face positions with feature constraints, instead of adding smooth offsets to the old defective surface. Original ears are restored exactly after R18 introduced a pointed ear-base attachment. Independent low/level/high multi-angle and four-source-view review accepts the smoother lower-orbit/malar/buccal transition only as a local WIP gain. The broad shallow cheek wall, low turn/long jaw, source upper-lid and wing identity, and facial deformation remain unfinished. No new makeup, garment or final animation work is credited.

Evidence: `../face-feedback-7/r19-sweep/` has55 actual matte/wire images (front hemisphere yaw−90…+90 at three elevations, not a full360° orbit). `../face-feedback-7/r19-comparison/` has verified paired boards. `../integrated-face-review-wip-5/` has four fresh source|WIP4|WIP5 face comparisons with unchanged uniform SRT. `../live-wip-5/` contains actual MCP head/body-centred ORTHO navigation captures. Native files and model origins were not changed by review.

Rebuild integration with `integrate_reference_finish.py --config frozen-inputs.json` in Blender. Its output points to a new replay directory. Selected producer native/manifest/deltas/recipe are archived under `../parts/face-finish7-r19/`; the source recipe records the earlier producer trial dependencies and is not by itself a standalone clean-room reconstruction of every discarded trial. Use the frozen selected native as the integration input.

Continue from `../face-feedback-7/ACCEPTANCE.md` and `../PROGRESS.md`. Preserve this checkpoint. New edits must show meaningful improvement over this and source art; a new version number, lower fit residual, preserved keys or a successful MCP call is not acceptance.
