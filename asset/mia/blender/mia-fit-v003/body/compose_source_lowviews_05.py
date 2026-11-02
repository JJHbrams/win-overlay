"""Untouched source | actual05 | actual3Dguide projection. No image warp."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'posed-target';C=P/'source-binding';s=json.loads((C/'constraints.json').read_text());art=Image.open(s['source']).convert('RGB');guides=json.loads((C/'actual-guides-05.json').read_text());records=json.loads((O/'actual-05/render-records.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13);rows=[]
for r in records:
    view='E2' if r['view']=='E2front' else 'F2';crop=s['cameras'][view]['source_crop'];source=art.crop(crop);actual=Image.open(r['path']).convert('RGB');assert source.size==actual.size==(887,887);overlay=actual.copy();d=ImageDraw.Draw(overlay);inv=np.linalg.inv(np.asarray(r['camera']['matrix']));scale=r['camera']['ortho_scale']
    for curve in guides['curves']:
        pts=np.asarray(curve['points']);camera=np.c_[pts,np.ones(len(pts))]@inv.T;xy=np.c_[443.5+camera[:,0]*887/scale,443.5-camera[:,1]*887/scale];color='#00cdd1' if curve['kind']=='observed-envelope-constrained' else '#e5a529'
        if curve['closed']:xy=np.r_[xy,xy[:1]];pts=np.r_[pts,pts[:1]]
        for k,(a,b) in enumerate(zip(xy[:-1],xy[1:])):
            if pts[k,1]<.015 and pts[k+1,1]<.015:d.line([tuple(a),tuple(b)],fill=color,width=1)
    board=Image.new('RGB',(2661,990),'#273039');dr=ImageDraw.Draw(board)
    for x,img,label in [(0,source,'USER E2/F2 / original pixels'),(887,actual,'ACTUAL05 / source-bound gray; hairOFF'),(1774,overlay,'ACTUAL3D guide projection / Xray')]:board.paste(img,(x,35));dr.text((x+10,8),label,font=font,fill='white')
    dr.text((10,931),f'{view}: estimated yaw{r["camera"]["yaw"]}°, pitch{r["camera"]["pitch"]}°; ORTHO{scale:.6f}m; source/body original aspect; no per-feature image fit.',font=small,fill='white')
    dr.text((10,951),'Cyan=source exterior support-constrained sections; amber=inferred continuity/fold bands. Overlay is projected real Blender curves, not depth-tested ink.',font=small,fill='white')
    dr.text((10,971),'v06 global height remains fixed. Camera/head-pose and source section-height residuals remain visible. Neck chart, garment/UV and final rig are not approved.',font=small,fill='white')
    path=C/f'actual05-{view}-source-gray-guides.png';board.save(path);rows.append(dict(view=view,source=s['source'],source_sha256=s['source_sha256'],crop=crop,actual=r['path'],actual_sha256=r['sha256'],board=str(path),board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),guide_data_sha256=guides['data_sha256'],registration='No image warp. Source and actual887² shown at original pixels; source-wide uniform metric and physical camera in render records.'))
(C/'actual-source-comparison-05.json').write_text(json.dumps(dict(boards=rows,status='First actual source-bound surface hypothesis. No source ART or motion approval; baseline samecamera and fuller view suite remain pending.'),indent=2)+'\n',encoding='utf-8');print('SOURCE_LOWVIEW_BOARDS_05_DONE',len(rows),flush=True)
