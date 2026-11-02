"""Frozen uniform source registration for actual front4 comparison boards."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;CAN=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');O=P/'actual-B-front4'
records=json.loads((O/'records.json').read_text());assert len(records)==4
pkg=json.loads((CAN/'blender/mia-refinement-v002/review/integrated-R3b/paired-source/reference-review.json').read_text());front=next(r for r in pkg['views'] if r.get('name',r.get('id'))=='front')
source=Image.open(front['reference']['path']).convert('RGB');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(front['reference']['path'])==front['reference']['sha256']
def registered(im,reg,render512=False):
    s=reg['uniform_scale']*(768/512 if render512 else 1);tx,ty=reg['translation_xy']
    return im.transform((590,600),Image.Transform.AFFINE,(1/s,0,-tx/s,0,1/s,-ty/s),Image.Resampling.BICUBIC,fillcolor='#25313c')
src=registered(source,front['reference_registration']);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);summaries=[]
for hair in ['hairOFF','hairON']:
    base=next(r for r in records if r['id']=='baseline-front-'+hair);cand=next(r for r in records if r['id']=='candidate-front-'+hair)
    assert base['camera']==cand['camera'] and base['active_face_keys']==cand['active_face_keys']
    a=Image.open(base['path']).convert('RGB');b=Image.open(cand['path']).convert('RGB');assert a.size==b.size==(512,512)
    tiles=[src,registered(a,front['baseline_registration'],True),registered(b,front['candidate_registration'],True)]
    board=Image.new('RGB',(1770,674),'#17232d');d=ImageDraw.Draw(board)
    for col,(label,tile) in enumerate(zip(['SOURCE portrait / visible fragments','BASELINE selected / '+hair,'CANDIDATE B / '+hair],tiles)):
        board.paste(tile,(590*col,38));d.text((590*col+8,8),label,font=font,fill='white')
    d.text((10,641),'Frozen uniform source/IPD display registration; original aspect. No extra roll, feature warp, brow lift or projected ink overlay.',font=small,fill='white')
    d.text((10,657),'Hidden full brow ends remain inferred. HairOFF isolates actual brow width; HairON tests actual clump gaps. Not whole-face/hair ART acceptance.',font=small,fill='white')
    path=O/('source-baseline-B-front-'+hair+'.png');board.save(path)
    # Existing pixels, uniform crop only, for normal-delivery-size line/gap review.
    crop=board.crop((0,38+145,1770,38+335));crop.save(O/('brow-detail-'+hair+'.png'))
    summaries.append({'condition':hair,'board':str(path),'sha256':sha(path),'baseline':base,'candidate':cand,
        'reference':front['reference'],'source_registration':front['reference_registration'],
        'model_registration':dict(front['baseline_registration'],render_size_conversion='512→768 uniform1.5 before frozen scalar'),
        'ART':'PENDING actual visual inspection; no candidate full native saved'})
(O/'source-paired-front.json').write_text(json.dumps(summaries,indent=2)+'\n',encoding='utf-8',newline='\n');print('Actual front4 source paired boards written')
