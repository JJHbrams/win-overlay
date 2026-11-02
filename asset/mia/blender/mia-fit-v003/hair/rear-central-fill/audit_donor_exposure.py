"""Original full-scene first-hit exposure of copied source faces. DATA, not ART."""
from pathlib import Path
import numpy as np,json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;R=P.parent/'rear-loop-cleanup';maps=np.load(R/'fullscene-family-ownership-DATA.npz');pro=np.load(P/'detail-prototypes.npz');rows=json.loads((P/'detail-prototypes.json').read_text())['prototypes'];report=[];board=Image.new('RGB',(1800,900),(237,241,244));dr=ImageDraw.Draw(board);f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17);sm=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);colors=[(235,80,65),(55,160,205),(177,104,208)]
for col,view in enumerate(['000','021','018','back_full']):
 face=maps[view+'_source_polygon'];normal=maps[view+'_normal'];owner=maps[view+'_owner'];shade=np.clip(.35+.55*np.abs(normal[:,:,1]),0,1);rgb=np.repeat(shade[:,:,None],3,2)*255;rgb[owner==0]=[42,48,53];stats=[]
 for row,c in zip(rows,colors):
  ids=np.unique(pro[row['name']+'_source_face']);ids=ids[ids>=0];mask=np.isin(face,ids);rgb[mask]=c;stats.append(dict(prototype=row['name'],firsthit_pixels=int(mask.sum()),exposed_source_faces=np.unique(face[mask]).tolist(),sampled_source_faces=len(ids)))
 im=Image.fromarray(rgb.astype(np.uint8)).resize((440,440),Image.Resampling.NEAREST);board.paste(im,(450*col,45));dr.text((450*col+10,10),view+' / original source faces',font=f,fill=(20,30,40));
 for j,r in enumerate(stats):dr.text((450*col+10,505+j*24),r['prototype']+': '+str(r['firsthit_pixels'])+' pixels',font=sm,fill=colors[j])
 report.append(dict(view=view,source='Previously recorded full-scene geometry first-hit DATA at384square; transparent masks may limit this interpretation',prototypes=stats))
dr.text((10,650),'These are SOURCE faces before copying; closed topology alone does not establish visible exterior detail or useful pigment.',font=f,fill=(20,30,40));dr.text((10,680),'Current source Main is unchanged. This audit tests the interior/backing-donor hypothesis; actual source color must be distinguished from lighting.',font=f,fill=(20,30,40));board.save(P/'DONOR_EXPOSURE_DATA.png');(P/'donor-exposure-DATA.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print([(r['view'],[(p['prototype'],p['firsthit_pixels']) for p in r['prototypes']]) for r in report])
