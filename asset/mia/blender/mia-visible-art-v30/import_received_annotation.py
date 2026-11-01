"""Preserve the user markup and extract colored observation pixels, never repaint art."""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
mia = P.parents[1]
refs = mia/'references'
source = Path('C:/Users/antio/AppData/Local/Temp/codex-clipboard-6df34461-e421-4d2e-8170-9583d554504d.png')
dest = refs/'received/mia-eye-lash-user-markup-20261102.png'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if not dest.exists():
    shutil.copyfile(source, dest)
assert sha(source) == sha(dest)
im = Image.open(dest)
row = {'id': 'MIA-EYE-LASH-USER-ANNOTATION-20261102', 'status': 'user_annotation',
    'role': 'visible_eye_opening_versus_lash_source_correction', 'path': dest.relative_to(refs).as_posix(),
    'sha256': sha(dest), 'size': list(im.size), 'mode': im.mode,
    'semantics': 'User red=source actual eye opening; green=source lashes; orange/yellow=old model opening/lash appearance. Makeup also rejected as unlike source.',
    'limits': 'Manual display annotation, not a texture, exact orthographic blueprint or approval of current model. Original unmarked portrait remains the design source.'}
catalog_path = refs/'reference-catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
if not any(x['id'] == row['id'] for x in catalog['assets']):
    catalog['assets'].append(row)
catalog['updated_date'] = '2026-11-02'
catalog['reference_selection']['latest_eye_lash_semantic_annotation'] = row['id']
catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
files_path = refs/'files.json'
files = json.loads(files_path.read_text(encoding='utf-8-sig'))
if not any(x['path'] == row['path'] for x in files['images']):
    files['images'].append({k: row[k] for k in ['path', 'sha256', 'size', 'mode']})
files_path.write_text(json.dumps(files, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(dest.with_suffix('.provenance.json')).write_text(json.dumps(dict(row, original_path=str(source),
    bytes_preserved=True, usage='Evidence/source boundary semantics only. Never paint colored annotation strokes into final maps.'), ensure_ascii=False, indent=2), encoding='utf-8')
rgb = np.asarray(im.convert('RGB')).astype(int)
r,g,b = rgb.transpose(2,0,1)
xx = np.indices(r.shape)[1]
sx = im.width/2560
masks = {'source_opening_red': (r>220)&(g<75)&(b<90)&(xx<640*sx),
         'source_lashes_green': (g>120)&(r<100)&(b<140)&(xx<640*sx),
         'model_opening_orange': (r>220)&(g>70)&(g<205)&(b<90)&(xx>=640*sx)&(xx<1280*sx),
         'model_lashes_yellow': (r>220)&(g>210)&(b<90)&(xx>=640*sx)&(xx<1280*sx)}
observations = {}
for name, mask in masks.items():
    seen = set()
    components = []
    for y,x in zip(*np.nonzero(mask)):
        if (y,x) in seen:
            continue
        queue = [(int(y),int(x))]
        seen.add((y,x))
        points = []
        while queue:
            py,px = queue.pop()
            points.append([px,py])
            for dy in [-1,0,1]:
                for dx in [-1,0,1]:
                    ny,nx=py+dy,px+dx
                    if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and (ny,nx) not in seen:
                        seen.add((ny,nx));queue.append((ny,nx))
        if len(points)>8:
            arr=np.array(points)
            components.append({'pixels':len(points),'bbox_xyxy':[int(arr[:,0].min()),int(arr[:,1].min()),int(arr[:,0].max()+1),int(arr[:,1].max()+1)],'points_xy':points})
    observations[name]=components
result={'image':row, 'coordinates':'Original received PNG pixel coordinates, no resize or warp.',
    'meaning':'Thresholded manual markup observations; line thickness/overlap uncertainty remains. Do not equate stroke extrema with exact skin vertices.',
    'observations':observations}
(P/'user-markup-pixels.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'path':str(dest),'sha256':row['sha256'],'size':row['size'],
    'components':{k:[(c['pixels'],c['bbox_xyxy']) for c in v] for k,v in observations.items()}}))
