"""Original-aspect source comparisons and actual-cage projection diagnostics."""
from pathlib import Path
import json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;B=P.parent;A=P/'actual-four'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v06=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png')
low=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-low-view-axilla-reaffirmed-20261103.png')
assert sha(v06)=='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1'
source=Image.open(v06).convert('RGB');lf=Image.open(low).convert('RGB');records=json.loads((A/'render-records.json').read_text());assert len(records)==4
try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20)
except OSError:font=ImageFont.load_default()
scale=1.0022371364653244;shift=4.890380313199103;srcstep=.00185
def sourcecrop(center):
    top=(1.785-1.475)/srcstep*scale+shift;side=.4/srcstep*scale
    box=[center-side/2,top,center+side/2,top+side]
    return source.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC),box
out=[]
for row in records:
    view=row['view'];size=row['camera']['resolution'][0];candidate=Image.open(A/Path(row['path']).name).convert('RGB');assert sha(A/Path(row['path']).name)==row['sha256']
    fixture=None;crop=None;limit=''
    if view in ['front','profile']:
        oldfolder=B/'posed-target/actual-01';old=json.loads((oldfolder/('gray-'+view+'-pre-render.json')).read_text());baseline=Image.open(oldfolder/('gray-'+view+'.png')).convert('RGB')
        center=239 if view=='front' else 568+(-.035+.018)/srcstep*scale
        src,crop=sourcecrop(center);labels=['v06 / uniform registered crop','Rejected01 context','Unselected06 diagnostic']
        limit='Profile85degree model versus illustrated nearprofile; residual camera/pose uncertainty retained.' if view=='profile' else 'Frozen wholeheight uniform registration; no torso-only normalization.'
    elif view=='F2lowoblique':
        oldfolder=B/'posed-target/actual-05';old=json.loads((oldfolder/'gray-F2oblique-pre-render.json').read_text());baseline=Image.open(oldfolder/'gray-F2oblique.png').convert('RGB');src=lf.crop((887,0,1774,887));crop=[887,0,1774,887];labels=['Reaffirmed F2 / unchanged aspect','Rejected05 context','Unselected06 diagnostic'];limit='Same estimated40/-8 camera; arm/cloth/source metric uncertainty remains.'
    else:
        src,crop=sourcecrop(935);baseline=None;old=None;labels=['v06 BACK CONTEXT / hair occlusion','Unselected06 rear140/-10'];limit='Back source is context only, not corresponding rear-oblique calibration; covered posterior wall inferred.'
    images=[src,baseline,candidate] if baseline is not None else [src,candidate]
    w=size;h=size+34;board=Image.new('RGB',(w*len(images),h),'#202632');draw=ImageDraw.Draw(board)
    for i,(im,label) in enumerate(zip(images,labels)):
        assert im.size==(w,w);board.paste(im,(i*w,34));draw.text((i*w+8,7),label,fill='white',font=font)
    path=P/('source-'+view+'.png');board.save(path)
    if old:
        assert row['camera']==old['camera'],('Fixture camera differs',view)
        active=lambda record:[x for x in record['actual_all_light_flags_before_render'] if not x['hidden']]
        newl,oldl=active(row),active(old)
        fixture=dict(camera_bitexact=True,color_management_exact=row['color_management']==old['color_management'],
            actual_light_energy_size_shadow_exact=all(a[k]==b[k] for a,b in zip(newl,oldl) for k in ['energy','size','use_shadow']),
            actual_light_matrix_max=float(max(np.max(np.abs(np.array(a['matrix'])-np.array(b['matrix']))) for a,b in zip(newl,oldl))))
    out.append(dict(view=view,path=str(path),sha256=sha(path),source_crop=crop,source_image_resized_uniformly=True,fixture=fixture,limits=limit))

# X-ray overlay of ACTUAL new control faces, projected by the actual camera.
data=np.load(P/'prototype06.npz');sizes=data['polygon_sizes'];off=np.r_[0,np.cumsum(sizes)];faces=[data['loop_vertices'][off[i]:off[i+1]] for i in range(len(sizes))];newstart=len(data['kept_original_faces'])
for view in ['front','F2lowoblique']:
    row=next(r for r in records if r['view']==view);cam=row['camera'];mat=np.linalg.inv(np.array(cam['matrix']));world=data['world'];local=world@mat[:3,:3].T+mat[:3,3];width,height=cam['resolution'];pixels=height/cam['ortho_scale'];xy=np.c_[width/2+local[:,0]*pixels,height/2-local[:,1]*pixels]
    im=Image.open(A/Path(row['path']).name).convert('RGB');draw=ImageDraw.Draw(im)
    for fi,f in enumerate(faces):
        if not any(data['regions'][f]) or world[f,2].mean()<1.12 or world[f,2].mean()>1.425:continue
        color='#35f494' if fi>=newstart else '#707c87';line=2 if fi>=newstart else 1
        for a,b in zip(f,np.roll(f,-1)):
            if -local[a,2]>.1 and -local[b,2]>.1:draw.line([tuple(xy[a]),tuple(xy[b])],fill=color,width=line)
    draw.rectangle((0,0,width,30),fill='#202632');draw.text((8,4),'ACTUAL control edges: green new quads / X-ray',fill='white',font=font);im.save(P/('cage-'+view+'.png'))
(P/'review-records.json').write_text(json.dumps(dict(prototype_sha256=sha(P/'prototype06.npz'),images=out,static=True,selected=False,migration='UNVERIFIED',source_binding='FAIL',extra_gpu_frames=0),indent=2)+'\n',encoding='utf-8')
print('PATCH06_SOURCE_REVIEW_COMPOSED',len(out),flush=True)
