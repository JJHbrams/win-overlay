# Narrow R3 coordinator changes

Copy `scene_fingerprint.py` beside the two canonical scripts. These are patch instructions only; this producer did not edit the coordinators, preview fixtures, live scene or native.

In both scripts, after `P` exists:

```python
sys.path.insert(0, str(P))
import scene_fingerprint as sfp
```

In `integrate_components.py`, replace only the local `digest`, `fingerprint`, `snapshot` definitions with the shared helper. Keep the existing key-coordinate, object-owner and removed-owner guards. For each stage:

```python
before_state = sfp.snapshot_scene()
before = before_state['objects']
# existing module replay
after_state = sfp.snapshot_scene()
after = after_state['objects']
assert before_state['scene'] == after_state['scene'], ('Scene envelope changed', stage['id'])
# existing changed/removed/allowed_existing_owners checks
driver_changes = sfp.assert_existing_driver_preservation(before, after, stage)
sfp.assert_scene_pose_owners_protected(before, after, stage)
# existing original facial key coordinate checks, including the body-G exception
```

The two shared assertions replace the old blanket CAMERA/LIGHT/ARMATURE row-equality loop. Cameras/lights remain fully protected. The rig stays identical in pose, transforms, data/custom properties and all other fields; only the exact declared object driver can differ. Existing driver removal is always rejected. An existing mesh/key driver expression also requires an exact declaration; additions remain visible in the owner fingerprint and governed by existing owner rules.

Add `actual_driver_changes=driver_changes` to each stage report. Do not use the replay's self-reported result as observation.

After the existing root preview/fps setup and save/pack, capture and write:

```python
final_state = sfp.snapshot_scene()
# add to existing integration report:
fingerprint_version=sfp.FINGERPRINT_VERSION,
fingerprint_helper_sha256=sha(Path(sfp.__file__)),
final_owners=final_state['objects'],
final_scene=final_state['scene'],
```

If the old unused `first=snapshot()` is retained, change it to `first=sfp.snapshot_scene()`. No preview-constructor changes are proposed here; root already fixed reuse and fps30.

In `verify_integrated_scene.py`, require the same version and helper bytes, then replace its local digest/manual partial fingerprint loop with:

```python
assert meta['fingerprint_version'] == sfp.FINGERPRINT_VERSION
assert meta['fingerprint_helper_sha256'] == sha(Path(sfp.__file__))
actual = sfp.snapshot_scene()
errors=[]
expected=meta['final_owners']
if set(expected) != set(actual['objects']):
    errors.append('Saved scene object inventory differs')
for name in sorted(set(expected) & set(actual['objects'])):
    old, now = expected[name], actual['objects'][name]
    for field in sorted(set(old) | set(now)):
        if old.get(field) != now.get(field):
            errors.append(name + ': saved ' + field + ' differs')
if meta['final_scene'] != actual['scene']:
    errors.append('Saved scene envelope differs')
checked=sorted(set(expected) & set(actual['objects']))
```

Keep existing zero-neutral-control, invalid-driver and packed-image checks as additional checks, plus native SHA immutability. Fresh comparison now covers the full exact same helper schema instead of the previous reduced subset.

Stage declarations for the two calibrations:

```json
{
  "smile": {
    "allowed_existing_owners": ["MIA_V27_Foundation_Face", "Mia_FacialControls_v002"],
    "allowed_driver_changes": [{
      "owner": "MIA_V27_Foundation_Face", "scope": "shape_keys",
      "data_path": "key_blocks[\"Face.M_F00_000_00_Fcl_MTH_Fun\"].value", "array_index": 0
    }]
  },
  "head_roll": {
    "allowed_existing_owners": ["MIA_V06_RIG", "Mia_FacialControls_v002"],
    "allowed_driver_changes": [{
      "owner": "MIA_V06_RIG", "scope": "object",
      "data_path": "pose.bones[\"J_Bip_C_Head\"].rotation_euler", "array_index": 2
    }]
  }
}
```

Owner permission does not excuse original driver changes; the explicit path/index permission is also required. Existing coordinate hashes remain independently protected. The new helper records authored data and excludes node UI locations/selections, runtime driver `is_valid` and RNA pointer addresses. Enum/ID/socket values serialize explicitly; unsupported value types fail rather than disappear into `str()`.
