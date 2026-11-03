"""Read-only projected ownership of actual frozen Main; not a Blender render.

The diagnostic includes the whole co-located skin/backing families. It does not
invent a source-aligned camera, alter geometry, or measure final appearance.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / '.mia-cache/face-live/fringe-ownership'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT / 'ownership.json').exists(), 'Keep the first diagnosis immutable'
a = np.load(ROOT / '.mia-cache/face-live/source-audit/analysis.npz')
components = np.load(ROOT / '.mia-cache/face-live/source-audit/components.npz')
cfg = json.loads((ROOT / 'asset/mia/blender/mia-fit-v003/brow-fringe/candidate-B.json').read_text())
v, faces, face_root = a['main_world'], a['main_triangles'], components['face_root']
families = cfg['logical_clumps']
root_family = {int(r): i for i, f in enumerate(families) for r in f['complete_component_roots']}
owned = np.isin(face_root, list(root_family))
ids = np.unique(faces[owned])
colors = np.array([(111, 184, 225), (244, 187, 88), (214, 127, 189),
                   (124, 204, 162), (239, 135, 120)], np.uint8)

# Same historical neutral front camera roll, but an explicitly disclosed crop
# for ownership inspection. This is not registration to the source portrait.
right = np.array([.9933727979660034, 0., -.11493712663650513])
up = np.array([.11493712663650513, 0., .9933727979660034])
origin = np.array([0., 0., 1.58])
u, z = (v-origin) @ right, (v-origin) @ up
W, H, mpp = 720, 400, .00025
xy = np.column_stack([u/mpp+W/2, H/2-z/mpp])
depth = np.full((H, W), np.inf)
labels = np.full((H, W), -1, np.int16)
rgb = np.full((H, W, 3), (224, 230, 234), np.uint8)
tri = xy[faces]
candidate = np.flatnonzero((tri[:,:,0].max(1)>=0) & (tri[:,:,0].min(1)<W) &
                          (tri[:,:,1].max(1)>=0) & (tri[:,:,1].min(1)<H))
for fi in candidate:
    p = tri[fi]
    lo = np.maximum(np.floor(p.min(0)).astype(int), 0)
    hi = np.minimum(np.ceil(p.max(0)).astype(int), [W-1, H-1])
    if np.any(hi < lo):
        continue
    xx, yy = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5,
                         np.arange(lo[1], hi[1]+1)+.5)
    e1, e2 = p[1]-p[0], p[2]-p[0]
    det = e1[0]*e2[1]-e1[1]*e2[0]
    if abs(det) < 1e-9:
        continue
    dx, dy = xx-p[0,0], yy-p[0,1]
    b = (dx*e2[1]-dy*e2[0])/det
    c = (e1[0]*dy-e1[1]*dx)/det
    hit = (b>=0) & (c>=0) & (b+c<=1)
    y0,y1 = lo[1],hi[1]+1
    x0,x1 = lo[0],hi[0]+1
    world_y = v[faces[fi],1]
    dd = world_y[0]+b*(world_y[1]-world_y[0])+c*(world_y[2]-world_y[0])
    replace = hit & (dd < depth[y0:y1,x0:x1])
    depth[y0:y1,x0:x1][replace] = dd[replace]
    label = root_family.get(int(face_root[fi]), -1)
    labels[y0:y1,x0:x1][replace] = label
    rgb[y0:y1,x0:x1][replace] = colors[label] if label>=0 else (85,88,91)

# Exact Y rays at the true neutral brow centerline, retaining every distinct
# overlapping island rather than just the first hit or semantic Fringe label.
t3 = v[faces]
p0 = t3[:,0][:,[0,2]]
e1, e2 = t3[:,1][:,[0,2]]-p0, t3[:,2][:,[0,2]]-p0
det = e1[:,0]*e2[:,1]-e1[:,1]*e2[:,0]
records = []
projection = Image.fromarray(rgb)
draw = ImageDraw.Draw(projection)
for side in (-1, 1):
    brow = a[f'V31_SourceBrow_{side}_world'].reshape(65,3,3)[:,1]
    observed = cfg['brow_width_case'][str(side)]['observed_u']
    for col, point in enumerate(brow):
        if not observed[0] <= col/64 <= observed[1]:
            continue
        d = point[[0,2]]-p0
        b = np.divide(d[:,0]*e2[:,1]-d[:,1]*e2[:,0], det,
                      out=np.zeros(len(faces)), where=abs(det)>1e-12)
        c = np.divide(e1[:,0]*d[:,1]-e1[:,1]*d[:,0], det,
                      out=np.zeros(len(faces)), where=abs(det)>1e-12)
        yy = t3[:,0,1]+b*(t3[:,1,1]-t3[:,0,1])+c*(t3[:,2,1]-t3[:,0,1])
        hit = np.flatnonzero((abs(det)>1e-12)&(b>=0)&(c>=0)&(b+c<=1)&(yy<point[1]-.00005))
        ordered = hit[np.argsort(yy[hit])]
        roots = list(dict.fromkeys(int(face_root[f]) for f in ordered))
        assert all(r in root_family for r in roots), 'An unowned backing blocker was found'
        records.append(dict(side=side,column=col,island_roots=roots))
        p = point-origin
        x,y = p@right/mpp+W/2, H/2-p@up/mpp
        draw.ellipse((x-2,y-2,x+2,y+2), fill=(245,248,252) if not roots else (220,25,35))

source = ROOT / 'asset/mia/references/received/mia-face-reaffirmed-20261031.png'
crop = Image.open(source).convert('RGB').crop((340,220,700,370))
board = Image.new('RGB', (W*2, H+145), (238,242,245))
src_display = ImageOps.contain(crop,(W,H))
board.paste(src_display,((W-src_display.width)//2,(H-src_display.height)//2+40))
board.paste(projection,(W,40))
bd = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
bd.text((12,8),'Source original-aspect crop (display only)',font=font,fill=(25,34,40))
bd.text((W+12,8),'Frozen actual Main: family ownership projection',font=font,fill=(25,34,40))
bd.text((12,H+48),'Not a Blender render or source-aligned proportion comparison.',font=font,fill=(25,34,40))
bd.text((12,H+73),'White = brow center clear of Main; red = blocked by 1+ laminated islands.',font=font,fill=(25,34,40))
for i,f in enumerate(families):
    x = 12+i*285
    bd.rectangle((x,H+108,x+15,H+123),fill=tuple(colors[i]))
    bd.text((x+21,H+105),f['family'].replace('screen_','').replace('_forelock',''),font=font,fill=(25,34,40))
board.save(OUT/'source-ownership.png')
report = dict(read_only=True,diagnostic='Projected frozen actual Main, not a Blender render',
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),source_crop=[340,220,700,370],
    source_aspect_unchanged=True,projection_meters_per_pixel=mpp,
    family_count=len(families),island_count=len(root_family),vertices=len(ids),faces=int(owned.sum()),
    source_window_samples=len(records),Main_clear_samples=sum(not x['island_roots'] for x in records),
    overlapping_island_count_histogram=dict(Counter(len(x['island_roots']) for x in records)),
    all_observed_Main_blockers_owned=True,records=records,
    geometry_modified=False,expression_test=False,native_saved=False,ART=False)
(OUT/'ownership.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='records'}))
