# Non-mutating hair organization plan

Actual mesh:122129 faces,340 geometry-connected components when coincident UV-seam vertices are identified for inspection only. The largest component contains108401 faces. Loose-part separation therefore cannot produce front/rear/base owners.

Existing primary vertex labels contain3821 mixed-label faces:1841 rear/side,974 crown/side,582 fringe/side,271 crown/fringe,4 crown/fringe/side,149 old braid/side. These are spatial classifications, not strand boundaries. Rear/side crossings extend from the crown transition to the lowest locks; blindly splitting there would cut curls lengthwise. Fringe/side crossings pass through cheek wisps; crown/fringe crossings intersect visible root sweeps. Old Left_Braid labels on317 whole faces are residual original-side hair, not the separate authored braid.

Proposed face ownership (no split executed):
1. Base: retain the two existing root-lining objects as scalp base. Keep crown gathering in a separate crown owner, not merged into anatomical scalp.
2. Fringe: select complete visible central and cheek-sweep lock surfaces by source polygon IDs, following valley/root overlap boundaries behind the visible fringe. Do not use a planar Y or Z cut.
3. Side/nape and rear: assign complete curls from their roots to tips. Move the boundary behind temple/ear overlap and along existing inter-lock gaps; the mixed-face band must be inspected as whole locks, not rounded to majority vertex labels.
4. Keep existing braid lanes/tail/tie and knot core/wraps independent.

At an intentional ownership boundary duplicate coincident boundary vertices and retain exact positions, custom normals, both UVMap/MIA_V17_PAINT_UV loop coordinates, material indices and MIA_SOURCE_POLYGON IDs. Duplicate vertices alone do not create a visible rest seam; independent future deformation can, so overlapping root coverage and shared root deformation must be designed later. No remesh, global unwrap, source-pixel repaint, or rig-readiness claim is implied.

Feasible as face-based segmentation with carefully chosen complete-lock ownership. Not feasible as an automatic connected-component or current-vertex-group split without cutting details. partition-inspection.json records actual counts and mixed-region bounds. No native modification was made by this inspection.
