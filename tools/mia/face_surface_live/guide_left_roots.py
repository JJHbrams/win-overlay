"""Read-only root-to-tip LEFT foreground inventory, not an edit/mask generator."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
OUT=ROOT/'.mia-cache/face-live/full-left-guide'
assert not OUT.exists()
OUT.mkdir()
a=np.load(ROOT/'.mia-cache/face-live/source-audit/analysis.npz')
c=np.load(ROOT/'.mia-cache/face-live/source-audit/components.npz')
v,f,roots=a['main_world'],a['main_triangles'],c['face_root']
center=v[f].mean(1)
fringe=a['main_weight_Fringe']>.5
locked=a['main_weight_Roots_Locked']>.5
fringe_top=float(v[fringe,2].max());roots_bottom=float(v[locked,2].min())
failed=np.load(ROOT/'.mia-cache/face-live/fringe-terminal01-ready/geometry.npz')['hidden_faces']
# Inventory bounds only. They are deliberately NOT exported as a face mask or
# proposed cut line; whole components can continue outside these bounds.
region=(center[:,0]>-.100)&(center[:,0]<.010)&(center[:,1]<-.010)&(center[:,2]>1.53)&(center[:,2]<1.705)
records=[]
for root in np.unique(roots[region]):
    all_faces=np.flatnonzero(roots==root)
    ids=np.unique(f[all_faces]);q=v[ids]
    records.append(dict(component_root=int(root),all_faces=len(all_faces),
        descriptive_left_region_faces=int(region[all_faces].sum()),
        crosses_inventory_boundary=bool(not region[all_faces].all()),
        has_Fringe_points=bool(fringe[ids].any()),has_RootsLocked_points=bool(locked[ids].any()),
        failed_terminal_faces=int(np.isin(all_faces,failed).sum()),
        world_bounds=[q.min(0).tolist(),q.max(0).tolist()]))
records.sort(key=lambda x:x['descriptive_left_region_faces'],reverse=True)

# The actual frozen Main foreground, with only measured semantic bands colored.
# Distinct visible root/transition/terminal bands reveal why a terminal-only
# module cannot repair the upstream shelf. No new geometry is generated.
W,H,mpp=440,630,.00032
right=np.array([.9933727979660034,0.,-.11493712663650513])
up=np.array([.11493712663650513,0.,.9933727979660034])
origin=np.array([-.035,0.,1.62])
xy=np.column_stack(((v-origin)@right/mpp+W/2,H/2-(v-origin)@up/mpp))
tri=xy[f];depth=np.full((H,W),np.inf);rgb=np.full((H,W,3),(226,232,237),np.uint8)
colors=dict(roots=(75,179,187),transition=(211,111,171),fringe=(238,181,81),terminal=(96,149,220),outside=(113,117,122))
candidate=np.flatnonzero((tri[:,:,0].max(1)>=0)&(tri[:,:,0].min(1)<W)&(tri[:,:,1].max(1)>=0)&(tri[:,:,1].min(1)<H))
failed_set=set(failed.tolist())
for fi in candidate:
    p=tri[fi];lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),[W-1,H-1])
    if np.any(hi<lo):continue
    x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
    e1,e2=p[1]-p[0],p[2]-p[0];det=e1[0]*e2[1]-e1[1]*e2[0]
    if abs(det)<1e-10:continue
    dx,dy=x-p[0,0],y-p[0,1]
    b=(dx*e2[1]-dy*e2[0])/det;cc=(e1[0]*dy-e1[1]*dx)/det
    inside=(b>=0)&(cc>=0)&(b+cc<=1)
    yy=v[f[fi],1];dd=yy[0]+b*(yy[1]-yy[0])+cc*(yy[2]-yy[0])
    sy,sx=slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1)
    hit=inside&(dd<depth[sy,sx]);depth[sy,sx][hit]=dd[hit]
    label='outside'
    if region[fi]:
        if fi in failed_set:label='terminal'
        elif locked[f[fi]].any():label='roots'
        elif fringe[f[fi]].any():label='fringe'
        elif fringe_top<=center[fi,2]<=roots_bottom:label='transition'
    rgb[sy,sx][hit]=colors[label]

source=Image.open(ROOT/'asset/mia/references/received/mia-face-reaffirmed-20261031.png').convert('RGB')
draw=ImageDraw.Draw(source)
# Broad observed root-to-tip direction guides, not replacement mesh contours.
for path,color in [([(482,95),(447,138),(417,200),(402,258),(423,326)],colors['roots']),
                   ([(497,106),(469,149),(446,206),(443,262),(473,310)],colors['fringe']),
                   ([(505,122),(483,178),(473,231),(492,290),(536,342)],colors['transition'])]:
    draw.line(path,fill=color,width=3)
crop=source.crop((340,50,575,370));display=ImageOps.contain(crop,(W,H))
board=Image.new('RGB',(W*2,H+160),(238,242,245));bd=ImageDraw.Draw(board)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
board.paste(display,((W-display.width)//2,38+(H-display.height)//2))
board.paste(Image.fromarray(rgb),(W,38))
bd.text((10,8),'Source: broad observed root-to-tip flow',font=font,fill=(25,34,40))
bd.text((W+10,8),'Actual frozen Main: measured bands',font=font,fill=(25,34,40))
for i,(key,label) in enumerate([('roots','RootsLocked > .5'),('transition','Untagged transition band'),('fringe','Fringe > .5'),('terminal','Failed terminal01 scope')]):
    x=10+(i%2)*440;y=H+54+(i//2)*26
    bd.rectangle((x,y,x+15,y+15),fill=colors[key]);bd.text((x+23,y-1),label,font=font,fill=(25,34,40))
bd.text((10,H+112),'Read-only projection. No source aspect change, final edit mask, new mesh or ART claim.',font=font,fill=(25,34,40))
bd.text((10,H+136),'Source panel fitted uniformly for context; panels are not registered for proportion measurement.',font=font,fill=(25,34,40))
board.save(OUT/'source-root-to-tip.png')
inv=json.loads((ROOT/'.mia-cache/face-live/source-audit/inventory.json').read_text())
other=[{k:o.get(k) for k in ('name','world_bounds','raw_vertices','raw_faces','custom_properties')}
       for o in inv['objects'] if o.get('name')=='MIA_V20_Crown_PixalDonorLock']
report=dict(status='READ_ONLY guide. Not an authorized edit mask or new geometry proposal.',
    source_Main_raw_sha256='16d192576cd8ecc1905f4eba96b4686c038e8c94a56e6eec7dee552e6eee0b2c',
    Fringe_point_count=int(fringe.sum()),Fringe_top_z=fringe_top,
    RootsLocked_point_count=int(locked.sum()),RootsLocked_bottom_z=roots_bottom,
    semantic_threshold_transition_gap_mm=(roots_bottom-fringe_top)*1000,
    descriptive_left_region=dict(x=[-.100,.010],y_less_than=-.010,z=[1.53,1.705],
        faces=int(region.sum()),components=len(records),filter_is_not_edit_mask=True),
    component_records=records,other_native_actor_bounds=other,
    inherited_source_limit='Original native inventory does not contain the later live RootLining actors. Their actual coverage must be checked before any whole-left live edit. Main-only projection is not an all-actor occlusion proof.',
    next_scope='Resolve complete upstream left foreground mass and root integration before another terminal replacement. Do not cut at a horizontal Z boundary. Preserve right diagonal/crown silhouette and retained M2 actors.',
    new_geometry_created=False,live_MCP_used=False,GPU_used=False,ART=False)
(OUT/'ownership.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k not in ('component_records','other_native_actor_bounds')}))
