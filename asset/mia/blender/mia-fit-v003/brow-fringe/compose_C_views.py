"""Source/baseline/C actual comparisons; frozen uniform SRT, no candidate refit."""
from pathlib import Path
import json,hashlib,math,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;CAN=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');O=P/'actual-C-views5';rows=json.loads((O/'records.json').read_text());assert len(rows)==5
old=json.loads((P/'actual-B-front4/records.json').read_text());pkg=json.loads((CAN/'blender/mia-refinement-v002/review/integrated-R3b/paired-source/reference-review.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
def registered(im,reg,render512=False):
    angle=math.radians(reg['rotation_degrees']);s=reg['uniform_scale']*(1.5 if render512 else 1);c=math.cos(angle);n=math.sin(angle)
    matrix=np.array([[s*c,-s*n,reg['translation_xy'][0]],[s*n,s*c,reg['translation_xy'][1]],[0,0,1.]])
    inv=np.linalg.inv(matrix);return im.transform((590,600),Image.Transform.AFFINE,tuple(inv[:2].ravel()),Image.Resampling.BICUBIC,fillcolor='#25313c')
reports=[]
for view in ['front','left_oblique','profile']:
    spec=next(r for r in pkg['views'] if r.get('name',r.get('id'))==view)
    baseline=next(r for r in (old if view=='front' else rows) if r['id']=='baseline-'+view+'-hairON')
    candidate=next(r for r in rows if r['id']=='candidate-'+view+'-hairON');assert baseline['camera']==candidate['camera']
    source=Image.open(spec['reference']['path']).convert('RGB');assert sha(spec['reference']['path'])==spec['reference']['sha256']
    a=Image.open(baseline['path']).convert('RGB');b=Image.open(candidate['path']).convert('RGB');assert a.size==b.size==(512,512)
    tiles=[registered(source,spec['reference_registration']),registered(a,spec['baseline_registration'],True),registered(b,spec['candidate_registration'],True)]
    board=Image.new('RGB',(1770,678),'#17232d');d=ImageDraw.Draw(board)
    for col,(label,tile) in enumerate(zip(['SOURCE / '+view,'COMPOSED BASELINE / '+view,'C DISTAL TAPER / '+view],tiles)):
        board.paste(tile,(590*col,38));d.text((590*col+8,8),label,font=font,fill='white')
    d.text((10,642),'Original source aspect; frozen same uniform SRT for before/after. No candidate refit, body/face/eye resize, brow lift or fake brow overlay.',font=small,fill='white')
    d.text((10,659),'Nonfront historical pose/display registration is provisional: normalized absolute facial proportions/roll are excluded. Hidden brow ends remain uncertain.',font=small,fill='white')
    path=O/('source-baseline-C-'+view+'.png');board.save(path)
    if view=='front':board.crop((0,183,1770,373)).save(O/'brow-detail-front.png')
    reports.append({'view':view,'board':str(path),'sha256':sha(path),'reference':spec['reference'],'reference_registration':spec['reference_registration'],
        'baseline':baseline,'candidate':candidate,'model_registration':dict(spec['baseline_registration'],resolution_conversion='512→768 uniform1.5 before frozen SRT'),
        'scope':'Actual shape/visibility producer comparison, no full candidate native or whole-character ART claim','visual_judgment':'PENDING'})
(O/'source-paired-C.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8',newline='\n');print('C actual source-paired front/oblique/profile boards written')
