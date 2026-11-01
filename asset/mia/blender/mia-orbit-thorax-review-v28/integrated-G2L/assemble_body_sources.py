"""Unwarped source|baseline|candidate boards. Only uniform S/R/T on source.

Torso-height registration: v06 shoulder guideline~221 to narrow waist~386
maps to fixed model Z1.38 to1.145. It cannot validate that normalized distance.
Clothed/illustrated source yaw and hidden nude anatomy remain uncertain.
"""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib,argparse
ap=argparse.ArgumentParser();ap.add_argument('--tag',default='D');ap.add_argument('--candidate-role');ap.add_argument('--views',default='front,profile,back,oblique,anchor-front');args=ap.parse_args();candidate_role=args.candidate_role or 'candidate-'+args.tag
P=Path(__file__).parent
R=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/body-foundation')
REF=R/'v06/mia-body-turnaround-v06.png';ANCHOR=R/'anchors/mia-body-front-user-selected-20261031.png'
OUT=P/('source4-uniform-'+args.tag);OUT.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
def art(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
source=Image.open(REF).convert('RGB');scale=(1.38-1.145)*800/.64/(386-221)
rows=[]
def make(name,panel,center,role='v06'):
 if role=='v06':
  crop=(panel*384,0,(panel+1)*384,1024);im=source.crop(crop);srcshoulder=221;srcwaist=386;s=scale;cx=center-panel*384
 else:
  im=Image.open(ANCHOR).convert('RGB');crop=(0,0,im.width,im.height);srcshoulder=295;srcwaist=550;s=(1.38-1.145)*800/.64/(srcwaist-srcshoulder);cx=center
 tx=349.4-s*cx;ty=(400-(1.38-1.24)*800/.64)-s*srcshoulder
 # Profile and oblique torso midlines use a recorded translation, not a width fit.
 if name=='profile':tx-=40
 if name=='oblique':tx-=22
 reference=im.transform((700,800),Image.Transform.AFFINE,(1/s,0,-tx/s,0,1/s,-ty/s),Image.Resampling.BICUBIC,fillcolor=(36,36,36))
 view=name if name!='anchor-front' else 'front'
 if name=='oblique' and (P/'renders/baseline/geometry-clay/yaw30.png').exists() and (P/'renders'/candidate_role/'geometry-clay/yaw30.png').exists():view='yaw30'
 b=Image.open(P/'renders/baseline/geometry-clay'/(view+'.png')).convert('RGBA') if (P/'renders/baseline/geometry-clay'/(view+'.png')).exists() else Image.open(P/'renders/baseline/clay'/(view+'.png')).convert('RGBA')
 c=Image.open(P/'renders'/candidate_role/'geometry-clay'/(view+'.png')).convert('RGBA')
 board=Image.new('RGB',(2100,700),(36,36,36));d=ImageDraw.Draw(board)
 for j,(tile,title) in enumerate([(reference,'SOURCE: '+role+' '+name+' (uniform SRT)'),(b,'e9 baseline | ORTHO '+view),(c,args.tag+' correction WIP | ORTHO '+view)]):
  if tile.mode=='RGBA':
   flat=Image.new('RGBA',tile.size,(36,36,36,255));flat.alpha_composite(tile);tile=flat.convert('RGB')
  tile=tile.crop((0,150,700,800));board.paste(tile,(j*700,45));d.text((j*700+12,12),title,font=font,fill='white')
 d.text((12,675),'Shoulder-to-waist normalized, not verified; bra hides nude attachment. Source aspect/color preserved. Source yaw is estimated.',font=font,fill='white')
 file=OUT/(name+'.png');board.save(file)
 rows.append({'id':name,'render_view':view,'reference':art(REF if role=='v06' else ANCHOR),'crop_xyxy':list(crop),'source_registration':{'uniform_scale':s,'scale_xy':[s,s],'rotation_degrees':0,'translation_xy':[tx,ty],'nonuniform_scale':False,'source_shoulder_y':srcshoulder,'source_waist_y':srcwaist,'model_shoulder_z':1.38,'model_waist_z':1.145,'normalized_distance_is_not_validation':True,'landmark_uncertainty_px':10,'reference_yaw_estimate_degrees':0 if name in ('front','anchor-front') else 90 if name=='profile' else 180 if name=='back' else 30,'yaw_uncertainty_degrees':0 if name in ('front','anchor-front') else 15},'board':art(file),'comparison_crop_xyxy':[0,150,700,800],'source_visibility_limit':'bra-covered breast volumes and hair-covered back; inferred nude attachment not exact measured source anatomy'})
for n,i,c in [('front',0,242),('profile',1,546),('back',2,934),('oblique',3,1296)]:
 if n in args.views.split(','):make(n,i,c)
if 'anchor-front' in args.views.split(','):make('anchor-front',0,518,'selected-front')
(OUT/'registration.json').write_text(json.dumps({'source_art_immutable':True,'source_scale_policy':'rotation + uniform scale + translation only; no fitted width, recolor or local warp','views':rows,'status':'WIP corresponding art review; source angles and bra coverage limit exact nude matching'},indent=2),encoding='utf8')
print('UNIFORM_SOURCE_BOARDS',len(rows))
