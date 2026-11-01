from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
O=Path(__file__).parent;folder=O/'medial-review';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
crops={'front':(65,370,705,510),'left_oblique':(0,370,575,580),'profile':(260,290,485,485)}
board=Image.new('RGB',(1800,1200),(234,239,244));dr=ImageDraw.Draw(board)
for r,view in enumerate(['front','left_oblique','profile']):
 y=r*400
 for c,tag in enumerate(['baseline','A']):
  im=Image.open(folder/tag/(view+'-Close0.png')).convert('RGB').crop(crops[view]);scale=min(880/im.width,345/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)));board.paste(im,(c*900,y+45));dr.text((c*900+10,y+10),view+' / '+('G2L baseline' if tag=='baseline' else 'A actual medial correction'),font=font,fill='black')
board.save(folder/'A-neutral-before-after.png')
if all((folder/'baseline-close'/(v+'-Close1.png')).exists() for v in crops):
 board=Image.new('RGB',(1800,1800),(234,239,244));dr=ImageDraw.Draw(board)
 for r,(view,value) in enumerate([(v,val) for v in ['front','left_oblique','profile'] for val in [.5,1]]):
  y=r*300
  for c,tag in enumerate(['baseline-close','A']):
   im=Image.open(folder/tag/(view+'-Close'+str(value)+'.png')).convert('RGB').crop(crops[view]);scale=min(880/im.width,250/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)));board.paste(im,(c*900,y+40));dr.text((c*900+10,y+8),view+' Close'+str(value)+' / '+('G2L baseline' if c==0 else 'A'),font=font,fill='black')
 board.save(folder/'A-closure-before-after.png')
print('MEDIAL_BOARDS_DONE')
