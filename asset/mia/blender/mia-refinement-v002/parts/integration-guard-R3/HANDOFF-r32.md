# r3.2: deterministic ID-property UI limits

Frozen current helper: `scene_fingerprint.py`, schema `mia.scene-fingerprint.r3.2`, SHA `694d0b0f5e0b649d20e8c036fdca16a2396a23b08a05d3ad6630d9943b20541c`.

The exact previous helper is preserved as `scene_fingerprint_r31.py`, SHA `e282d98bd8db32cdc9a56d444fce41e4cadd4aed10ae53337972f8dfc70c5e29`. Previous r3.1 mutation report/manifest remain historical records for those bytes; they are not the current runtime manifest.

r3.2 adds separate `custom_property_ui` records alongside the unchanged custom-property values. Supported properties use `block.id_properties_ui(key).as_dict()` and deterministic JSON serialization. Only unsupported `TypeError`/`KeyError` cases are skipped; serialization errors propagate. Authored hard/soft bounds, defaults, subtype, descriptions and supported property metadata are observed, without editor selection/layout state. The companion records cover object/data/key owners and the material/node/group/modifier/world/scene property locations already fingerprinted. Legacy core geometry/key/UV/weight fields and driver exception policy are unchanged.

The bounded actual CPU test `test_id_property_ui_r32.py` temporarily changed only `Mia_FacialControls_v002.PresetTotal` UI hard maximum1→16 on exact R2. Its value and driver stayed unchanged in neutral. r3.1 did not observe the edit; r3.2 detected precisely the `custom_property_ui` field. The only UI metadata difference was `max`. All618 owners' full snapshot restored exactly, repeated snapshots matched, and a fresh reopen of the unchanged R2 matched the same full r3.2 baseline. Actual success marker: `R32_ID_PROPERTY_UI_GUARD_DONE`; elapsed45.29s. See `CPU-id-property-ui-r32-report.json`.

No17-case rerun, native save, GPU use or canonical/live/Git edit occurred. The normalization fix itself remains root's new delta. Root copies current `scene_fingerprint.py` for R3b, preserves r3.1 separately for history, and runs the existing same-version/helper-SHA fresh comparison on the newly saved R3b metadata. The new `custom_property_ui` owner field must remain visible in stage change records.
