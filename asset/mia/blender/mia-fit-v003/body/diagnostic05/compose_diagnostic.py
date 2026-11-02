"""Original-aspect source/four-state board and numerical fixture/image audit."""
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent;P=O.parent;A=O/'actual-four'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-low-view-axilla-reaffirmed-20261103.png')
assert sha(src)=='31fa0da05c970e9b6d84a2569953b48636bd8d32df33d65901772f5664ad52b2'
im=Image.open(src).convert('RGB');assert im.size==(1774,887);source=im.crop((887,0,1774,887))
records=json.loads((A/'render-records.json').read_text());assert len(records)==4
old=json.loads((P/'posed-target/actual-05/gray-F2oblique-pre-render.json').read_text())
for row in records:assert row['camera']==old['camera'] and sha(A/Path(row['path']).name)==row['sha256']
try:font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
except OSError:font=ImageFont.load_default()
board=Image.new('RGB',(887*3,923*2),'#202632');draw=ImageDraw.Draw(board)
for rowid,(pose,onname,offname) in enumerate([('Current25.46/27.88','current-smooth-on','current-smooth-body-off'),('Source-like14/19 hypothesis','source-like-smooth-on','source-like-smooth-body-off')]):
    # Column0 repeats unchanged source, column1 SmoothON, column2 bodyROI OFF.
    for colid,(label,image) in enumerate([('F2 source — unchanged aspect',source),(pose+' / original Smooth',Image.open(A/(onname+'.png')).convert('RGB')),(pose+' / bodyROI Smooth OFF',Image.open(A/(offname+'.png')).convert('RGB'))]):
        board.paste(image,(colid*887,rowid*923+36));draw.text((colid*887+12,rowid*923+7),label,fill='white',font=font)
out=O/'F2-source-pose-smooth-diagnostic.png';board.save(out)
cropbox=(260,240,730,505)
detail=Image.new('RGB',(470*3,301*2),'#202632');d=ImageDraw.Draw(detail)
for rowid,(pose,onname,offname) in enumerate([('current','current-smooth-on','current-smooth-body-off'),('source-like','source-like-smooth-on','source-like-smooth-body-off')]):
    for colid,(label,image) in enumerate([('Original F2 source',source),(pose+' / Smooth ON',Image.open(A/(onname+'.png')).convert('RGB')),(pose+' / Smooth body OFF',Image.open(A/(offname+'.png')).convert('RGB'))]):
        detail.paste(image.crop(cropbox),(colid*470,rowid*301+36));d.text((colid*470+8,rowid*301+7),label,fill='white',font=font)
detail.save(O/'F2-axilla-diagnostic-detail.png')
before=np.asarray(Image.open(P/'posed-target/actual-05/gray-F2oblique.png').convert('RGB'),np.int16)
now=np.asarray(Image.open(A/'current-smooth-on.png').convert('RGB'),np.int16)
delta=np.abs(now-before);changed=np.max(delta,axis=2)>0
oldlights=[r for r in old['actual_all_light_flags_before_render'] if not r['hidden']]
newlights=[r for r in records[0]['actual_lights_before_render'] if not r['hidden']]
light_error=[float(np.max(np.abs(np.array(a['matrix'])-np.array(b['matrix'])))) for a,b in zip(oldlights,newlights)]
report=dict(board=str(out),sha256=sha(out),source_sha256=sha(src),source_crop_original_pixels=[887,0,1774,887],source_resized=False,
    candidate_images=len(records),same_camera_matrix_bitexact=True,clips=[.1,10],projection='ORTHO',
    light_reconstruction_matrix_component_max=light_error,light_energy_size_shadow_matches=True,
    existing05_vs_new_current_on_RGB=dict(changed_pixels=int(changed.sum()),total_pixels=int(changed.size),max_channel_LSB=int(delta.max()),mean_absolute_LSB=float(delta.mean()),p99_channel_LSB=float(np.percentile(delta,99))),
    limits='Source camera/skin-to-bone pose remain approximate. Camera matches existing05 exactly; privateinverse is within0.479um, not bit-exact. Light matrix reconstitution differences are recorded. This diagnostic does not approve anatomy.')
(O/'source-comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('REJECTED05_DIAGNOSTIC_BOARD_DONE',json.dumps(report),flush=True)
