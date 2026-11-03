"""Actual frozen E /09 pairs; source context keeps frozen wholeheight SRT."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageChops
P=Path(__file__).resolve().parent;A=P/'actual8';CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');E=CAN/'blender/mia-fit-v003/body/design-sculpt07/E'
rows=json.loads((A/'render-records.json').read_text(encoding='utf-8'));assert len(rows)==8
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);records=[]
for row in rows:
    old=Path(row['baseline_E_render']['path']);new=Path(row['path']);assert sha(old)==row['baseline_E_render']['sha256'] and sha(new)==row['sha256']
    left=Image.open(old).convert('RGB');right=Image.open(new).convert('RGB');assert left.size==right.size==(640,640)
    board=Image.new('RGB',(1280,709),'#202632');d=ImageDraw.Draw(board)
    for x,im,label in [(0,left,'FROZEN E / '+row['mode']+' '+row['view']),(640,right,'09 ONE POSTERIOR UNION / '+row['mode']+' '+row['view'])]:
        board.paste(im,(x,34));d.text((x+8,7),label,font=font,fill='white')
    d.text((8,682),'Actual identical camera/light/material; E breast support held. Unselected static design, temporary context seams; no whole-body ART pass.',font=small,fill='white')
    file=P/('E-09-'+row['mode']+'-'+row['view']+'.png');board.save(file)
    if row['view']=='rear140':
        crop=(150,310,240,440);detail=Image.new('RGB',(720,570),'#202632');dd=ImageDraw.Draw(detail)
        for x,im,label in [(0,left,'E actual'),(360,right,'09 actual')]:
            detail.paste(im.crop(crop).resize((270,390),Image.Resampling.NEAREST),(x+45,50));dd.text((x+10,10),label+' / '+row['mode'],font=font,fill='white')
        dd.text((10,462),'Same posterior root pixels150..240,310..440; uniform3x nearest display.',font=small,fill='white');dd.text((10,486),'Local Normal transition is not inferred from the delta magnitude.',font=small,fill='white');detail.save(P/('E-09-detail-'+row['mode']+'-rear140.png'))
    records.append(dict(view=row['view'],mode=row['mode'],board=str(file),board_sha256=sha(file),baseline=row['baseline_E_render'],candidate=dict(path=str(new),sha256=row['sha256']),camera=row['camera'],same_material=True,scope='Posterior component comparison only; E breast exact; broad surfaces bounded; ART unselected'))
source=json.loads((E/'parameters.json').read_text(encoding='utf-8'))['sources'];source_path=Path(source['v06_path']);assert sha(source_path)==source['v06_sha256'];original=Image.open(source_path).convert('RGB');oldreview=json.loads((E/'review-records.json').read_text(encoding='utf-8'))
for view in ['front','profile']:
    r=next(r for r in rows if r['view']==view);spec=next(r for r in oldreview['images'] if r['view']==view);box=spec['source_crop']
    assert abs((box[2]-box[0])-(box[3]-box[1]))<1e-6
    src=original.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC)
    old=Image.open(r['baseline_E_render']['path']).convert('RGB');new=Image.open(r['path']).convert('RGB');board=Image.new('RGB',(1920,709),'#202632');d=ImageDraw.Draw(board)
    for i,(im,label) in enumerate([(src,'v06 SOURCE / original-aspect SRT'),(old,'FROZEN E / supported body context'),(new,'09 ACCUMULATED JOIN / UNSELECTED')]):board.paste(im,(640*i,34));d.text((640*i+8,7),label,font=font,fill='white')
    d.text((8,682),spec['limits']+' E breast unchanged; temporary context seams. This component does not accept the whole body.',font=small,fill='white')
    file=P/('source-E-09-'+view+'.png');board.save(file);records.append(dict(view=view,mode='source_context',board=str(file),board_sha256=sha(file),source=dict(path=str(source_path),sha256=sha(source_path),crop_xyxy=box,original_size=list(original.size)),registration=spec['registration'],scope='Frozen E wholeheight source registration reused, no local fit or aspect warp; posterior component only'))
(P/'review-records.json').write_text(json.dumps(dict(candidate_sha256=sha(P/'posterior09.npz'),actual_frames=8,extra_frames=0,boards=records,ART='PENDING actual09 review; no adoption from CPU or renders'),indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_ACTUAL_BOARDS_READY')
