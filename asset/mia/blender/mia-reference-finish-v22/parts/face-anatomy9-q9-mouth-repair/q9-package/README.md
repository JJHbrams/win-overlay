# Q9 mouth anchor postprocess

Blender invocation: `blender -b -t 4 --python replay_mouth_anchor_q9.py -- --source Q7_NATIVE.blend --output-dir FRESH_OUTPUT`.

Input is exact Q7 geometry, including a successfully replayed Q7 file; path/native byte hash may differ. Source coordinate/key/UV/topology/weight/other-mesh/driver fingerprints are guarded. Dependencies are relative and hash-checked. The actual topological mouth boundary is rediscovered and checked against the evaluated WIP8 loop evidence before applying exact reviewed deltas.

Evidence: actual WIP8 lip loop mean local Z 1.4949055761098862 m; Q7 1.490905730985105 m. The inherited P2 pass moved the lip approximately -4 mm despite claiming to preserve it. Q9 restores +4 mm with a wide mouth/corner carrier, retaining P2 chin endpoint. Mouth-loop restoration is independent of the uncertain source visible-width estimate. A separate bounded 1.2 mm X-only cheek inset is included, with no Y reduction and zero actual eye-boundary displacement.

The original candidate is Mia_ConnectedSurface_Q9_MouthAnchor.blend in the parent folder. Exact same 47-key/UV/weights/driver/evaluated-surface fingerprints are verified on replay. One native plus audit is written, no intermediate natives. Verified run: ../q9-replay-verified/replay-audit.json.

Geometry evidence: ../review-q9 contains actual source | Q7 | Q9 four views using frozen uniform SRT. ../matte-q9 contains front/profile/bilateral oblique, low 0/+30/-30, half/full blink 0/+30/-30, and actual subtle Eye+MouthSorrow .15 at 0/+25. Producer inspected the actual images: the mouth anchor restores as intended, no obvious new mouth gap/tearing in the subtle sorrow image, but upper-muzzle/inner-nose wrinkles and profile wedge remain. This is not whole-face art or unrestricted deformation approval.

Q7 remains preserved. Apply E2 eye changes after this postprocess and review the combined actual geometry; this script intentionally rejects already changed eye geometry. Frozen mouth reference includes immutable WIP8 SHA and coordinates, and output audit records restored mean Z and loop-translation spread.
