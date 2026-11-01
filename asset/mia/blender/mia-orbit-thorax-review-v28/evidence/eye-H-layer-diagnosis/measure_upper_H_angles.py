"""Visible-border slopes in original camera axes. No chord flattening."""
import json,numpy as np
from pathlib import Path
O=Path(__file__).parent;s=json.loads((O/'upper-H-visible-opening-traces.json').read_text());g=json.loads((O/'upper-H-G2-projections.json').read_text());rows=[]
central={'front':{'image_left':[1,3],'image_right':[1,3]},'left_oblique':{'image_left':[1,2],'image_right':[1,3]},'right_oblique':{'image_left':[1,3],'image_right':[1,3]},'profile':{'near':[1,3]}}
for view,eyes in s['views'].items():
 for eye,t in eyes.items():
  side='-1' if eye=='image_left' else '1';a=np.array(t['upper_visible']);a=a[::-1] if side=='-1' else a
  # Orientation reads medial->lateral while preserving image vertical axis.
  ang=lambda q:float(np.degrees(np.arctan2(-(q[-1,1]-q[0,1]),abs(q[-1,0]-q[0,0]))))
  w=np.array(g['world_skin'][side]['upper']);u=(abs(w[:,0])-abs(w[0,0]))/(abs(w[-1,0])-abs(w[0,0]));q=np.array(g['views'][view]['skin'][side]['upper']);r=np.array([[np.interp(t,u,q[:,j]) for j in range(2)] for t in [.3,.8]])
  unc=s['uncertainty_original_px'][view];span=float(abs(a[-1,0]-a[0,0]));lo=ang(np.array([a[0]+[0,-unc],a[-1]+[0,unc]]));hi=ang(np.array([a[0]+[0,unc],a[-1]+[0,-unc]]))
  aa=np.array(t['upper_visible'])[central[view][eye]];aa=aa[::-1] if side=='-1' else aa
  clo=ang(np.array([aa[0]+[0,-unc],aa[-1]+[0,unc]]));chi=ang(np.array([aa[0]+[0,unc],aa[-1]+[0,-unc]]))
  rows.append({'view':view,'eye':eye,'source_full_observed_upper_segment_slope_outward_deg':ang(a),'source_full_endpoint_pixel_uncertainty_slope_interval_deg':[lo,hi],'source_central_visible_run_slope_outward_deg':ang(aa),'source_central_endpoint_pixel_uncertainty_slope_interval_deg':[clo,chi],'source_central_selected_indices':central[view][eye],'G2_skin_upper_30to80percent_slope_outward_deg':ang(r),'source_visible_horizontal_span_px':span,'not_correspondence_fit':'Source visible trace is partially covered and not the same anatomical stations as G2 30..80%; full segment also includes medial turn, so it is NOT a central-run comparison. Both estimates retained to expose interval sensitivity; neither establishes a vertex target. Camera roll/gaze uncertainty remains.'})
(O/'upper-H-raw-upper-angle-diagnostic.json').write_text(json.dumps({'rows':rows,'policy':'Source and native camera raw pixel axes; no chord rotation, no fitted eye rotation. Full-face pose is not solved by these slopes.','conclusion':'Black-tail-based canthus inference withdrawn. Inherited endpoint preservation is an unreviewed invariant, not yet evidence that anatomical endpoints must move. Current visible white-border differences require review with source uncertainty, camera roll and gaze.'},indent=2));print(json.dumps(rows,indent=2))
