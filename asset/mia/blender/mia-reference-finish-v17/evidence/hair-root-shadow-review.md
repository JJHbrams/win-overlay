# v17g diagnosed root-shadow correction

Frozen native SHA256: `a384d7552bf5e9fda69e79b20742892cee7eb6e3610113dc8122141fb58775ff`. Source v17f preserved unchanged. Build exit0.

Actual rays establish a near-side hair opening: at worldY.060/Z1.628, visible root-lining X+.0401 precedes first hair hit at far-side X-.0776. Adjacent rays hit near-side hair X+.0625 to+.0871. This is not a root-lining protrusion. No geometry was moved or deleted and full skin remains intact.

Only MIA_V17_RootLining_MIA_V06_BODY_SKIN material assignment changed to MIA_V17G_RootLining_WarmHairShadow, matching the hair palette and its normal-response multiplier. This removes the unrelated dark-gray color contrast. It does not restore strands, eliminate the underlying opening, or prove clipping repaired. The rectangular opening remains somewhat discernible.

Fresh reopen assertions:156 mesh coordinate/key/UV hashes identical;155 other mesh material assignments identical;58 packed image byte hashes identical. Face/body/head/UV/keys and knot unchanged. Same-camera before_profile.png and after_profile.png at scale.64/targetZ1.46. All packed images retained with fake users. No additional geometry or broad hair trial.

Root may apply this single material assignment on its integrated candidate. No native writes pending.
