"""Diagnostic layout only: actual source and renders, inherited uniform SRT."""
import json,hashlib,math,argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--output-dir',default=str(ROOT/'actual-review'))
OUT=Path(ap.parse_args().output_dir).resolve()
records=json.loads((OUT/'render-records.json').read_text())
manifest=json.loads((OUT/'manifest.json').read_text())
package_path=Path(manifest['face_package']['path'])
package=json.loads(package_path.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(package_path)==manifest['face_package']['sha256']
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
size=(640,640)
def transform(im,reg):
    scale=reg['uniform_scale'];angle=math.radians(reg['rotation_degrees'])
    A=scale*np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    inv=np.linalg.inv(A);t=-inv@np.array(reg['translation_xy'])
    im=im.convert('RGBA').transform(size,Image.Transform.AFFINE,tuple(inv[0])+tuple(t[:1])+tuple(inv[1])+tuple(t[1:]),resample=Image.Resampling.BICUBIC)
    bg=Image.new('RGBA',size,'#edf1f4');bg.alpha_composite(im)
    return bg.convert('RGB')
boards=[]
for row in package['views']:
    view=row['id']
    if view not in ['front','left_oblique']:continue
    ref=(package_path.parent/row['reference']['path']).resolve()
    assert sha(ref)==row['reference']['sha256']
    assert row['baseline_registration']==row['candidate_registration']
    for mode in ['lit','color_only']:
        panes=[transform(Image.open(ref),row['reference_registration'])]
        for role in ['baseline','candidate']:
            record=records[role+'/'+mode+'-'+view]
            assert sha(record['render'])==record['sha256']
            panes.append(transform(Image.open(record['render']),row['baseline_registration']))
        board=Image.new('RGB',(1920,760),'#edf1f4');draw=ImageDraw.Draw(board)
        for i,(pane,label) in enumerate(zip(panes,['SOURCE ART','WIP9 M4 / FRESH BASELINE','M5 / SAME GEOMETRY'])):
            board.paste(pane,(i*640,50));draw.text((i*640+10,13),label,font=font,fill='#172633')
        draw.text((10,700),view+' / '+mode+' | inherited uniform SRT; camera/light/display fixed; eye-to-chin normalization does not prove proportions.',font=small,fill='#172633')
        draw.text((10,724),'COLOR-ONLY: skin light bypassed, hair hidden; eyes/accessories keep native shader. No native/source texture changed. Not an ART PASS.',font=small,fill='#172633')
        out=OUT/(mode+'-'+view+'-source-m4-m5.png');board.save(out)
        boards.append({'view':view,'mode':mode,'path':str(out),'sha256':sha(out),'reference':str(ref),'reference_registration':row['reference_registration'],'baseline_and_candidate_registration':row['baseline_registration'],'pose_uncertainty':row['pose_uncertainty']})
(OUT/'comparison-boards.json').write_text(json.dumps(boards,indent=2))
print(json.dumps([b['path'] for b in boards],indent=2))
