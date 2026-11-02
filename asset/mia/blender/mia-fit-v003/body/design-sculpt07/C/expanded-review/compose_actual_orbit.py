"""Actual frame GIF/contact sheets; no generated interpolation or motion."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;C=P.parent;records=json.loads((P/'render-records.json').read_text(encoding='utf-8'));sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest();assert len(records)==15
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
for r in records:assert sha(r['path'])==r['sha256']
orbit=[r for r in records if r['view'].startswith('orbit-')];assert len(orbit)==12
frames=[];contact=Image.new('RGB',(384*4,414*3),'#202632');draw=ImageDraw.Draw(contact)
for i,r in enumerate(orbit):
    im=Image.open(r['path']).convert('RGB');assert im.size==(384,384);frame=Image.new('RGB',(384,414),'#202632');frame.paste(im,(0,30));ImageDraw.Draw(frame).text((7,7),'ACTUAL C yaw%03d pitch+8 / STATIC'%r['camera']['yaw'],font=font,fill='white');frames.append(frame);contact.paste(frame,((i%4)*384,(i//4)*414))
durations=[330,330,340]*4
frames[0].save(P/'actual-orbit-4sec.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2,optimize=False);contact.save(P/'actual-orbit-contact-sheet.png')
critical=[r for r in records if not r['view'].startswith('orbit-')];board=Image.new('RGB',(640*3,690),'#202632');draw=ImageDraw.Draw(board)
for i,r in enumerate(critical):
    im=Image.open(r['path']).convert('RGB');board.paste(im,(i*640,30));draw.text((i*640+8,7),'ACTUAL C '+r['view']+' / held geometry',font=font,fill='white')
draw.text((8,672),'Supplementary view inspection; body/axilla/source fit still open; private context seams UNVERIFIED.',font=small,fill='white');board.save(P/'actual-critical-three.png')
# Same frozen wholeheight source registration, original aspect. Back source is
# covered and cannot calibrate the hidden posterior wall.
params=json.loads((C/'parameters.json').read_text(encoding='utf-8'));source=Image.open(params['sources']['v06_path']).convert('RGB');scale=1.0022371364653244;shift=4.890380313199103;step=.00185;top=(1.785-1.485)/step*scale+shift;side=.4/step*scale;box=[935-side/2,top,935+side/2,top+side];src=source.transform((640,640),Image.Transform.EXTENT,box,resample=Image.Resampling.BICUBIC);back=Image.open(P/'back.png').convert('RGB');paired=Image.new('RGB',(1280,700),'#202632');paired.paste(src,(0,30));paired.paste(back,(640,30));draw=ImageDraw.Draw(paired);draw.text((8,7),'v06 BACK / outer contour, hair covered',font=font,fill='white');draw.text((648,7),'ACTUAL C back180/0 / hairOFF',font=font,fill='white');draw.text((8,674),'Observable outer contour only; hidden back wall inferred. Not a calibrated naked-back ART pass.',font=small,fill='white');paired.save(P/'source-back-context.png')
gif=Image.open(P/'actual-orbit-4sec.gif');actual_durations=[]
for i in range(gif.n_frames):gif.seek(i);actual_durations.append(gif.info['duration'])
assert gif.n_frames==12 and sum(actual_durations)==4000
out=dict(actual_frame_count=15,orbit_actual_frames=12,gif_frame_durations_ms=actual_durations,gif_duration_ms=sum(actual_durations),actual_no_interpolation=True,static_geometry_held=True,not_final_30fps_animation=True,source_back_crop=box,source_back_limit='Outer observable contour only; hair-covered posterior wall inferred; no naked-back calibration.',outputs=[dict(path=f.name,sha256=sha(f)) for f in [P/'actual-orbit-4sec.gif',P/'actual-orbit-contact-sheet.png',P/'actual-critical-three.png',P/'source-back-context.png']]);(P/'composition-records.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print('C_ACTUAL_ORBIT_GIF_COMPOSED',flush=True)
