"""Actual coupled-root pairs and requested SOURCE|D|09 front/profile."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;E=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-fit-v003/body/design-sculpt07/E');D=E.parent/'D';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
extra=json.loads((P/'actual-extra3/render-records.json').read_text(encoding='utf-8'));initial=json.loads((P/'actual8/render-records.json').read_text(encoding='utf-8'));params=json.loads((E/'parameters.json').read_text(encoding='utf-8'));source=params['sources'];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);records=[]
for row in extra:
    old=Image.open(row['baseline_E_render']['path']).convert('RGB');new=Image.open(row['path']).convert('RGB');size=new.width;assert old.size==new.size
    assert sha(row['path'])==row['sha256'] and sha(row['baseline_E_render']['path'])==row['baseline_E_render']['sha256']
    tiles=[(old,'FROZEN E / '+row['view']),(new,'09 ACCUMULATED JOIN / '+row['view'])];source_item=None
    if row['view']=='F2lowoblique':
        ref=Path(source['low_path']);assert sha(ref)==source['low_sha256'];original=Image.open(ref).convert('RGB');assert original.size==(1774,887)
        tiles.insert(0,(original.crop((887,0,1774,887)),'Reaffirmed F2 / original pixels'));source_item=dict(path=str(ref),sha256=sha(ref),crop_xyxy=[887,0,1774,887],original_size=list(original.size))
    board=Image.new('RGB',(size*len(tiles),size+68),'#202632');d=ImageDraw.Draw(board)
    for i,(im,label) in enumerate(tiles):board.paste(im,(size*i,34));d.text((size*i+8,7),label,font=font,fill='white')
    d.text((8,size+42),'Same frozen geometry/camera/gray/light; coupled anterior-root check. F2 camera estimated40/-8; source cloth/pose uncertainty. No whole-body ART pass.',font=small,fill='white')
    file=P/('source-E-09-F2lowoblique.png' if source_item else 'E-09-gray-'+row['view']+'.png');board.save(file);records.append(dict(view=row['view'],path=str(file),sha256=sha(file),baseline_E=row['baseline_E_render'],candidate=dict(path=row['path'],sha256=row['sha256']),source=source_item,camera=row['camera']))
review=json.loads((E/'review-records.json').read_text(encoding='utf-8'));ref=Path(source['v06_path']);assert sha(ref)==source['v06_sha256'];original=Image.open(ref).convert('RGB')
for view in ['front','profile']:
    row=next(r for r in initial if r['view']==view);drow=json.loads((D/'actual-six-D'/('gray-'+view+'-pre-render.json')).read_text(encoding='utf-8'));assert row['camera']==drow['camera'];spec=next(r for r in review['images'] if r['view']==view);box=spec['source_crop'];assert abs((box[2]-box[0])-(box[3]-box[1]))<1e-6
    src=original.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC);oldpath=D/'actual-six-D'/('gray-'+view+'.png');old=Image.open(oldpath).convert('RGB');new=Image.open(row['path']).convert('RGB');board=Image.new('RGB',(1920,708),'#202632');d=ImageDraw.Draw(board)
    for i,(im,label) in enumerate([(src,'v06 SOURCE / frozen uniform SRT'),(old,'HELD D / flatter supported baseline'),(new,'09 = E support + accumulated join')]):board.paste(im,(i*640,34));d.text((i*640+8,7),label,font=font,fill='white')
    d.text((8,682),spec['limits']+' Separate original-aspect source; no local feature/width refit. Static guide/context seams remain unverified.',font=small,fill='white');file=P/('source-D-09-'+view+'.png');board.save(file)
    records.append(dict(view=view,path=str(file),sha256=sha(file),baseline_D=dict(path=str(oldpath),sha256=sha(oldpath)),candidate=dict(path=row['path'],sha256=row['sha256']),source=dict(path=str(ref),sha256=sha(ref),crop_xyxy=box,original_size=list(original.size)),camera=row['camera'],registration=spec['registration']))
(P/'extra-review-records.json').write_text(json.dumps(dict(additional_actual_frames=3,initial_actual_frames=8,geometry_variants=1,boards=records,source_facts='v06 wholeheight authority; F2 clothed support/root evidence with estimated camera. No new source dimensions inferred.'),indent=2)+'\n',encoding='utf-8',newline='\n')
print('POSTERIOR09_EXTRA_AND_SOURCE_D_BOARDS_READY')
