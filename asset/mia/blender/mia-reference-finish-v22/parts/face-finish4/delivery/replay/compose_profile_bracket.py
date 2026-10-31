from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,hashlib,numpy as np
H=Path(__file__).resolve().parent;F=H/'finish-4/profile-bracket';d=json.loads((F/'camera-records.json').read_text());ref=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/mia-clean-master-v22.png');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
lighting=json.loads((H/'finish-4/renders/render-records.json').read_text())['profile']['camera']['lighting']
for record in d['records'].values():record['camera']['lighting']=lighting
d['metadata_note']='Actual identical root rig recorded numerically. Removed obsolete generic helper production_skin description; no camera or native change.'
(F/'camera-records.json').write_text(json.dumps(d,indent=2))
crop=[525,48,605,120];s=5.5;tr=np.array([30-crop[0]*s,35-crop[1]*s]);ra=np.array([[558,70],[553,107]])*s+tr
def render(im,scale,angle,t):
 A=scale*np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);inv=np.linalg.inv(A);tt=-inv@t;im=im.convert('RGBA').transform((500,500),Image.Transform.AFFINE,tuple(inv[0])+tuple(tt[:1])+tuple(inv[1])+tuple(tt[1:]),resample=Image.Resampling.BICUBIC);bg=Image.new('RGBA',(500,500),'#edf1f4');bg.alpha_composite(im);return bg.convert('RGB')
board=Image.new('RGB',(2500,1240),'#edf1f4');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',23);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19);records={}
for row,hair in enumerate([True,False]):
 src=render(Image.open(ref),s,0,tr);board.paste(src,(0,70+row*570));draw.text((15,30+row*570),'SOURCE SIDE ART',font=font,fill='#172633')
 for col,yaw in enumerate([60,70,80,90],1):
  name=('hair_' if hair else 'bare_')+str(yaw);ma=np.array(d['records'][name]['landmarks']['anchor_pixels']);u=ma[1]-ma[0];v=ra[1]-ra[0];scale=np.linalg.norm(v)/np.linalg.norm(u);angle=math.atan2(v[1],v[0])-math.atan2(u[1],u[0]);A=scale*np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]]);t=ra[0]-A@ma[0];board.paste(render(Image.open(F/(name+'.png')),scale,angle,t),(col*500,70+row*570));draw.text((col*500+15,30+row*570),f'YAW {yaw} / '+('HAIR ON' if hair else 'HAIR HIDDEN'),font=font,fill='#172633');records[name]={'uniform_scale':float(scale),'rotation_degrees':float(math.degrees(angle)),'translation_xy':t.tolist(),'normalization_basis':'Visible-side iris carrier center to actual chin normalized to manual source eye/chin; this height/orientation is not validated. No anisotropic warp.','render_sha256':sha(F/(name+'.png'))}
draw.text((20,1200),'Same frozen finish4 geometry, ORTHO .29, common scene light. Each view uses uniform eye/chin SRT only. Drawn SIDE label is not a calibrated90-degree camera.',font=small,fill='#172633');board.save(F/'source-profile-yaw-bracket.png')
(F/'comparison-registration.json').write_text(json.dumps({'reference':{'path':str(ref),'sha256':sha(ref),'crop_xyxy':crop,'anchors':[[558,70],[553,107]],'anchor_uncertainty_original_px':2},'candidate':d['native'],'registrations':records,'board_sha256':sha(F/'source-profile-yaw-bracket.png'),'pose_uncertainty':'Unknown stylized source projection; yaw60..90 bracket, pitch±6; hair and source eye drawing can independently affect iris exposure. SRT eye-to-chin anchors cannot prove exact camera or profile depth.'},indent=2));print(F/'source-profile-yaw-bracket.png')
