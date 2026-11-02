"""Observed E2/F2 traces -> explicit support bands, with local uncertainty.

Originalv06 remains the global height/width authority. These are exterior bra
support tangents and short visible axillary skin runs, not naked internal roots.
"""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'source-binding';O.mkdir(exist_ok=True)
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia')
src=CAN/'references/received/mia-low-view-axilla-reaffirmed-20261103.png'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='31fa0da05c970e9b6d84a2569953b48636bd8d32df33d65901772f5664ad52b2'
g=json.loads((P/'scaffold-D/guide-data.json').read_text());mpp=g['height_registration']['metres_per_source_pixel']/(704/430)
traces={
 'E2_cup_left':[[390,317],[376,336],[361,359],[354,382],[358,401],[368,418]],
 'E2_cup_right':[[553,318],[570,338],[580,363],[585,387],[579,410],[568,429]],
 'E2_band_bottom':[[369,449],[391,437],[417,426],[444,421],[469,419],[497,421],[524,428],[550,439],[568,453]],
 'E2_axilla_left':[[359,327],[351,338],[347,351],[350,365]],
 'E2_axilla_right':[[586,329],[594,344],[597,359],[593,375]],
 'F2_cup_outer':[[1219,335],[1207,345],[1198,355],[1191,365],[1186,375],[1183,385],[1183,395],[1186,405],[1191,415],[1198,425]],
 'F2_axilla_near':[[1405,339],[1420,354],[1428,374],[1433,393]],
 'F2_band_bottom':[[1208,448],[1236,434],[1267,425],[1302,425],[1335,432],[1367,442],[1394,454]]}
def at_y(name,y):
    t=np.asarray(traces[name]);return float(np.interp(y,t[:,1],t[:,0]))
cameras=dict(E2=dict(yaw_degrees=0,pitch_degrees=-8,yaw_uncertainty_degrees=4,pitch_uncertainty_degrees=6,body_axis_pixel_x=470,source_crop=[0,0,887,887]),F2=dict(yaw_degrees=40,pitch_degrees=-8,yaw_uncertainty_degrees=8,pitch_uncertainty_degrees=6,body_axis_pixel_x=1336,source_crop=[887,0,1774,887]))
rows=[]
# Semantic CUP stations use originalv06 uppercup/upper-middle/maxcup/lowercup
# heights. The firstE2 cloth point is not the higher clavicle/shoulder station.
sy=np.array([s['source_y'] for s in g['stations']]);hx=np.array([s['outer_half_width'] for s in g['stations']]);py=np.array([s['front_outer_y'] for s in g['stations']])
for i,source_y,ey,fy in [(0,262,317,335),(1,275,350,355),(2,290,385,385),(3,310,415,415)]:
    halfwidth=float(np.interp(source_y,sy,hx));profile=float(np.interp(source_y,sy,py));zz=g['height_registration']['crown_z']-(source_y-54)*g['height_registration']['metres_per_source_pixel'];front=[at_y('E2_cup_left',ey),at_y('E2_cup_right',ey)];width=(front[1]-front[0])*mpp;oblique_x=at_y('F2_cup_outer',fy);support=(1336-oblique_x)*mpp;xx=min(.9*halfwidth,width/2);yaw=math.radians(cameras['F2']['yaw_degrees']);derived_y=-.018-(support-math.cos(yaw)*xx)/math.sin(yaw)
    # A cross-sectional broad arc, not an appended sphere: radius is inferred
    # from one lobe's observed front width. The continuous body/root/fan must
    # still satisfy actual views. Intersect this arc with profile uncertainty.
    peak_x=.60*halfwidth;radius=width/4;dx=xx-peak_x;sag=radius-math.sqrt(max(radius*radius-dx*dx,radius*radius*.10));lat_y=derived_y;pole_y=lat_y-sag
    if pole_y<profile-.020:pole_y=profile-.020;lat_y=pole_y+sag
    rows.append(dict(station=i,v06_source_y=source_y,world_z=zz,v06_outer_halfwidth=halfwidth,v06_front_profile_y=profile,source_E2_y=ey,source_F2_y=fy,source_front_x_interval=front,source_front_width_m=width,source_F2_outer_x=oblique_x,oblique_support_m=support,oblique_support_uncertainty_m=.014,inferred_lateral_x=xx,inferred_peak_x=peak_x,inferred_round_arc_radius=radius,inferred_round_arc_sag=sag,inferred_lateral_y_unclamped=derived_y,chosen_lateral_y=lat_y,chosen_broad_pole_y=pole_y,actual_projected_F2_x=1336-(math.cos(yaw)*xx+math.sin(yaw)*(-lat_y-.018))/mpp,geometry_limit='Clothed exterior support tangent constrains broad connected envelope. Arc/meridian placement is inference inside source/profile bands, not a recovered internal nakedroot or separate sphere; no tangent-point correspondence between views.'))
fold=[]
for ey,fy in [(338,354),(351,374),(365,393)]:
    xx=(at_y('E2_axilla_right',ey)-470)*mpp;sx=(at_y('F2_axilla_near',fy)-1336)*mpp;yaw=math.radians(40);yy=-.018+(sx-math.cos(yaw)*xx)/math.sin(yaw)
    fold.append(dict(source_E2_y=ey,source_F2_y=fy,inferred_x=xx,inferred_y=yy,uncertainty_m=.014,world_z=float(np.interp(ey,[327,365],[1.345,1.290])),limit='Short visible ink/skin fold, partly shadow and arm/cloth-occluded. Finite anterior branch band; posterior corridor is not inferred from it.'))
report=dict(source=str(src),source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),source_size=[1774,887],authority='User reaffirmed E2/F2 upperbody fullness/lateralroot/axilla on2026-11-03. Originalv06 remains global proportion/height authority; no hip enlargement from E/F.',traces_original_pixels=traces,cameras=cameras,display_metric=dict(metres_per_pixel=mpp,method='One source-wide uniform display metric from originalv06 crown-to-crotch span430px and E2 corresponding704px. NOT calibrated dimensions; crown-to-band ratio differs, retained as registration residual.',global_vertical_limit='v06 global Z stations retained. E2/F2 section correspondence is semantic cup-envelope fraction; no source image warp or per-feature mesh warp.'),section_support_bands=rows,anterior_fold_bands=fold,uncertainty='Observed cup contour±3–8px; skinfold±8px plus camera/pose uncertainty. Section heights use v06; E2/F2 are shape/support constraints. Hidden nakedroot/posterior depth are inferred.',status='SOURCE_BINDING_DATA; actual fitter MUST consume these bands. Data/projection is not anatomy or ART approval.')
(O/'constraints.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
im=Image.open(src).convert('RGB');d=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',15)
for name,pts in traces.items():
    color='#00cdd1' if 'axilla' not in name else '#e5a529';d.line([tuple(p) for p in pts],fill=color,width=3);d.text(tuple(pts[len(pts)//2]),name,font=font,fill=color)
im.save(O/'observed-source-traces.png')
print('LOWVIEW_SOURCE_CONSTRAINTS_DONE',json.dumps(dict(mpp=mpp,sections=rows,fold=fold)),flush=True)
