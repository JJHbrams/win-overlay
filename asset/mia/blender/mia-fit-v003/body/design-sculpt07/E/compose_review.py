"""Actual image/source/baseline comparisons with original uniform registration."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');B=CAN/'blender/mia-fit-v003/body';A=P/'actual-E';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=json.loads((P/'parameters.json').read_text());source=Image.open(p['sources']['v06_path']).convert('RGB');low=Image.open(p['sources']['low_path']).convert('RGB');records=json.loads((A/'render-records.json').read_text());records=[r for r in records if r['view'] in ['front','profile','F2lowoblique','rearoblique']]
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
scale=1.0022371364653244;shift=4.890380313199103;srcstep=.00185
def crop(center):
    top=(1.785-1.475)/srcstep*scale+shift;side=.4/srcstep*scale;box=[center-side/2,top,center+side/2,top+side]
    return source.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC),box
images=[]
for row in records:
    view=row['view'];size=row['camera']['resolution'][0];candidate=Image.open(A/Path(row['path']).name).convert('RGB');assert sha(A/Path(row['path']).name)==row['sha256']
    oldfolder=P.parent/'D/actual-six-D';baseline=Image.open(oldfolder/('gray-'+view+'.png')).convert('RGB');old=json.loads((oldfolder/('gray-'+view+'-pre-render.json')).read_text());assert row['camera']==old['camera']
    if view in ['front','profile']:
        src,box=crop(239 if view=='front' else 568+(-.035+.018)/srcstep*scale);label='v06 wholeheight uniform registration';limit='Near-profile drawing vs85deg fixture; pose/cloth uncertainty.' if view=='profile' else 'Source clothed envelope; no local width/height normalization.'
    elif view=='F2lowoblique':src=low.crop((887,0,1774,887));box=[887,0,1774,887];label='Reaffirmed F2 original aspect';limit='Estimated40/-8; camera uncertainty yaw짹8,pitch짹6; global mpp retained.'
    else:src,box=crop(935);label='v06 BACK context (covered)';limit='Covered back is context, not matching rear140/-10 calibration; posterior inferred.'
    board=Image.new('RGB',(size*3,size+68),'#202632');draw=ImageDraw.Draw(board)
    for i,(im,title) in enumerate([(src,label),(baseline,'Held07-D actual / same fixture'),(candidate,'NEW sculpt07-E / UNSELECTED')]):
        assert im.size==(size,size);board.paste(im,(i*size,34));draw.text((i*size+8,7),title,fill='white',font=font)
    draw.text((8,size+42),limit+'  Private context seams UNVERIFIED.',font=small,fill='white');file=P/('source-'+view+'.png');board.save(file)
    images.append(dict(view=view,path=str(file),sha256=sha(file),source_crop=box,registration='Frozen wholeheight uniform scale/translation; source pixels unchanged in F2; no aspect warp.',limits=limit,baseline=str(oldfolder/('gray-'+view+'.png')),baseline_sha256=sha(oldfolder/('gray-'+view+'.png')),candidate=row['path'],candidate_sha256=row['sha256']))
summary=Image.new('RGB',(1280,1280),'#202632')
for i,row in enumerate(records):
    im=Image.open(A/Path(row['path']).name).convert('RGB');im.thumbnail((640,600),Image.Resampling.LANCZOS);x=(i%2)*640;y=(i//2)*640;summary.paste(im,(x+(640-im.width)//2,y+34));ImageDraw.Draw(summary).text((x+8,y+7),row['view']+' / STATIC UNSELECTED',font=font,fill='white')
summary.save(P/'actual-four-contact-sheet.png')
(P/'review-records.json').write_text(json.dumps(dict(status='UNSELECTED DESIGN; requires root actual visual judgment',mesh_sha256=sha(P/'sculpt07-E.npz'),parameters_sha256=sha(P/'parameters.json'),images=images,extra_gpu_frames=0,native_saved=False),indent=2)+'\n')
print('SCULPT07_E_SOURCE_BOARDS_DONE',flush=True)
