"""Source ART | actual baseline | actual candidate. Uniform SRT only."""
import json,math,hashlib,argparse
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('candidate');ap.add_argument('--baseline',default=str(ROOT/'baseline'));ap.add_argument('--hair',action='store_true');a=ap.parse_args();BASE=Path(a.baseline).resolve();prefix='hair_' if a.hair else '';folder=Path(a.candidate).resolve();manifest=json.loads((folder/'manifest.json').read_text());views=json.loads((folder/'source-view-definitions.json').read_text());base=json.loads((BASE/'render-records.json').read_text());cand=json.loads((folder/'renders/render-records.json').read_text());dest=folder/('source-review-hair' if a.hair else 'source-review');dest.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
art=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
def reg(scale,angle,t,basis):return {'uniform_scale':float(scale),'rotation_degrees':float(math.degrees(angle)),'translation_xy':list(map(float,t)),'normalization_basis':basis}
def transform(im,rr):
 s=rr['uniform_scale'];th=math.radians(rr['rotation_degrees']);A=s*np.array([[math.cos(th),-math.sin(th)],[math.sin(th),math.cos(th)]]);inv=np.linalg.inv(A);tt=-inv@np.array(rr['translation_xy']);out=im.convert('RGBA').transform((640,640),Image.Transform.AFFINE,tuple(inv[0])+tuple(tt[:1])+tuple(inv[1])+tuple(tt[1:]),resample=Image.Resampling.BICUBIC);bg=Image.new('RGBA',(640,640),'#eef1f3');bg.alpha_composite(out);return bg.convert('RGB')
rows=[]
for v in views:
 name=v['id'];crop=v['crop'];w=crop[2]-crop[0];h=crop[3]-crop[1];s=min(590/w,590/h);translation=np.array([(640-w*s)/2-crop[0]*s,(640-h*s)/2-crop[1]*s]);rr=reg(s,0,translation,'Display only: source crop uniformly fitted; no source aspect change')
 ra=np.array(v['anchors'])*s+translation;ma=np.array(base[name]['landmarks']['anchor_pixels']);u=ma[1]-ma[0];vv=ra[1]-ra[0];sc=np.linalg.norm(vv)/np.linalg.norm(u);th=math.atan2(vv[1],vv[0])-math.atan2(u[1],u[0]);A=sc*np.array([[math.cos(th),-math.sin(th)],[math.sin(th),math.cos(th)]]);tr=ra[0]-A@ma[0]
 mr=reg(sc,th,tr,'Baseline iris-carrier midpoint/visible-side center to evaluated chin mapped to manual source eye/chin anchors. This distance and in-plane orientation are normalized, NOT independently validated. Exact same SRT applied to candidate; no candidate refit.')
 source=Image.open(v['reference']);source.crop(crop).save(dest/(name+'-source-crop.png'))
 images=[transform(source,rr),transform(Image.open(BASE/(prefix+name+'.png')),mr),transform(Image.open(folder/'renders'/(prefix+name+'.png')),mr)]
 board=Image.new('RGB',(1920,770),'#eef1f3');d=ImageDraw.Draw(board)
 for i,im in enumerate(images):
  board.paste(im,(i*640,75));d.text((i*640+18,20),['SOURCE ART','c02 BASELINE / ORTHO','CANDIDATE / SAME ORTHO'][i],font=font,fill='#14242e')
 d.text((18,725),name+' | uniform SRT only; '+('hair ON' if a.hair else 'hair hidden')+' on models; eye-to-chin distance normalized, not validated',font=small,fill='#26363d')
 boardpath=dest/(name+'-source-baseline-candidate.png');board.save(boardpath)
 assert base[name]['camera']==cand[name]['camera'],name
 rows.append({'id':name,'reference':{**art(v['reference']),'crop_xyxy':crop,'crop_artifact':art(dest/(name+'-source-crop.png'))},'baseline_render':art(BASE/(prefix+name+'.png')),'candidate_render':art(folder/'renders'/(prefix+name+'.png')),'comparison_board':art(boardpath),'baseline_camera':base[name]['camera'],'candidate_camera':cand[name]['camera'],'reference_registration':rr,'baseline_registration':mr,'candidate_registration':mr,'pose_uncertainty':v['uncertainty'],'observed_differences':'Pending direct visual review of this newly generated board; no art pass.','unresolved':'Inherited paint/temple/cap shading and expression fit remain unfinished. Reference eye gaze and projection are approximate.','material_mode':'Unchanged source production pigment times normal ramp to Emission; same display. Shape comparison only.'})
data={'schema_version':1,'part':'face','baseline_native':manifest['source'],'candidate_native':manifest['native'],'required_views':[v['id'] for v in views],'views':rows,'art_status':'UNVERIFIED; source evidence board is not automatic acceptance'}
(folder/('reference-review-hair.json' if a.hair else 'reference-review.json')).write_text(json.dumps(data,indent=2));print(folder/'reference-review.json')
