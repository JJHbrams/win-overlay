"""Original-aspect whole-height source comparison; one global scale, no feature warp."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;R=P/'current-source4';REF=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png');ref=Image.open(REF).convert('RGBA');records=json.loads((R/'render-records.json').read_text());front=Image.open(R/'front.png').convert('RGBA');a=np.asarray(front)[:,:,3];ys,xs=np.where(a>16);native_crown=int(ys.min());native_sole=int(ys.max());source_crown=54;source_sole=950;scale=(source_sole-source_crown)/(native_sole-native_crown);vertical_shift=source_sole-native_sole*scale
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
rows=[];centers=dict(front=239,profile=568,back=935,oblique=1317);crops=dict(front=(0,440),profile=(440,750),back=(750,1120),oblique=(1120,1536))
for rec in records:
    name=rec['view'];im=Image.new('RGB',(1000,1100),'#273039');draw=ImageDraw.Draw(im);draw.text((12,10),'USER TARGET v06 / '+name,font=font,fill='white');draw.text((512,10),'CURRENT4dc1 / same whole height',font=font,fill='white')
    left,right=crops[name];crop=ref.crop((left,0,right,1024));im.paste(crop,(int(250-(centers[name]-left)),45),crop)
    current=Image.open(rec['path']).convert('RGBA');current=current.resize((round(current.width*scale),round(current.height*scale)),Image.Resampling.LANCZOS);im.paste(current,(round(750-400*scale),round(45+vertical_shift)),current)
    draw.line((0,45+source_crown,1000,45+source_crown),fill='#99b8bd');draw.line((0,45+source_sole,1000,45+source_sole),fill='#99b8bd')
    draw.text((10,1060),f'One global scale {scale:.6f}; crown54/sole950; no shoulder, waist or width normalization.',font=small,fill='white');draw.text((10,1080),'Original aspect; source pose/occlusion uncertainty remains local. Current full head/hair/body included.',font=small,fill='white')
    file=P/('current-v06-'+name+'.png');im.save(file);rows.append(dict(view=name,path=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),native_frame=rec['path'],reference_crop_x=[left,right],horizontal_reference_center=centers[name]))
report=dict(source=str(REF),source_sha256=hashlib.sha256(REF.read_bytes()).hexdigest(),registration=dict(method='One global front sole-to-hair-crown uniform scale/vertical translation applied to ALL four current views; per-view horizontal pelvis centering only. No feature-specific normalization or aspect stretch.',source_crown_y=source_crown,source_sole_y=source_sole,current_alpha16_crown_y=native_crown,current_alpha16_sole_y=native_sole,scale=scale,vertical_translation=vertical_shift,uncertainty='Source hair flyaways and feet vary by about5px acrossviews; head/bust/shoulder landmarks require visible-run limits. This display normalization removes only total-height difference, not head/body ratio.'),boards=rows,native_saved=False)
(P/'current-v06-boards.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('CURRENT_V06_BOARDS_DONE',scale,vertical_shift,flush=True)
