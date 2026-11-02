"""Existing-pixel crops and semantic annotations only. No Blender/model work."""
from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia');R=CAN/'blender/mia-refinement-v002/review/integrated-R3b';E=CAN/'blender/mia-refinement-v002/expressions'
SHA='4dc117364643078827f1f1b05288c086c1b6279689634087809e50e4a06d4fc1';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
records=json.loads((R/'expressions/render-records.json').read_text(encoding='utf-8'));byid={r['id']:r for r in records};rows=json.loads((E/'expression-intents.json').read_text(encoding='utf-8'))['panels'];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
manifest=[]
for page in range(2):
 board=Image.new('RGB',(1500,880),(235,240,245));d=ImageDraw.Draw(board)
 for k,row in enumerate(rows[page*8:page*8+8]):
  i=row['panel'];x=(k%2)*750;y=(k//2)*220
  d.text((x+5,y+3),f'P{i:02} | actual 4dc1: hair ON / hair OFF',font=font,fill=(20,30,40))
  for j,label in enumerate(['hairON','hairOFF']):
   record=byid[f"P{i:02}-{row['id']}-{label}"];assert record['native_sha256']==SHA and sha(record['path'])==record['sha256'];im=Image.open(record['path']).convert('RGB');assert im.size==(512,512);crop=(130,180,380,300);im=im.crop(crop).resize((375,180),Image.Resampling.NEAREST);board.paste(im,(x+j*375,y+28));manifest.append(dict(panel=i,role=label,path=record['path'],sha256=record['sha256'],crop_xyxy=crop,uniform_display_scale=1.5,native_sha256=record['native_sha256']))
 board.save(P/f'actual-source16-brow-hairON-OFF-page{page+1}.png')
portrait=CAN/'references/received/mia-face-reaffirmed-20261031.png';on=R/'source/front-hairON.png';off=R/'source/front-hairOFF.png';srecords=json.loads((R/'source/render-records.json').read_text(encoding='utf-8'));sr={r['id']:r for r in srecords}
for name,file in [('front-hairON',on),('front-hairOFF',off)]:assert sr[name]['native_sha256']==SHA and sha(file)==sr[name]['sha256']
cyan=(0,210,230);amber=(240,150,0);green=(30,205,75)
source_paths=dict(brow=[[[410,277.5],[425,276],[455,275]],[[520,270.5],[537,265],[551,262]]],crease=[[[409,301],[438,299],[466,304]],[[539,290],[558,283],[583,282]]],lash=[[[398,318],[420,310],[451,311],[476,317]],[[538,309],[559,297],[594,292],[625,296]]])
model_paths=dict(brow=[[[215,370],[242,357],[286,353],[337,355]],[[395,348],[438,335],[483,328],[527,326]]],crease=[[[238,397],[282,389],[326,395]],[[435,380],[472,373],[517,376]]],lash=[[[214,410],[246,400],[288,404],[336,419]],[[424,399],[450,388],[494,383],[548,381]]])
board=Image.new('RGB',(2400,765),(235,240,245));d=ImageDraw.Draw(board)
for col,(file,box,scale,title,paths) in enumerate([(portrait,(370,240,650,350),2.5,'SOURCE portrait / visible fragments',source_paths),(on,(185,300,560,445),2.,'Actual 4dc1 / hair ON',None),(off,(185,300,560,445),2.,'Actual 4dc1 / hair OFF',model_paths)]):
 im=Image.open(file).convert('RGB').crop(box);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);x=col*800;d.text((x+6,7),title,font=font,fill=(20,30,40));board.paste(im,(x,38));ann=im.copy();ad=ImageDraw.Draw(ann)
 if paths:
  for kind,color in [('brow',cyan),('crease',amber),('lash',green)]:
   for line in paths[kind]:ad.line([((px-box[0])*scale,(py-box[1])*scale) for px,py in line],fill=color,width=3)
 else:
  # Circle only the observed tiny inner brow fragment. The long brown mark below is the crease.
  px,py=(397-box[0])*scale,(347-box[1])*scale;ad.ellipse((px-10,py-10,px+10,py+10),outline=cyan,width=3)
  ad.line([((435-box[0])*scale,(376-box[1])*scale),((500-box[0])*scale,(372-box[1])*scale)],fill=amber,width=3)
  ad.line([((440-box[0])*scale,(394-box[1])*scale),((510-box[0])*scale,(384-box[1])*scale)],fill=green,width=3)
 board.paste(ann,(x,402));d.text((x+6,350),'Unmarked existing pixels',font=small,fill=(20,30,40))
d.text((6,719),'Cyan: true brow fragments | Amber: upper crease | Green: upper lash/liner | Hidden tails and central covered spans are not reconstructed.',font=font,fill=(20,30,40))
d.text((6,744),'Semantic crop layout only. Original aspect and uniform scales preserved. Source pose differs; this is not a proportion registration.',font=small,fill=(20,30,40));board.save(P/'portrait-actual-brow-crease-lash-annotated.png')
# Conservative screen-color proxy, not a geometric ownership or pixel-perfect visibility claim.
a=np.asarray(Image.open(off).convert('RGB'),dtype=np.int16);b=np.asarray(Image.open(on).convert('RGB'),dtype=np.int16);stats=[]
for side,box in [('screen_left',(205,335,345,378)),('screen_right',(380,310,535,355))]:
 x0,y0,x1,y1=box;aa=a[y0:y1,x0:x1];bb=b[y0:y1,x0:x1];mask=aa.max(2)<110;match=mask&(np.abs(aa-bb).max(2)<=2);stats.append(dict(side=side,window_xyxy=box,dark_hairOFF_pixels=int(mask.sum()),matching_hairON_pixels_within2RGB=int(match.sum()),matching_fraction=float(match.sum()/max(1,mask.sum())),limit='Brow-only manually checked windows. Color agreement is an appearance proxy; antialiasing and coincident hair ink prevent interpreting this as an exact geometric visibility fraction.'))
record=dict(native_sha256=SHA,source_portrait=dict(path=str(portrait),sha256=sha(portrait)),source_expression_sheet=dict(path=str(CAN/'references/mia-expression-style-confirmed-20261031.png'),sha256=sha(CAN/'references/mia-expression-style-confirmed-20261031.png')),actual_pair_crops=manifest,all32_expression_hashes_verified=True,source_front_pair_hashes_verified=True,annotations=dict(source_native_xy=source_paths,actual_hairOFF_native_xy=model_paths,uncertainty='Manual semantic traces, roughly1..3original pixels; line is marked for identification, not a new contour or texture.'),appearance_proxy=stats,no_render=True,no_native_open_or_save=True,no_model_changes=True)
(P/'layout-evidence.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(stats,indent=2))
