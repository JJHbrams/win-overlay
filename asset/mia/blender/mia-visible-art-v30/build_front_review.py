"""Normal-scale source opening/IPD framing; no repeated image rotation or candidate refit."""
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--candidate',required=True);ap.add_argument('--label',required=True);ap.add_argument('--tag',required=True);a=ap.parse_args()
source_spec=P.parent/'mia-face-finish-v29/final-review/source-boards/reference-review.json'
old=json.loads(source_spec.read_text());front=next(r for r in old['views'] if r['id']=='front')
ref=(source_spec.parent/front['reference']['path']).resolve()
base=P.parent/'mia-face-finish-v29/final-review/source/front-hairOFF.png'
markup=P.parents[1]/'references/received/mia-eye-lash-user-markup-20261102.png'
candidate=Path(a.candidate).resolve();out=P/'reviews'/a.tag;out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
reg={'uniform_scale':1.1698146556808693,'rotation_degrees':0.,'translation_xy':[-142.01146815879025,-223.93878303771004],
 'normalization_basis':'One frozen baselineC opening-centre/IPD scalar and translation; IPD excluded from independent validation. Actual camera already hassource-like roll. No per-eye, eye-chin, candidate refit or extra2Drotation.'}

def transform(im, r, raw=False):
 scale=r['uniform_scale']*(768/im.width if raw else 1.)
 th=math.radians(r['rotation_degrees']);c,s=math.cos(th),math.sin(th);x,y=r['translation_xy']
 return im.convert('RGBA').transform((640,640),Image.Transform.AFFINE,
   (c/scale,s/scale,-(c*x+s*y)/scale,-s/scale,c/scale,(s*x-c*y)/scale),
   Image.Resampling.BICUBIC,fillcolor=(237,242,246,255))
src=Image.open(ref).convert('RGBA');crop=front['reference']['crop_xyxy'];canvas=Image.new('RGBA',src.size,(237,242,246,255));canvas.paste(src.crop(crop),crop[:2])
tiles=[transform(canvas,front['reference_registration']),Image.open(markup).crop((0,50,640,690)).convert('RGBA'),transform(Image.open(base),reg,True),transform(Image.open(candidate),reg,True)]
board=Image.new('RGB',(2560,740),(237,242,246));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
labels=['SOURCE / original aspect','USER red opening / green lashes','C baseline / corrected frame',a.label]
for i,(tile,label) in enumerate(zip(tiles,labels)):
 board.paste(tile.convert('RGB'),(i*640,50));draw.text((i*640+10,12),label,font=font,fill=(24,38,49))
draw.text((12,704),'One frozen IPD scalar + translation; camera roll retained, NO extra2D rotation. This is an actual model preview, not a generated substitute.',font=font,fill=(24,38,49))
path=out/'front-source-markup-before-candidate.png';board.save(path)
(out/'front-frame.json').write_text(json.dumps({'source':{'path':str(ref),'sha256':sha(ref),'crop':crop,'registration':front['reference_registration']},
 'user_markup':{'path':str(markup),'sha256':sha(markup),'crop_xyxy':[0,50,640,690]},
 'baseline':{'path':str(base),'sha256':sha(base)},'candidate':{'path':str(candidate),'sha256':sha(candidate)},
 'model_registration':reg,'render_resolution_conversion':'Uniform768/rawimagewidth only, samecamera/framing required.',
 'board':{'path':str(path),'sha256':sha(path)},'status':'Diagnostic source-frame proof, not source ART pass or strict finalpackage.'},indent=2),encoding='utf-8')
print(str(path))
