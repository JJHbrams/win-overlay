# B causal underbust diagnostic — geometry unchanged

2026-11-03. Root requested this audit before any new sculpt because the two gray bands could have come from context visibility or shading. **No C geometry, new parameters, or hidden sculpt changes were made.** Original B is frozen in commit `14600ec`; all pre-existing B file hashes were asserted unchanged after the two new actual frames. Source native also remains unchanged. These diagnostics do not grant B an anatomy/source ART pass.

The producer directly viewed `design-only-gray-front.png`, `design-only-normal-front.png` and `actual-meridian-contour-tangent.png`. The two underbust bands persist with only the B design actor rendered. Normal→Emission also shows corresponding normal-color bands. Context visibility and old normal maps therefore do not explain their existence; gray cast/light contrast can amplify their appearance. The actual meridian is continuous, so **two dark bands are not evidence of two disconnected physical lips or folds**.

## Actual evaluated context and first-hit ownership

`actual-context-first-hit-audit.json` measures actual evaluated geometry and materials, not raw polygon-mask hashes alone. Private context has80,771 evaluated vertices. Actual triangle material counts are39,104 at slot12,86,336 at slot1,3,536 at slot10 and32,208 at slot0. Slot12 is the actual direct Transparent BSDF→EEVEE Output route; the other listed slots resolve to the recorded physical gray. Actual gray and transparent material signatures are included.

The exact-front underbust sampling grid contains3,021 rays: X±140mm, Z1.14..1.27m. After skipping triangles whose actual output ancestry is fully Transparent BSDF,2,769 rays first hit the new B design and252 miss; **zero rays first hit context or another actor**. General alpha/transmission solving is not claimed. The two design-only renders independently remove context cast/visibility contributions.

## Actual geometry / normal relationship

The NPZ's true triangle intersections at X+66.114mm produce840 segments /840 nodes in one connected closed contour loop, every node degree2. The plot samples the anterior minimumY and actual segment tangent/projected geometric face normal at1mm Z intervals through a roughly3mm voxel mesh. It does not substitute the source profile table or assume smoothness from the field construction.

| Z | Actual meridian tangent from vertical | Nearest positive primitive |
|---|---:|---|
|1.170|−9.96°|Thorax/abdomen|
|1.180|−49.36°|Thorax near the union|
|1.185|−67.58°|Breast pair|
|1.195|−57.74°|Breast pair|
|1.200|−57.25°|Breast pair|
|1.205|−59.40°|Breast pair|
|1.220|−34.81°|Breast pair|
|1.240|−15.64°|Breast pair|

There is a strong lower thorax-to-bowl normal turn around Z1.18–1.19, partial relaxation and another smaller turn around1.205, followed by the bowl's front return. Maximum1mm-sample triangle-tangent step inZ1.16..1.24 is9.22°; some steps reflect tessellation, not a proven analytic discontinuity. The meridian is one continuous branch. This separates the lower union and bowl turning regions without claiming two separate physical fold surfaces.

Producer inference: independently interpolating CY and RY can produce an extra front-slope turn even though `CY(station)−RY(station)` matches each desired front station. That is a plausible contributor, **not an executed causal interpolation ablation**. B's rectangular frontal width/bowl shape remains a separate source issue. Do not reshape merely to erase a cast shadow, nor interpret the gray band's count as the number of geometric folds.

## Two actual render records

Only two new actual images were rendered under the granted GPU token, then the token was released. Same exact B front camera,0.1..10m clipping, ortho scale0.4m,640², pixel aspect1, frame1 and Standard/None display settings. Existing three gray lights remain unchanged. `design-only-gray` uses the recorded physical BSDF; `design-only-normal` uses actual Geometry Normal→multiply-add(0.5,0.5)→Emission with no old maps. Every other mesh is hidden. Actor flags, active actor name, actual material signature, actual lights and state SHA256 are recorded before both shots. Material signatures are asserted unchanged after rendering.

Blender exited0 in11.8s. The log has no error/compile/failed/traceback matches. No native save, live application, UV/key/weight migration, head scale or accepted facial-form edit was performed. Engram MCP remains unavailable; repository evidence only.
