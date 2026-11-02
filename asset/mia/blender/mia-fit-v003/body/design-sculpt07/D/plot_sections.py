"""Actual mesh intersections, not rendered art or reconstructed naked anatomy."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;d=np.load(P/'actual-sections.npz');audit=json.loads((P/'cpu-audit.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
im=Image.new('RGB',(1200,740),'#202632');draw=ImageDraw.Draw(im)
for i,(name,points) in enumerate(d.items()):
    x=(i%2)*600;y=(i//2)*370;row=audit['source_support_rows'][i];draw.text((x+12,y+8),'ACTUAL Z %.4f / F2 residual %.1f mm'%(row['z'],row['support_residual_mm']),font=font,fill='white')
    origin=np.array([x+300,y+240]);xy=np.c_[points[:,0]*1400,points[:,1]*1100]+origin
    for q in xy:draw.ellipse((q[0]-1,q[1]-1,q[0]+1,q[1]+1),fill='#67dcca')
    draw.line((x+300,y+40,x+300,y+355),fill='#596272');draw.text((x+12,y+337),'X horizontal / anterior -Y up / no image normalization',font=font,fill='#b7c4d5')
im.save(P/'actual-section-audit.png');print('SCULPT07_D_SECTION_PLOT_DONE')
