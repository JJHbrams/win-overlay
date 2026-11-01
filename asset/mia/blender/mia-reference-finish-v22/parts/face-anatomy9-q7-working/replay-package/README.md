# Q7 portable replay

Run with Blender 5.2.3 (tested build e13b728c6880), using only the immutable WIP8 native and this folder:

```powershell
& 'C:/Program Files/Blender Foundation/Blender 5.2/blender.exe' -b -t 4 --python replay_face_q7.py -- --source 'PATH/TO/Mia_ReferenceFinish_v22.blend' --output-dir 'PATH/TO/FRESH_OUTPUT'
```

The source must have SHA-256 ff2b61b2b2146fc4f73119cf10534571609dff75f6333fbec34d0926068b8bb4. A nonempty output directory is rejected. Dependencies are resolved relative to the script and their hashes are checked.

The script applies the frozen original P2 lower-face field, bakes Subsurf alone in rest space for all 47 keys with UV/weight interpolation, restores Armature, retargets four lash driver IDs, and applies Q7 exact dense deltas. Every skin shape-key value is explicitly zero. No P2 or bake-control native is read or written. The rejected Q6b loft is never saved: only its reversible float32 arithmetic is reproduced to match the accepted-for-review Q7 coordinate arrays exactly.

Output: one Mia_ConnectedSurface_Q7_Replayed.blend plus replay-audit.json. After save/reopen, the audit checks exact float32 hashes of all 47 key coordinate arrays, UV arrays, topology, weights, group names, 165 other meshes, driver target routes, and evaluated neutral surface against expected-q7.json. Native byte hashes are recorded but are not the equality criterion. The original source is rehashed unchanged.

Verified real execution: ../replay-test-verified/replay-audit.json. fingerprint_equal=true, mismatched_fields=[], all_skin_keys_zero=true. Initial ../replay-test failed only because in-memory driver tuples were compared to decoded JSON lists; all actual array hashes already matched. The final script canonicalizes the comparison through JSON before comparing.

This reproduces a partial midface improvement. Whole-face art, eyelid identity, profile wedge, inner nose/mouth grooves and final rig acceptance remain unresolved. Reproduction success does not establish art acceptance.
