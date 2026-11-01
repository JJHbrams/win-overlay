from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops
import sys
O=Path(__file__).parent;V=sys.argv[1] if len(sys.argv)>1 else 'D';folder=O/('lash-review/'+V+'-first');font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);B=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references')
jobs=[('front',B/'received/mia-face-reaffirmed-20261031.png',(530,280,640,340),(475,330,715,465)),('profile',B/'mia-clean-master-v22.png',(548,60,579,83),(295,285,500,475)),('left_oblique',B/'mia-expression-style-confirmed-20261031.png',(1310,65,1362,96),(200,275,600,490))]
board=Image.new('RGB',(1800,1050),(234,239,244));dr=ImageDraw.Draw(board)
def fit(im,x,y):
 s=min(590/im.width,285/im.height);im=im.resize((round(im.width*s),round(im.height*s)));board.paste(im,(x,y))
for ri,(v,p,bb,crop) in enumerate(jobs):
 y=ri*350;fit(Image.open(p).convert('RGB').crop(bb),0,y+40);fit(Image.open(folder/(v+'-production.png')).convert('RGB').crop(crop),600,y+40)
 if v=='front':im=ImageChops.lighter(Image.open(folder/'front-upperONLY.png').convert('RGB'),Image.open(folder/'front-lowerONLY.png').convert('RGB'))
 else:im=Image.open(folder/(v+'-lashONLY.png')).convert('RGB')
 fit(im.crop(crop),1200,y+40)
 dr.text((5,y+8),v+' SOURCE / lash+liner appearance together',font=font,fill='black');dr.text((605,y+8),V+' native production, hair OFF',font=font,fill='black');dr.text((1205,y+8),V+' lash geometry ONLY / physical gray',font=font,fill='black')
 dr.text((5,y+320),'Original source axes/aspect retained. Crop + uniform scale. Gray isolates show geometry; source black decoration does not set hidden skin anatomy.',font=font,fill='black')
board.save(O/('lash-review/'+V+'-source-first.png'));print('LASH_SOURCE_BOARD',V)
