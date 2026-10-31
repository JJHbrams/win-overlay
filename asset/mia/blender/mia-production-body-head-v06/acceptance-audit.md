# Independent acceptance audit — checkpoint 97b05f

Native SHA-256: `97b05f5bef8e2291669c49119e1cf8bcabe638e93c117c4e8b9d55f15ed4b75f`.

The planner did not implement this model. AC3–5 were reviewed from actual `final-matrix/` and `final-poses/` images. Technical AC1/2/6 use the separate servant's fresh Blender 5.2.3 runtime and `independent-final-audit-r2` evidence; the planner did not rerun Blender or directly inspect JSON in its restricted role.

```text
[ACCEPTANCE_AUDIT]
AC1: PASS — separate anatomy ownership, non-rendering packed references, proxy/hair/garment excluded.
AC2: PASS — immutable source/archive, original 42 key-coordinate hashes, ordered topology and UV preserved; derived Face44 prefix valid.
AC3: PASS — slender abdomen/waist, restrained shoulders, pelvis/thigh emphasis and slim calf form remain coherent across views.
AC4: FAIL — head remains too large/round, forehead broad, nose/mouth shallow and jaw/neck overly simple; mature Mia direction is insufficient.
AC5: PASS — actual blink/mouth/gaze and arm/torso/knee stress controls deform visible geometry, no major tearing in tested poses, neutral return 0.
AC6: PASS — independent fresh reopen/render exited 0; source/candidate SHA unchanged, refs packed and no missing textures.
overall: FAIL
```

This is a usable body fit and rigged structural checkpoint. It is not an approved Mia face or a completed character. Root additionally flagged severe far-iris foreshortening in three-quarter views for measured follow-up; the planner did not classify the observed foreshortening as a proven mesh collapse.

The first technical audit's false `derived_structure_match` came from a comparison-code field-name error. Every shared structural field already matched. Replacing the dict comparison with explicit structural keys and rerunning the same native produced r2 PASS; the first result is retained.
