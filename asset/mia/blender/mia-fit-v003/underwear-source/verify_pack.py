"""Verify actual source bytes, source-pixel samples and undistorted board panels."""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
def read(name):
    return json.loads((HERE/name).read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

manifest=read('source-paths.json'); samples=read('appearance-samples.json'); proof=read('verification.json')
source_path=Path(manifest['source']['path']); source=Image.open(source_path).convert('RGB')
assert sha(source_path)==manifest['source']['sha256']==samples['source_sha256']==proof['source_sha256_before']
assert source.size==tuple(manifest['source']['size_px'])==(1536,1024)
assert sha(HERE/'source-paths.json')==proof['source_paths_sha256']
assert sha(HERE/'appearance-samples.json')==proof['appearance_samples_sha256']
assert sha(HERE/'source-overlay-original-aspect.png')==proof['overlay_sha256']
assert Image.open(HERE/'source-overlay-original-aspect.png').size==source.size
assert len({p['id'] for p in manifest['paths']})==len(manifest['paths'])
for p in manifest['paths']:
    assert p['confidence']['level'] in ('high','medium','low') and p['observed_limits']
    x0,y0,x1,y1=p['crop_xyxy']
    assert all(isinstance(x,int) and isinstance(y,int) and x0<=x<x1 and y0<=y<y1 for x,y in p['points_px'])
arr=np.asarray(source)
for sample in samples['samples']:
    x0,y0,x1,y1=sample['patch_xyxy'];patch=arr[y0:y1,x0:x1]
    assert patch.shape[0]*patch.shape[1]==sample['pixel_count']
    assert np.array_equal(np.median(patch.reshape(-1,3),axis=0),sample['srgb_encoded_median_u8'])
checks=[]
for record in proof['boards']:
    board=Image.open(HERE/record['path']).convert('RGB')
    assert sha(HERE/record['path'])==record['sha256']
    crop=source.crop(record['source_crop_xyxy']); scale=record['uniform_scale']
    assert scale==2 and crop.size==tuple(record['source_crop_size_px'])
    expected=crop.resize((crop.width*scale,crop.height*scale),Image.Resampling.NEAREST)
    actual=board.crop((0,48,expected.width,48+expected.height))
    assert np.array_equal(np.asarray(expected),np.asarray(actual)),record['path']
    checks.append({'board':record['path'],'actual_original_panel_matches_uniform_source_crop':True})
assert all(not region['points_px'] for region in manifest['unobserved'])
review=read('visual-review.json')
assert len(review['images_actually_viewed'])==4
proof['visual_overlay_review']='Actual four boards inspected; see visual-review.json'
proof['actual_source_panel_checks']=checks
proof['appearance_patch_medians_recomputed_exact']=True
proof['visual_review_sha256']=sha(HERE/'visual-review.json')
proof['status']='PASS'
(HERE/'verification.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':'PASS','source_hash_exact':True,'actual_source_panels_exact':len(checks),'recomputed_patch_medians':len(samples['samples']),'original_pixel_paths':len(manifest['paths'])}))
