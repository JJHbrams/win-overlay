# Whole-height gate before source-fit C

Four fresh current R3b full-scene source frames are in `current-source4/`. `current-v06-{front,profile,back,oblique}.png` compares them with the exact newly received user-selected v06. `current-v06-boards.json` records the registration: one global scale1.0022371365 and vertical shift4.89038px applied to every current view. Source front crown54/sole950 determines this display scale; there is no shoulder, waist, neck or width normalization. Reference hair/sole variation across the four views is about5px. The front torso coordinate grid is a common2× zoom of this registered board.

The current native and its actual body/31 visible-mesh bounds, bone endpoints, complete neutral pose basis and47 key values are captured in `current-proportions.json`. The render script captures the pose before rendering and asserts it unchanged before all four frames. The companion CPU audit reopens the same exact native/frame1; it does not infer pose from a template. Actual3 source lights60/15/8 and all archived-light flags are recorded before every render. No native was saved.

## Observed differences

These are bounded visible-run measurements, not precision anatomy reconstructed from a drawing. Pixel coordinates refer to original source height1024. Current values are in the registered source coordinate system. World dimensions use the unchanged current sole-to-hair-crown span1.653969m over896 display pixels, approximately1.846mm/pixel.

| Landmark / span | User target v06 | Current | Implication / limit |
|---|---|---|---|
| Hair crown → chin, front | about131±4px | about121.5±3px; raw Face690 chin1.46988m | Current head-height proxy is about7–10% smaller relative to whole height. Hair flyaways and source chin angle limit precision. No head change selected. |
| Head-height count | about6.84 | about7.37 | This gives a direction for the ratio difference, not permission to sculpt or scale the head. |
| Corresponding exposed upper-deltoid skin span, front | about154±8px at source y225 (x159..313) | about134±5px at registered y215 (x682..816 in right board) | About15%±8% wider in source. Source/current crest heights differ; matching only one scan height would conflate width and height. Hair limits both endpoints. |
| Second deltoid contour run |169px at source y235 (x156..325)|148px at registered y225 (x675..823)|Independent~14% width difference. Both are SKIN counterpart runs, not a skin-to-rig comparison. |
| Internal rig shoulder-joint span, context only | Not directly visible in source |117.75px =.21736m | Do NOT use this internal span against source outer skin to infer expansion. Prior25–35% inference was mixed and is withdrawn. |
| Cup transverse panel, front | visible/estimated total about130–140px | about100±3px | The current bust is substantially too narrow; source mass must widen and fill the upper/lateral region. Hair limits the exact outer source edge. |
| Cup vertical extent | about50–60px from scoop neighborhood to lower band | about35–40px | Current material and supported volume look short/low. Garment top/bottom landmarks are not naked anatomical roots. |
| Profile pole beyond thorax | roughly40–47px, about74–87mm | about42px /77mm | Current depth is already substantial. Do not meet the size request by an indiscriminate forward extrusion. |
| Pole height, profile | approximatelyy292–300 | approximatelyy304 | A bounded upward redistribution around10–20mm is supported; not a blanket shrink. Exact source curve is cloth-covered. |
| Sternoclavicular drawn cue, front | approximatelyy219–223 | Current Neck bone.head projects near202, but is a DIFFERENT landmark | Prior precise neck-lowering inference from this mixed pair is WITHDRAWN. Material seam and rig pivot are not visible source anatomical equivalents. Neck/trap shape is handled through the integrated scaffold and actual skin continuity. |
| Shoulder support height | approximatelyy232–240 | joint approximatelyy225 | Wider shoulders also need a modest lower, shallower trapezius route, not just larger deltoid spheres. |
| Underband / waist / pelvis | source lower band and waist modestly lower; hip/thigh already comparable or fuller currently | see original-aspect boards | Do not globally enlarge hips or warp legs to conceal a torso mismatch. Local pose uncertainty remains explicit. |

## C construction direction

1. Enlarge and round the actual ribcage transversely, with a bounded profile-depth correction rather than the old fixed-G3 assumption. Keep waist/hip continuity, accepted Face690 and head shape exact. This is a torso cage correction, not another isolated lower-fold fairing.
2. Redistribute the supported soft mass upward and outward over that ribcage. Preserve substantial pole projection, broaden upper/lateral fullness, and rebuild the inferior attachment as a smooth broad return. Do not preserve the known G pointed fold merely to keep its metrics. No volume scalar/cone mapping.
3. Widen shoulder support and use a shallower, slightly lower trapezius/neck transition. The visible skin measurements suggest roughly15–20mm per-side outer-support expansion as a provisional range, not30mm joint relocation. Any fitted shoulder-joint relocation is mechanically material: a mesh-only deltoid widening must not pretend the old rig pivot remains correct. Declare a paired rig/rest strategy for root review before selecting the shoulder result; original pose values remain protected.
4. Keep the head untouched in C. If root chooses a ratio correction, it must be a separately reviewed consistent transformation of the entire head and every attachment, preserving facial sculpt proportions and all original arrays. No local face sculpt or unreported anisotropic stretch.
5. Fit the actual source charcoal scoop bra, lower band, straps and briefs to the selected3D form, then author coherent UV/fabric/shadow response. Current world-height masks are not a valid fitted pattern. The current harsh cup/cloth shadows and missing sewn-band structure are material failures in addition to the geometric size/attachment defects.

Root has reviewed all four boards and authorized C torso/breast production. Shoulder production remains gated on skin counterpart measurement plus a declared paired rest/surface strategy. No C geometry or garment edit has been made at this gate. A/B remain unselected; all original47 and nonbody data remain exact. Actual source4 comparisons precede C production, as requested.
