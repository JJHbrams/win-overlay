# Mia correction v20

User request: archive other worktrees safely, then perform actual body/face corrections and hair mesh work. Continue the existing reference-first production protocol, not a new character redesign.

Input: integrated v18, SHA256 `87334607c76f6c0e876807f10ff407e8ce60fc7055265ae3591257893ba7b88d`; repository checkpoint `725de89`. The source remains immutable and is not art-approved.

| ID | Criterion / user-visible outcome | Intended runtime | Verification / evidence | Critical |
|---|---|---|---|---|
| AC1 | Inactive Mia worktrees leave the active list while all files, ignored native backups, branch heads and recovery metadata remain available | Windows filesystem / Git | Exact allowlist; source/destination tree SHA manifests; archive mapping; post-cleanup worktree and branch checks; no forced dirty removal | true |
| AC2 | Actual body edits improve breast–chest/axilla, pelvis–thigh and neck–shoulder continuity while preserving the reference body identity | Blender saved native and fresh render | Same-pose, same-camera/light front/profile/back/3Q before/after and reference comparison; source/other-owner preservation; residual defects explicitly assessed | true |
| AC3 | Actual face/head/eye corrections improve cheek flow, eye design and cross-view reference likeness | Blender saved native and fresh render | Front plus profile/both oblique views and relevant subtle-angle expression panels; distinguish camera/pose uncertainty from visible geometry defects; no raw chin-direction guess | true |
| AC4 | Pixal hair detail is retained while source holes, rear ends and mechanical knot are corrected; any partition follows meaningful complete locks | Blender saved native and fresh render | Multiview before/after, actual source polygon ownership and both UVs/normals; no blind spatial or loose-part split; new geometry receives explicit provenance | true |
| AC5 | A single integrated editable native opens and reproduces the corrected result, with honest per-part judgments and remote checkpoint | Blender / live MCP / Git | Fresh saved-native review, actual protected-owner and file checks, independent acceptance, remote commit SHA | true |

Scope: no garment production or final event/secondary-motion rig. Tiny deformation checks may diagnose face construction. A successful save/hash/UV check never replaces visual acceptance.

Ownership: root integrates and archives inactive worktrees. Body producer edits visible body below world Z=1.46 m; face producer owns face/eyes/lids and any necessary head cap edits at or above Z=1.46 m. Body vertex IDs/deltas must remain traceable for combining disjoint changes. Hair production follows body correction in the existing hair producer worktree. Producers do not edit canonical source or each other's files.

The canonical root, current Codex cwd, Desktop checkout and unrelated feature worktrees remain. The two active producer worktrees remain until their work is integrated. Archived branches are retained. Archive movement is a preservation action, not destruction of rejected studies.
