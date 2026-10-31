"""Original source registration retained; no feature refit. Actual raster composition only."""
from pathlib import Path
import json,hashlib,math,copy,numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;old=json.loads((H.parent/'finish-4/reference-review-hair.json').read_text());records=json.loads((H/'render-records.json').read_text());man=json.loads((H/'manifest.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();art=lambda p:{'path':str(Path(p)),'sha256':sha(p)}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16)
def pane(path,reg):
 im=Image.open(path).convert('RGBA');angle=math.radians(reg['rotation_degrees']);A=reg['uniform_scale']*np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);iv=np.linalg.inv(A);t=-iv@np.array(reg['translation_xy']);im=im.transform((640,640),Image.Transform.AFFINE,tuple(iv[0])+tuple(t[:1])+tuple(iv[1])+tuple(t[1:]),resample=Image.Resampling.BICUBIC);bg=Image.new('RGBA',(640,640),'#edf1f4');bg.alpha_composite(im);return bg.convert('RGB')
rows=[]
for row in old['views']:
 name=row['id'];reg=row['baseline_registration'];b=records['baseline/'+name];c=records['candidate/'+name];im=Image.new('RGB',(1920,745),'#edf1f4');draw=ImageDraw.Draw(im)
 for i,(p,rr,label) in enumerate([(row['reference']['path'],row['reference_registration'],'SOURCE ART'),(b['render']['path'],reg,'FACE4 / SAME LIGHT'),(c['render']['path'],reg,'FINISH5 / LOCAL PIGMENT')]):im.paste(pane(p,rr),(640*i,55));draw.text((640*i+12,15),label,font=font,fill='#172633')
 draw.text((12,710),name+' | original uniform registration retained; geometry/eyes/lash/light unchanged; pigment-only A/B, not an ART pass',font=small,fill='#172633');dest=H/(name+'-source-face4-finish5.png');im.save(dest);n=copy.deepcopy(row);n.update(baseline_render=b['render'],candidate_render=c['render'],comparison_board=art(dest),baseline_camera=b['camera'],candidate_camera=c['camera'],observed_differences='Local fixed-UV under-eye pigment contrast control; actual source comparison pending independent review.',material_mode='Identical full native geometry and actual fixed root light. Only face-skin original-UV procedural crescent pigment differs. No source image bytes edited.');rows.append(n)
for name in ['front','left_oblique']:
 reg=next(v for v in old['views'] if v['id']==name)['baseline_registration'];out=Image.new('RGB',(1280,690),'#edf1f4');draw=ImageDraw.Draw(out)
 for i,role in enumerate(['baseline','candidate']):out.paste(pane(H/role/('bare_'+name+'.png'),reg),(i*640,50));draw.text((i*640+12,15),'FACE4 BARE' if i==0 else 'FINISH5 BARE',font=font,fill='#172633')
 out.save(H/('bare-'+name+'-ab.png'))
for row in rows:row.update(json.loads((H/'view-observations.json').read_text())[row['id']])
package={'schema_version':1,'part':'face','baseline_native':man['source'],'candidate_native':man['native'],'required_views':old['required_views'],'views':rows,'art_status':'PIGMENT A/B ONLY; no geometry/likeness or animation pass','registration_source':art(H.parent/'finish-4/reference-review-hair.json')};(H/'reference-review.json').write_text(json.dumps(package,indent=2));print('FINISH5_BOARDS_DONE')
