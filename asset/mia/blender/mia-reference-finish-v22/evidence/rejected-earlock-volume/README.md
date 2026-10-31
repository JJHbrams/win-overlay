# REJECTED ear-terminal experiment — do not integrate

Keep baseline hair0d. This package records a failed local repair, not an accepted hair update. No further geometry work is pending.

Rejected native: Mia_EarLockVolume_v22.blend
SHA256: d195ce72e03f8ec71dca25b223d57d196d73c24c917e1927571a17d1b3dfca53
Baseline source SHA256: 0d787482198137c37a5fd80067f7f6ce74678c1a99df783b0ece7cb59c5fb319

Visual failure: the closed terminal removes the longitudinal slit but reads as a smooth bean/appendage with a pinched root. The retained inner lobe still exposes its flat cut. Front/profile/oblique failure boards show both problems under identical clay. A complete-lock design must include both lobes and the connector; another isolated capsule is not the next step.

Technical scope: exactly430 declared original faces removed from one owner MIA_V17_PIXAL_DetailedHair;702 new vertices and728 faces added as an independent closed island. All retained old vertices/faceUV/source IDs/weights remain exact; other owners and64 packed images match baseline. New patch has Euler2, every edge two oppositely wound faces, positive signed volume and no degenerate3D triangles or zero total weights. These facts do not establish art acceptance.

Additional failure: nearest-surface UV transfer creates564 zero-area UV triangles; effective density varies from0 to27902px/cm (median8.8). Actual checker images confirm this is not production-usable UV. No UV PASS. Global indexed edge counts include existing UV-split boundaries; do not interpret73021 indexed open edges as73021 new cracks.772 loose edges remain after FACES_ONLY deletion. The full hair is not watertight; root overlap was never a welded join.

old-new-mapping.npz: new_vertex_to_old/new_face_to_old; -1 means newly authored. MIA_V22_OLD_VERTEX_ID/MIA_V22_OLD_FACE_ID persist in the rejected native; MIA_V22_TERMINAL_REGION1 marks patch faces; new MIA_SOURCE_POLYGON=-1. proposed-selection.json holds deleted430 original/source face IDs. A new terminal-only material copies original pigment/light route but uses actual geometric normals; original material slots stay intact. No maps were repainted.

Runtime: first build saved/rendered but manifest failed on stale Blender material reference (exit1); corrected identical-shape rebuild exited0. Read-only provenance/checker audit exited0. Source0d and3a8 remain immutable; no root/live/Git changes. The rejected blend1 backup is local prior-build evidence, not a second selected candidate.

Minimal portable failure evidence is enumerated in failure-package.json using relative paths. The large rejected native is optional archival evidence; replay requires unchanged baseline0d at the relative path documented in build_candidate.py and proposed-selection.json. No installation or GUI tools required.
