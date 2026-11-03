# 2026-11-03 workspace correction

Actual cleanup: **25 exact legacy C audit duplicates /16,307,864bytes** removed. Their25 canonical D counterparts were rechecked for size and SHA-256. The allowlist and result are `C-exact-duplicate-plan.json` and `C-exact-duplicate-result.json`.

**Bulk cleanup remains incomplete.** The two task-created D backup subtrees total9,287files/6,764,548,435bytes and still exist. Root and independent reviewer checked every current C original/D copy against the original manifests. Automatic review rejected removing these D directories before process start (`blocked by policy`, no detailed reason). No alternative-tool retry was made; the C originals and prior rejected C cleanup targets were also untouched. `D-duplicate-preflight.json` and `D-duplicate-cleanup-result.json` distinguish verified duplicates from actual deletion.

The inventory is a snapshot of logical file sizes, not NTFS allocation or proof of the cause of earlier disk exhaustion. Free space measured before this cleanup was C37.21GB/D49.04GB. Do not attribute the prior increase from near-zero C free space to this16.3MB cleanup.

Whole old C worktrees retain unique/untracked data; old body also has an unmerged tip. No dirty worktree was forcibly removed. C's shared `.git/objects` remains the alternate used by D's Git repository. Original art, R3b/11 source natives, accepted E and unique/uncommitted F failure witnesses were protected.

`storage_guard.py` is read-only unless a small report is explicitly requested. Before a large operation, it requires20GiB free on C/D plus anticipated D writing, and a2GiB total Review12 output budget including the reservation. It measures the two component folders in all three D worktrees, the canonical presentation/GIF folder and runtime-temp. Root grants one heavy writer at a time; a preflight estimate is not an atomic quota. Normal native800MiB reserve passes; an excessive reserve fails with exit2. Capacity does not imply model/art acceptance. Never silently skip a missing guard.

New large outputs stay on D. Use existing immutable inputs by path+hash, scoped deltas and a small set of actual witnesses rather than whole-scene or backup duplication. The original full-body two-material native/GIF/source4 deliverables remain open.
