"""Clearly labelled CPU wire/whole-scene first-hit diagram, not shaded artwork."""
from pathlib import Path
import json,numpy as np,sys
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;V=sys.argv[1] if len(sys.argv)>1 else 'B';assert V in ('B','C');r=json.loads((P/('CPU-guard-'+V+'.json')).read_text());inp=json.loads((P/'current-inputs.json').read_text());cam=np.array(inp['camera']['matrix']);scale=inp['camera']['ortho_scale'];a=np.load(P/('CPU-wire-'+V+'.npz'))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',13)
def proj(q):
    rel=q-cam[:3,3];return np.stack((.5+rel@cam[:3,0]/scale,.5-rel@cam[:3,1]/scale),axis=-1)*512
board=Image.new('RGB',(1048,830),'#17232d');draw=ImageDraw.Draw(board)
source=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-face-reaffirmed-20261031.png')
crop=Image.open(source).convert('RGB').crop((340,200,680,370));crop=crop.resize((510,255),Image.Resampling.NEAREST);board.paste(crop,(12,35))
draw.text((12,8),'SOURCE portrait crop340,200..680,370; uniform1.5x; hidden ends uncertain',font=font,fill='white')
draw.text((540,60),'CPU actual evaluated wire + whole-scene rays',font=font,fill='white')
draw.text((540,92),'Green: real gap; red: Main foreground.',font=font,fill='#75e688')
draw.text((540,117),'Blue: root lining; orange: other opaque actor.',font=small,fill='#acd9ed')
draw.text((540,142),'All render-visible mesh owners tested.',font=small,fill='white')
draw.text((540,167),'Only provably pure Transparent faces excluded.',font=small,fill='white')
draw.text((540,192),'No shaded candidate render is shown here.',font=small,fill='#ffdf85')
for col,(label,key,rows) in enumerate([('BASELINE','before',r['real_hair_gap_visibility_before']),('CANDIDATE '+V,'after',r['real_hair_gap_visibility_after'])]):
    panel=Image.new('RGB',(512,480),'#eef2f4');d=ImageDraw.Draw(panel)
    for tri in proj(a[key]):d.line([tuple(p) for p in tri]+[tuple(tri[0])],fill='#b5bec5',width=1)
    for side in rows:
        pts=proj(np.array([s['target_world'] for s in side['samples']]))
        d.line([tuple(p) for p in pts],fill='#283238',width=2)
        for xy,s in zip(pts,side['samples']):
            owner=s['first_hit_owner'];color=('#23934d' if owner is None else '#cb4150' if owner=='MIA_V17_PIXAL_DetailedHair' else '#2e81c4' if 'RootLining' in owner else '#dc8d20')
            x,y=xy;d.ellipse((x-3,y-3,x+3,y+3),fill=color)
    count=sum(s['unoccluded'] for s in rows);total=sum(s['observed_samples'] for s in rows)
    d.text((8,8),label+f' | observed brow samples clear {count}/{total}',font=font,fill='#17232d')
    board.paste(panel,(12+col*524,320))
draw.text((12,806),'Geometry/first-hit diagnostic only. Source width/angle, natural fringe flow and surface appearance await actual hairOFF/ON pairs.',font=small,fill='white')
board.save(P/('CPU-whole-scene-firsthit-'+V+'.png'))
print('CPU first-hit diagram written; source and panel aspect unchanged')
