# A3 initial proxy invalid

The initial proxy sampled control-cage vertices by nearest X/Z and gave the new object an identity world transform. The reviewed skin object has a 180-degree Z world rotation, so that preview would not occupy the same world space. It is retained only to make the coordinate error reproducible. It is not a face candidate or a valid target surface.

The replacement must sample the neutral evaluated **front** sheet by a local +Y ray and copy the skin object's world transform.
