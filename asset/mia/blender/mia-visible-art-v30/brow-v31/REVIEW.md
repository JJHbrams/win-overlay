# Source eyebrow correction — scoped working review

The user's latest concern is that brows and lashes change Mia's impression. This work separates the actual brow layer from upper/lower lashes and FaceA eyelid-crease pigment. It is not a whole-face, hair, body or animation approval.

## Finding and implementation

The visible inherited brow was **master slot4**, `V27_OriginalAlpha_Ink_4`, using packed `F00_000_FaceBrow_00` (1024x256). Its alpha silhouette is a raised cosmetic arch. The old separately named brow actors were hidden. Changing the fold/crease texture would not correct that visible brow.

Primary portrait exposed runs (original1024pixels) are approximately left410..455 and right520..551. The primary and expression01 show broader, lower, relatively straight ink strokes. Most full ends are hidden by bangs, so the complete end-to-end design is inferred rather than measured. Source target arrays and framing are in `build_source_brows.py`; original image aspect is never changed.

Two new independent mesh surfaces (`V31_SourceBrow_-1/1`,195vertices/128quads each) conform to actual skin. They keep the exact42named key list, transfer the original brow's semantic expression motion, reseat each named target on actual skin, and follow `J_Bip_C_Head`. They have editable `BrowParamUV`. Original brow geometry/alpha is archived reversibly by replacing only master slot4 with a private transparent material. Original mouth, skin, eye opening, globe, lashes, facial paint, BodyL, hair, UVs, original graphs/maps and other keys remain exact.

A's.14mm surface offset had a tiny AngryHalf burial. B uses.22mm. Fresh evaluated51named/interpolated states,32946vertex/quad-centre samples measured+.0257..+.4586mm signed skin clearance, zero embedding. This is a sampled contact result, not proof of arbitrary expression combinations. A denser evaluated-triangle audit was added after small bright flecks were noticed in an actual pose; its result must be read before declaring deformation finished.

The denser **C** audit is now complete:51states/1,207,986actual evaluated samples, including45barycentric samples per rendered triangle, measured+.02310..+.45864mm with zero embedding. C is B geometry exact. Thus the coarse nearest-surface result was checked more rigorously; the few bright edge pixels still need a native edge-coverage ablation rather than being called either a mesh gap or harmless ink without evidence.

C is **B geometry exact**, with only2brow material slots changed. Native UV edge coverage uses SmoothStep across15percent of each cross-strip edge, keeping central charcoal ink unchanged. It makes the hard ribbon edge less abrupt. This is graphic ink, not scene-light specular or a newly painted high-resolution bitmap.

## Actual review and limits

- Source/before/C/hair-on paired boards exist for front/profile/both obliques in `../reviews/browsC-source4/paired`. Source-package validator reports evidence_valid=true, ART=NOT_EVALUATED.
- Front uses the corrected frozen opening-centre/IPD scale1.16981465568, zero additional display roll, common translation. IPD is excluded from independent proportion validation. Nonfront retains the explicitly provisional old source display, with eye/chin-normalized proportions and extra small2Droll excluded from acceptance. No candidate refit or image stretching.
- C actual source4 production/neutral images and13actual512pose images are preserved with native/camera/light/key records. These images, not the existence of keys, establish what was seen.
- Independent hair producer (did not implement brows) read primary/expression01, before/A/C and registered C boards. It supports retaining the lower/flat direction: closer to tired/aloof Mia than the old beauty arch. The exposed front height/slant is broadly close; no evidence supports a large further relocation. C edge coverage improves A's hard edge. Slightly thick/neat ribbon and cut-like inner ends remain; fully hair-hidden endpoints cannot be certified. Full-face ART is not approved.
- Root read actual front, profile, both oblique/individual examples and AngryHalf/Sorrow. The brows now wrap along skin rather than floating flat, but posture-specific tiny flecks require the dense check noted above. Do not hide them under hair or turn the earlier coarse metric into a blanket PASS.

EyeM/source-scale lashes and F iris are integrated before this brow-only delta. The separate outer-orbit wall gap is owned by the outer producer; rejected A/B/C gap trials must not be silently selected. Face eye-to-mouth/chin length, fatigue/nose paint specificity and hair finishing remain open independently.
