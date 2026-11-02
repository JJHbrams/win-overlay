"""Source/before/current eyebrow preview in the one frozen frontal frame."""
import json,math,hashlib,argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--live-tag',required=True);a=ap.parse_args();O=P/'live'/a.live_tag
old=P.parent/'mia-face-finish-v29/final-review/source-boards/reference-review.json';row=json.loads(old.read_text())['views'][0]
source=(old.parent/row['reference']['path']).resolve();before=P/'reviews/v31-before-depthfixed/source/front-hairOFF.png';current=O/'head-hairOFF.png'
def transform(im,scale,xy):
 return im.convert('RGBA').transform((640,640),Image.Transform.AFFINE,(1/scale,0,-xy[0]/scale,0,1/scale,-xy[1]/scale),Image.Resampling.BICUBIC,fillcolor=(237,242,246,255))
im=Image.open(source).convert('RGBA');sc=Image.new('RGBA',im.size,(237,242,246,255));crop=row['reference']['crop_xyxy'];sc.paste(im.crop(crop),crop[:2]);r=row['reference_registration'];tiles=[transform(sc,r['uniform_scale'],r['translation_xy'])]
for path in [before,current]:
 im=Image.open(path);tiles.append(transform(im,1.1698146556808693*768/im.width,[-142.01146815879025,-223.93878303771004]))
board=Image.new('RGB',(1920,740),(237,242,246));d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21)
for i,(im,label) in enumerate(zip(tiles,['SOURCE / original aspect','BEFORE / inherited brow arch','WORKING / source brow direction'])):
 board.paste(im.convert('RGB'),(640*i,50));d.text((640*i+10,12),label,font=font,fill=(24,38,49))
d.text((12,702),'Same source camera/lighting and frozen IPD frame. Hair OFF for brow inspection. Closed-lash style is still being refined.',font=font,fill=(24,38,49))
dest=O/'source-before-current-brows.png';board.save(dest)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
(O/'brow-preview-provenance.json').write_text(json.dumps({'source':{'path':str(source),'sha256':sha(source)},'before':{'path':str(before),'sha256':sha(before)},'current':{'path':str(current),'sha256':sha(current)},'live_record':json.loads((O/'live-review.json').read_text()),'board':{'path':str(dest),'sha256':sha(dest)},'framing':'Source unchanged aspect, uniform cropfit. Model fixed C-IPDscalar+translation, resolution-only conversion768/rawWidth, no extra2Droll/perfeaturefit.','status':'Working eyebrow preview, not whole-source ART.'},indent=2),encoding='utf-8')
print(dest)
