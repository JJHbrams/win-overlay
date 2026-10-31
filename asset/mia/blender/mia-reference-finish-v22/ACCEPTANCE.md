# Mia reference finish v22 — active contract

User request: while the user sleeps, correct actual Blender viewing/pivot/camera/light behavior; refine face/head/body against the multiple canonical art views, especially eye–nose bridge–mouth profile and nose shading; author and apply source-style UV surface maps. Preserve staged commits and remote checkpoints. The source-view pipeline must survive compaction and be enforced, not just documented.

Baseline: Git083dd40, native `../mia-correction-v20/integrated-r2/Mia_Corrected_v20.blend`, SHA c02b8ad73b86b278f2768e61eff019be223a8828bd92df62ce0ab7cb60f56936. Baseline is immutable and ART FAIL.

| ID | User-visible outcome | Runtime | Required verification | Critical |
|---|---|---|---|---|
| AC1 | Orbit/zoom centres on head or full body appropriately, review cameras/lights are explicit; prior capture projection is accurately explained | Live Blender MCP and saved native | Before/after viewport state and actual captures, zoom/orbit check, saved-camera metadata audit; no geometry/origin changes disguised as navigation repair | true |
| AC2 | Reference-faithful face/head, eye–nose–mouth depth and nose plane with coherent multi-angle shape | Saved native and fresh renders | Source-art/baseline/candidate matched front/profile/both oblique boards, relevant expression angles, neutral geometry and small deformation checks; independent review | true |
| AC3 | Coherent reference body primary form, chest/breast attachment, pelvis and neck | Saved native and fresh renders | Body Foundation front/profile/back/oblique paired comparisons, smooth connected surfaces, original preserved, independent review | true |
| AC4 | Actual UV-bound art maps and controlled toon lighting preserve source line/color/shadow character | Blender EEVEE target look | Active map/UV/material paths, new-detail provenance, color-only and neutral/production light comparisons; no mere upscale claim | true |
| AC5 | Single integrated editable native with honest final review and remote checkpoint | Live Blender MCP/Git | Fresh reopening, protected ownership/source hashes, actual live scene, reference package validator, independent per-criterion art audit, remote SHA | true |
| AC6 | Source-view comparison is enforced through compaction and handoff | Repository workflow/validator | AGENTS/current state links; validator rejects missing views, missing art and stale artifacts; art approval remains separate | true |

Ownership: root owns live Blender/cameras/lights/integration/reference-package gate and status. Existing face worktree owns `mia-face-finish-v22` face/head and face maps. Existing body worktree owns `mia-body-finish-v22` body below head boundary. Producers do not overwrite canonical source, each other, or live GUI. Keep archived originals; a derived topology is allowed when documented and transferable. No final garments or event/secondary-motion rig before art gates.

Sequence: camera/evidence registration -> independent face/body work -> source-style surface refinement and integration -> fresh source-paired multiview/live review -> independent acceptance -> Git checkpoint. Missing criteria are not silently dropped. No new token or spending budget was requested. No external asset upload, purchase or installation is required.
