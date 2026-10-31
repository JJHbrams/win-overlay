# Stage 0 qualitative part decisions

Status: **design reuse decisions; production topology and animation acceptance remain incomplete**.

Inputs are recorded in `../mia-production-stage0/source-inventory.json`. Common head cameras and recorded proxy normalizations support qualitative review; head bounds are not calibrated anatomical landmarks. The illustrated concept views also vary in pose and camera. Full frames separately normalize visible height and sole position. Source shaders remain different, with neutral clay used alongside actual color.

| Region | Decision | Observed basis and next action |
|---|---|---|
| Face likeness | REUSE_DESIGN / RETOPO_PENDING | Pixal single-head retains the narrow eye impression, jaw outline and tired character better than the generic-looking native face studies. Keep its high-resolution surface/color as the design sculpt; independent eyelid/eye/mouth deformation structure is unverified. |
| Multiview head | REFERENCE / REPAIR_REQUIRED | Useful side/rear tied-hair mass, but clay shows irregular neck and facial surface detail. Do not adopt it as a cleaner replacement merely because it is multiview. |
| Hair waves and braid | REUSE_DESIGN / PARTITION_REVIEW | Preserve single-head wave detail. The earlier native hair remains an editable flow reference, but its broad strips and profile layering need repair. Front/rear/half-up/braid partition boundaries require color-ID review. |
| Head interior | ADD_VOLUME_PROXY | A high-detail exterior does not establish a complete hidden forehead/skull. Include an independent three-dimensional inner volume and inspect it alone; this is not final face retopology. |
| Body anatomy | PRESERVE / FIT_PENDING | Native source has separate face/body roles and existing facial keys, but its long-leg/small-pelvis impression differs from the clothed concept. Preserve it as anatomy/rig research and a hidden fitting proxy; no automatic facial-key transfer. |
| Outfit silhouette | REUSE_DESIGN / RETOPO_PENDING | Pixal full-body preserves the crop/cardigan/cargo/shoe arrangement. Puffy sleeve folds, seams and hidden layers require later modeling/deformation work. Preserve detail while introducing inspectable static design partitions. |
| Bag and strap | REUSE_PLACEMENT / CONTACT_PENDING | Preserve the rear-hip bag placement and diagonal strap as design information. Rigid hardware, flexible strap and garment contact require separate production handling. |

The Stage 1 assembly may retain existing high-resolution geometry as a **static design partition**, rather than replacing successful detail with generic primitives. Partition coverage is a data-preservation check, not proof of correct anatomical labels or animation-ready edges. Every source face must remain assigned exactly once, including hidden replaced/reference parts; ambiguous labels stay review-required.

Stage 2 must resolve clean deformation topology, eye/lid/mouth structures, independent hair/garment boundaries and hidden-surface policies. Stage 1 is not approved by face counts, labels, collection names or source reuse alone.

## Executed Stage 1 result

The source upper-body partitions produced jagged junctions, so the review checkpoint uses new editable crop, inner band, cardigan body/sleeves, strap, rear bag, waist and neck/abdomen volumes. Generated lower trousers/shoes remain design surfaces. The prior native three-lane braid is reused and fitted separately. High-resolution head/waves remain a static reference surface with mixed boundaries, not a finished facial rig mesh.

The saved review package passed exact coordinate/UV and imported-face coverage checks after reopening in Blender. Technical blockout acceptance does not approve likeness: eyes, hands, wardrobe fit and production topology still require work.
