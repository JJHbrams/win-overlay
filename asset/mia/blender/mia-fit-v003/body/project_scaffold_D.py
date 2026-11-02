"""CPU project actual Blender readback curves over prior actual C frames.
Explicit X-ray diagram; this is not a new rendered native-view claim.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'scaffold-D';actual=json.loads((O/'guide-actual-Blender.json').read_text());data=json.loads((O/'guide-data.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12);out=[]
records=[('gray',r) for r in json.loads((P/'renders-form-C-gray/render-records.json').read_text())]+[('source',r) for r in json.loads((P/'renders-form-C-source/render-records.json').read_text())]
for mode,r in records:
    cam=r['camera'];w,h=cam['resolution'];matrix=np.linalg.inv(np.asarray(cam['matrix']));scale=cam['ortho_scale'];view=r['view'];bg=Image.open(r['path']).convert('RGBA');im=Image.new('RGB',(w*2,h+90),'#273039');im.paste(bg,(0,40),bg);im.paste(bg,(w,40),bg);draw=ImageDraw.Draw(im)
    def project(points,offset):
        p=np.asarray(points);q=np.column_stack([p,np.ones(len(p))])@matrix.T;return [(float(w/2+x*h/scale+offset),float(h/2-y*h/scale+40)) for x,y in q[:,:2]]
    def line(points,color,offset,dashed=False):
        pts=project(points,offset)
        if dashed:
            for j in range(0,len(pts)-1,4):draw.line(pts[j:min(j+3,len(pts))],fill=color,width=1)
        else:draw.line(pts,fill=color,width=1)
    for c in actual['curves']:
        name=c['name'];kind=c['kind'];col=data['colors'][kind]
        sections=('.section.' in name or '.meridian.' in name)
        if sections:
            if '.meridian.' not in name or name.endswith(('.00','.03','.06','.09')):line(c['points'],col,0,dashed=kind!='garment')
        else:line(c['points'],col,w,dashed=kind in ['inferred','occluded'])
    for m in actual['meshes']:
        if 'fan_web' not in m['name'] and 'fold_bridge' not in m['name']:continue
        for face in m['faces']:
            poly=[m['vertices'][j] for j in face];line(poly+[poly[0]],'#f46bcb' if 'fan_web' in m['name'] else '#acb7c5',w,True)
    draw.rectangle((0,0,w*2,39),fill='#273039');draw.text((8,7),f'{mode} {view} / CORE + CLOTH-BOUND SECTIONS',font=font,fill='white');draw.text((w+8,7),'PECTORAL / AXILLARY / SHOULDER BRANCH WEB',font=font,fill='white');draw.text((8,h+44),'Actual Blender curves read back; CPU X-ray projection over existing actual C image. Not a new GPU render.',font=small,fill='white');draw.text((8,h+63),'Blue: inferred core | gold: cloth-envelope interpolation | pink: inferred fan/root | gray: hidden posterior arc.',font=small,fill='white');file=O/(f'projected-{mode}-{view}.png');im.save(file);out.append(dict(mode=mode,view=view,path=str(file),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),underlying_actual_image=r['path'],underlying_actual_image_sha256=hashlib.sha256(Path(r['path']).read_bytes()).hexdigest(),actual_camera=cam,method='CPU X-ray projection of actual Blender curve/readback geometry; no visibility/depth claim'))
(O/'projection-records.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('ACTUAL_GUIDE_PROJECTION_BOARDS_DONE',len(out),flush=True)
# Same actual3D readback projected into all source panels. These are
# provisional camera assumptions, explicitly separate from observed traces.
source=Image.open(data['reference']).convert('RGB');draw=ImageDraw.Draw(source);mpp=data['height_registration']['metres_per_source_pixel'];zcrown=data['height_registration']['crown_z'];centers=[239,568,935,1317]
for panel,(center,yaw) in enumerate(zip(centers,[0,90,180,30])):
    r=np.deg2rad(yaw)
    for c in actual['curves']:
        if '.meridian.' in c['name'] and not c['name'].endswith(('.00','.03','.06','.09')):continue
        pts=np.asarray(c['points']);xx=center+(np.cos(r)*pts[:,0]+np.sin(r)*(pts[:,1]+.018))/mpp;yy=54+(zcrown-pts[:,2])/mpp;q=list(zip(xx.tolist(),yy.tolist()));col=data['colors'][c['kind']]
        for j in range(0,len(q)-1,4):draw.line(q[j:min(j+3,len(q))],fill=col,width=1)
draw.rectangle((0,0,1536,34),fill='#273039');draw.text((10,7),'ACTUAL BLENDER3D SCAFFOLD -> SOURCE | provisional cameras; all wire arcs inferred between observed bounds',font=font,fill='white');source.save(O/'actual3D-projected-on-source.png')
