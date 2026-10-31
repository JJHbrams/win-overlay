# Read-only active hair texture findings

Actual used main hair material samples packed sRGB MIA_V17_Pixal_Repacked4096.001 through explicit MIA_V17_PAINT_UV, Linear filtering. Original UVMap remains available. The4096 map was an EMIT rebake of original2048 raw atlas RGB, using oldUV as source and newly packedUV as target. It is not new high-resolution strand paint.

Actual area-weighted median densities across crown/front/rear/side: original2048 approximately11.6texels/cm;4096rebake approximately19.4texels/cm. Formula: sqrt(UVarea*resolution²/surfaceArea_m²)/100; area-weighted median. The current1000pixel ortho.52m camera displays19.23pixels/cm, so original information is about0.60texel/displaypixel. Atortho.29m it is about0.34. These support the observed soft/low-detail appearance in close views. Increasing the container to8K alone cannot recover absent source detail.

Limits: area-based density does not measure directional UV stretch, seams or actual frequency/sharpness. Coarse geometry and baked marks also contribute to apparent breakup. This is not a wholeUV PASS or proof all defects are caused by resolution. No texture, shader, UV or image pixels were changed by this inspection. Further high-resolution repaint/UV decisions belong to root's separate lookdev scope.

Central rear surface sampling:12rays atX±.025/0,Z1.54/1.56/1.58/1.60 all hit original main hair atY.121.. .136. This supports a lack of visible tied volume around the buried decorative loop, rather than proving a broad central scalp mesh hole. Sparse rays are not a watertightness proof. Exact records and source hashes are in texture-and-rear-inspection.json.
