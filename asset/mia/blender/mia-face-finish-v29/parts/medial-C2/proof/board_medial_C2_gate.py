from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).parent;R=O/'medial-review';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
jobs=[(R/'C2'/(v+'-Close'+str(k)+'.png'),v+' Close'+str(k)) for v in ['front','left_oblique','profile'] for k in [0,.5,1]]+[(R/'C2-post'/(n+'.png'),n) for n in ['right_oblique-clean','lowRIGHT-clean','unilateralR-front','unilateralL-front','head-12-clean','head+12-clean']]
board=Image.new('RGB',(1800,1800),(234,239,244));dr=ImageDraw.Draw(board)
for i,(p,label) in enumerate(jobs):
 x=(i%3)*600;y=(i//3)*360;im=Image.open(p).convert('RGB');crop=(70,355,710,545) if label.startswith(('front','unilateral','head')) else (265,285,500,500) if label.startswith('profile') else (170,155,545,315) if label.startswith('lowRIGHT') else (0,310,740,600);im=im.crop(crop);s=min(590/im.width,325/im.height);im=im.resize((round(im.width*s),round(im.height*s)));board.paste(im,(x,y+30));dr.text((x+5,y+5),label,font=font,fill='black')
board.save(R/'C2-geometry-gate-contactsheet.png')
source=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-face-reaffirmed-20261031.png');src=Image.open(source).convert('RGB');b=Image.new('RGB',(1800,1050),(234,239,244));d=ImageDraw.Draw(b)
def pastefit(im,x,y,w,h):
 s=min(w/im.width,h/im.height);out=im.resize((round(im.width*s),round(im.height*s)));b.paste(out,(x,y))
pastefit(src.crop((340,220,700,490)),0,40,590,530)
for x,tag in [(600,'baseline'),(1200,'C2')]:pastefit(Image.open(R/(tag+'-identity/front-production-hairOFF.png')).convert('RGB').crop((90,140,690,730)),x,40,590,530)
pastefit(src.crop((385,280,640,350)),0,660,590,250)
for x,tag in [(600,'baseline'),(1200,'C2')]:pastefit(Image.open(R/tag/'front-Close0.png').convert('RGB').crop((65,370,705,510)),x,660,590,250)
for x,t in [(0,'SOURCE / original pixels'),(600,'G2L / native with ink'),(1200,'C2 / actual modeled canthus + retained ink')]:d.text((x+5,10),t,font=font,fill='black')
d.text((5,610),'Visible source eye border; covered anatomy UNKNOWN. Below: native clean-lid before / after, ink/lash/brow/UV makeup OFF.',font=font,fill='black');d.text((5,980),'Crop + uniform display scale only; native source-camera axes retained. Stage geometry/identity check, not final source4 or ART acceptance.',font=font,fill='black');b.save(R/'C2-source-identity-clean-ink.png');print('C2_GATE_BOARDS_DONE')
