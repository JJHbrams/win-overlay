# Mia inactive worktrees — 2026-10-31

The user requested cleanup before continuing corrections. Seven inactive modeling worktrees were moved into `C:/Users/antio/.codex/worktree-archives/mia-20261031-v20`, then only their stale Git registrations were pruned. All 9,210 files (5,794,750,204 bytes), including ignored Blender backups, were verified by path/size/SHA-256 before and after movement. No branch was deleted and no forced dirty worktree removal was used.

| Former worktree | Archive subdirectory / preserved branch |
|---|---|
| `mia-face-lookdev-v07` | `mia-face-lookdev-v07/tree` / `codex/mia-face-lookdev-v07` |
| `mia-final-garments-v12` | `mia-final-garments-v12/tree` / `codex/mia-final-garments-v12` |
| `mia-final-hair-v12` | `mia-final-hair-v12/tree` / `codex/mia-final-hair-v12` |
| `mia-head-refine-v06` | `mia-head-refine-v06/tree` / `codex/mia-head-refine-v06` |
| `mia-layered-workflow` | `mia-layered-workflow/tree` / `codex/mia-layered-model-v02` |
| `mia-reference-face-art` | `mia-reference-face-art/tree` / `codex/mia-reference-face-art` |
| `mia-reference-hair-surface` | `mia-reference-hair-surface/tree` / `codex/mia-reference-hair-surface` |

The first move of `mia-layered-workflow` encountered a temporary file lock. The resumed attempt succeeded; its full file hashes were verified before registration cleanup. No process was terminated.

`result.json`, `plan.json`, per-worktree `files-before.json` / `files-after.json` and `git-admin-snapshot` live in the archive. The old `.git` file was preserved as `.git.archived-pointer` after verification, so these snapshots cannot be mistaken for active worktrees. Recover through a new worktree of the preserved branch plus the archived files; never blindly restore the obsolete pointer.

Active modeling workspaces: canonical `mia-body-head-v06`, producer `mia-final-face-v12`, producer `mia-head-hair-fit-v16`; current chat cwd `mia-reference-recovery` remains as a handoff entry. The user's Desktop checkout, animation calibration, launch branding and window-climbing worktrees were retained.

Machine-readable scoped evidence: [worktree-archive.json](blender/mia-correction-v20/worktree-archive.json). Historical absolute paths into archived worktrees now require the mapping above. Canonical packed v18 and diagnostic v19 natives remain in the canonical worktree and are unchanged.
