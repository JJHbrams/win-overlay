"""Original-aspect source context beside actual paired renders; no feature registration."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
P=Path(__file__).resolve().parent;O=P/'actual-first4';src=Image.open('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/mia-clean-master-v22.png').convert('RGB');f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',21);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);board=Image.new('RGB',(1740,1480),(237,241,244));dr=ImageDraw.Draw(board)
def aspect_fit(im,box):
 x,y,w,h=box;s=min(w/im.width,h/im.height);r=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS);board.paste(r,(x+(w-r.width)//2,y+(h-r.height)//2))
for row,(view,title,box) in enumerate([('back_full','v22 BACK source / original aspect',(748,0,942,230)),('oblique_low_full','v22 PROFILE context / not same camera',(510,0,710,230))]):
 y=20+row*715;dr.text((15,y),title,font=small,fill=(20,30,40));aspect_fit(src.crop(box),(10,y+40,420,640))
 for x,stage in [(445,'baseline'),(1090,'candidate')]:
  path=O/(stage+'-'+view+'.png');im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(40,44,47,255));bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x,y+40));dr.text((x+5,y),(stage+' / '+view+' / actual shader'),font=f,fill=(20,30,40))
dr.text((15,1455),'Same actual camera/light/pose within each render pair; source is qualitative context, never aspect-stretched or feature-warped. Partial loop cleanup only.',font=small,fill=(20,30,40));board.save(P/'ACTUAL_SOURCE_BACK_LOW_REVIEW.png');print('ACTUAL_REVIEW_BOARD',P/'ACTUAL_SOURCE_BACK_LOW_REVIEW.png')
