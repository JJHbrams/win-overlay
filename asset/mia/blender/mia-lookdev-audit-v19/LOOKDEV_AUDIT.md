# v19 read-only camera / lighting / material audit

Source: Mia_HeadHair_v18.blend, SHA256 `87334607c76f6c0e876807f10ff407e8ce60fc7055265ae3591257893ba7b88d`. Inspection and diagnostic rendering exited0. Source hash is unchanged; neither script contains a native save operation. Scene overrides existed only in the background Blender process.

## Measured current conditions

EEVEE,1000x1000 at100%,square pixels. Camera ORTHO,scale0.48,location(0,-2,1.555),rotation approximately(90deg,0,0),shift0,clip0.1..1000. The stored50mm lens does not control an orthographic projection. Standard view,Medium High Contrast look,exposure0,gamma1,no curves.

World active node: Background RGB(.12,.15,.18),strength.8. World.color(.035,.045,.065) is not the connected node value. Three white AREA lights: HeadKey380W,size2,position(2.2,-2.9,2.7); HeadFill150W,size2,position(-2,-2.2,2); HeadRim220W,size1.3,position(0,2.4,2.4). Full matrices/rotations and recursively traversed active node paths are in scene-material-audit.json.

## Actual used material paths

| Visible owner | Active color data / UV | Connected shading |
|---|---|---|
| MIA_V14_SculptedSkin,slot7 only (1342 base faces) | MIA_V17_FixedUV_FacePigment,2048²,Non-Color,packed; explicit UVMap | pigment multiplied by normal-driven warm skin ramp,then Emission |
| MIA_V06_BODY_SKIN,slot0 (4060 base faces) | MIA_V13_BodySkin_UV_2048,2048²,Non-Color,packed; image Vector unlinked,active render UVMap | same skin ramp multiplied by image,then Emission |
| MIA_V17_PIXAL_DetailedHair | MIA_V17_Pixal_Repacked4096.001,4096²,sRGB,packed; explicit MIA_V17_PAINT_UV; old UVMap retained inactive | image color to luminance to warm-gray ramp; normal multiplier; Emission |
| Braid / knot | local longitudinal / cylindrical UV,procedural Wave to color ramp | normal multiplier to Emission |
| Sclera / iris / lashes | sclera constant; iris UV-based procedural masks/color/highlight; lashes constant | Emission,with Transparent mix for iris aperture; hidden legacy cards Transparent |
| Hair root linings / tie | constants or fixed warm shadow | Emission; one root lining has normal multiplier |

Important distinction: legacy MToon-compatible Principled nodes,metallic1,roughness1 and neutral8x8 normal textures exist in unused material slots. Current visible skin has no polygons assigned to those slots; eye surface uses sclera,procedural iris and transparent legacy slots. Their mere presence does not establish an active diffuse/specular/normal-map pipeline.

Skin synthetic direction is(-.2996,-.6492,+.6991); hair direction is(+.3,-.65,+.7). Thus skin and hair shade from different X sides independently of the scene lamps. Skin maps dot range[-.4,.9] into a warm ramp; hair maps[-1,1] to multiplier[.62,1]. Neither is a measured response to the three Area lamps. No active roughness/specular/normal texture is connected to the used face/body/main-hair surfaces.

Image paths include old external/relative locations. All active images above are packed. A stale filepath is not evidence of missing pixels in the current native. Do not change colorspace merely because a PNG is named BaseColor: current face/body are authored as numeric pigment multipliers; their intended linear-data contract must be retained or deliberately converted with image values and shader together. Hair sRGB decoding is part of its current tone calibration.

## What the diagnostic evidence supports

Seven files use the same head framing and a fixed front or45deg camera. target_front/target_three_quarter preserve production materials and color management. lamps_off_front sets only Area-light energy to0 and leaves world/camera/materials unchanged. Mean absolute RGB difference from target_front is0.001508 on an8-bit scale;99th percentile0,max6 at isolated pixels. This is near-invariance,not byte identity; the active graph independently explains why lamp changes cannot meaningfully tune the main emission surfaces. The small pixel differences are not attributed to a specific cause by this audit.

unlit_color_signal_front bypasses normal shading only on main face/body/hair. Skin uses a fixed warm base tint(.78,.65,.58); hair retains its luminance-to-tone conversion. It is NOT certified physical albedo. Dark/light hair strand markings and face under-eye/nose/mouth paint remain visible. Fact: these marks are in the color signal. Inference: some inherited Pixal light/dark strata represent illustrated/baked illumination as well as pigment; the atlas cannot automatically be treated as illumination-free PBR albedo or split into specular/roughness maps.

uv_checker_front uses an unlit procedural checker with explicit current paint UV for hair and active UVMap for skin. It tests visible mapping/density; it does not prove all UVs are distortion-free. No unwrap or texture change was made.

diffuse_clay_three_quarter replaces only skin/cap with neutral18% Diffuse BSDF,removes hair from render and hides separate liner meshes. Full skin/cap remain; eye cards keep their existing alpha/materials. Under neutral lamps the forehead/cap transition and uneven face planes are more apparent. This is a visual observation requiring geometry/normal continuity review,not a new mesh diagnosis proved solely by a screenshot.

specular_probe_three_quarter uses temporary black-base Principled,metallic0,roughness.30,IOR1.45 under the same neutral rig. It reveals normal/surface continuity through reflected highlights. It is NOT a proposed final skin material,a delivered specular map,or evidence that the production shader currently supports highlights.

## Minimal fixed review rig and sequence

Freeze one camera set before editing maps: front(0,-2,1.555),45deg(1.414214,-1.414214,1.555),both aim(0,0,1.555),ORTHO.48,1000²,shift0,pixel aspect1. Keep these identical for geometry,color,UV and shader comparisons. Root may first align this set to the confirmed reference,then lock it; do not fit each material pass independently. The drawing is not a calibrated orthographic photograph.

For neutral geometry/reflection diagnostics use Standard/None,exposure0,gamma1. Disable original lights. White Area key60W,disk size1 at(-.6,-1,2.2),fill15W,disk size1.5 at(.8,-.8,1.8),both aimed at the head target; no rim. Neutral world Background(.18,.18,.18),strength.10. This exact temporary rig produced the clay/probe images; values are a reproducible diagnostic setup,not a universal physically measured studio. Do not compensate for surface defects by changing exposure per view.

1. Geometry first: neutral diffuse clay,front and45deg; check silhouette,face/cap normal continuity,eye aperture and surface ripples. Use a specular probe only where reflection continuity adds information.
2. UV/color next: explicit UV checker and unlit color signal under Standard/None,with all geometry and cameras fixed. Separate authored pigment from synthetic normal shading. Preserve source maps and the current colorspace contract; do not infer roughness from painted darkness.
3. Target toon last: restore Standard/Medium High Contrast and the actual production graph. If retaining emission toon,make its synthetic light directions an explicit shared design choice; Area lamps cannot serve as its tonal calibration control. Do not compare its RGB directly to a differently color-managed diagnostic pass.
4. Only if a genuinely light-responsive finish is desired,prototype that shader separately under the fixed rig. Start with constants for roughness/specular. Add a spatial roughness or normal map only for a demonstrated need; eyes can use a separate material response. Existing procedural iris glints are artwork,not view-dependent reflection.

Minimum useful assets now are skin pigment,illustrated hair color,UVs and alpha/region masks. A complete diffuse/specular/roughness/normal map set is not automatically required by the current stylized emission pipeline. No such maps were generated by this audit.
