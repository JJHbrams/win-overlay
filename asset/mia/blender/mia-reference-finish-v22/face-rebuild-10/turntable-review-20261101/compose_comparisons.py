import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--body',action='store_true');args=ap.parse_args();OUT=Path(args.output)
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay')
PKG=ROOT/'asset/mia/blender/mia-reference-finish-v22/face-rebuild-10/selected-v27/reference-review.json'
pkg=json.loads(PKG.read_text());rows={r['id']:r for r in pkg['views']}
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)
ink='#172633';bg='#eef2f6';cyan='#13869d';orange='#bb6824';red='#b44b65';green='#3b8864'
resolve=lambda d:(PKG.parent/d['path']).resolve()

def transform(im,reg,size):
    th=math.radians(reg['rotation_degrees']);sc=reg['uniform_scale'];A=sc*np.array([[math.cos(th),-math.sin(th)],[math.sin(th),math.cos(th)]]);inv=np.linalg.inv(A);t=-inv@np.array(reg['translation_xy'])
    q=im.convert('RGBA').transform(size,Image.Transform.AFFINE,tuple(inv[0])+tuple(t[:1])+tuple(inv[1])+tuple(t[1:]),resample=Image.Resampling.BICUBIC)
    out=Image.new('RGBA',size,bg);out.alpha_composite(q);return out.convert('RGB')

def line(draw,y,w,color):
    for x in range(0,w,14):draw.line((x,int(y),x+7,int(y)),fill=color,width=1)

titles={'front':'정면','profile':'측면에 가까운 뷰','left_oblique':'사선 · 왼쪽','right_oblique':'반대쪽 미묘한 각도'}
notes={'front':['yaw 0° · roll -6.6°','별도 IPD 비교판에서 눈선–턱 길이를 다시 확인'],
       'profile':['yaw 80° · 측면 원본 얼굴 영역 80×72 px','원화 yaw 추정 70–90° · 가려진 콧대/깊이 정량 불가'],
       'left_oblique':['yaw 25° · elevation +2° · roll -15°','원화는 옆을 보는 시선 · 중립 모델과 시선 차이 있음'],
       'right_oblique':['yaw -10° · elevation -3° · roll -15°','원화는 올려본 눈/열린 입 · 반대쪽 45° 원화가 아님']}
board=Image.new('RGB',(1920,1530),'#f7f9fb');d=ImageDraw.Draw(board)
d.text((24,12),'원화 ↔ 현재 모델 · 정면 / 측면 / 양쪽 사선',font=font(32),fill=ink)
d.text((24,59),'같은 저장 모델 e9c86541 · 정투영 · 기존 균일 SRT 유지 · 눈–턱 기준 배율이므로 얼굴 높이 자체는 별도 검증',font=font(21),fill=ink)
for j,name in enumerate(['front','profile','left_oblique','right_oblique']):
    r=rows[name];x=(j%2)*960;y=110+(j//2)*700
    d.text((x+16,y),titles[name],font=font(27),fill=ink)
    for i,(role,reg) in enumerate([('reference','reference_registration'),('candidate_render','candidate_registration')]):
        pane=transform(Image.open(resolve(r[role])),r[reg],(640,640)).resize((480,480),Image.Resampling.LANCZOS)
        board.paste(pane,(x+i*480,y+76));d.text((x+i*480+16,y+42),'기준 원화' if i==0 else '현재 모델',font=font(22),fill=ink)
    for k,n in enumerate(notes[name]):d.text((x+16,y+570+k*30),n,font=font(20),fill=ink)
    d.line((x,y+680,x+955,y+680),fill='#bac7d4',width=1)
board.save(OUT/'face-multiview-comparison.png')

marks={'reference':{'eyes':[[450,324],[582,310]],'mouth':[518,412],'chin':[519,463],'jaw':[[457,430],[586,416]]},
       'candidate_render':{'eyes':[[386,541],[617,515]],'mouth':[520,682],'chin':[528,772],'jaw':[[408,726],[637,700]]}}
front=Image.new('RGB',(1160,990),'#f7f9fb');d=ImageDraw.Draw(front)
d.text((20,12),'정면 비율 비교 · 눈 간격으로 정규화',font=font(31),fill=ink)
d.text((20,59),'눈 중심선과 간격만 맞춤 · 턱과 입 위치는 맞추지 않음 · 비균일 늘이기 없음',font=font(22),fill=ink)
measure={}
for i,role in enumerate(['reference','candidate_render']):
    m=marks[role];eyes=np.array(m['eyes'],float);delta=eyes[1]-eyes[0];ipd=float(np.linalg.norm(delta));mid=eyes.mean(0);theta=-math.atan2(delta[1],delta[0]);R=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    A=240/ipd*R;t=np.array([280,185])-A@mid;reg={'uniform_scale':240/ipd,'rotation_degrees':math.degrees(theta),'translation_xy':t.tolist()}
    pane=transform(Image.open(resolve(rows['front'][role])),reg,(560,580));pdraw=ImageDraw.Draw(pane)
    P=lambda p:A@np.array(p)+t
    for e in eyes:
        xx,yy=P(e);pdraw.ellipse((xx-5,yy-5,xx+5,yy+5),outline=cyan,width=2)
    for key,color in [('mouth',red),('chin',orange)]:
        xx,yy=P(m[key]);line(pdraw,yy,560,color);pdraw.ellipse((xx-4,yy-4,xx+4,yy+4),fill=color)
    line(pdraw,185,560,cyan);pdraw.line((280,110,280,560),fill='#8ba0b1',width=1)
    ja,jb=P(m['jaw'][0]),P(m['jaw'][1]);pdraw.line(tuple(ja)+tuple(jb),fill=green,width=3)
    front.paste(pane,(20+i*580,145));d.text((28+i*580,105),'기준 원화' if i==0 else '현재 모델',font=font(25),fill=ink)
    n=np.array([-delta[1],delta[0]])/ipd
    measure[role]={'raw_landmarks':m,'ipd_px':ipd,'eye_to_chin_over_ipd':float(np.dot(np.array(m['chin'])-mid,n)/ipd),'eye_to_mouth_over_ipd':float(np.dot(np.array(m['mouth'])-mid,n)/ipd),'mouth_to_chin_over_ipd':float(np.dot(np.array(m['chin'])-m['mouth'],n)/ipd),'jaw_section_width_over_ipd':float(np.linalg.norm(np.array(m['jaw'][1])-m['jaw'][0])/ipd),'display_uniform_srt':reg}
labels=[('눈선 → 턱 / 눈 간격','eye_to_chin_over_ipd'),('눈선 → 입 / 눈 간격','eye_to_mouth_over_ipd'),('입 → 턱 / 눈 간격','mouth_to_chin_over_ipd'),('눈선 아래 0.80 눈 간격의 하안면 폭','jaw_section_width_over_ipd')]
d.text((710,726),'원화',font=font(18),fill=ink);d.text((960,726),'현재',font=font(18),fill=ink)
for j,(title,key) in enumerate(labels):
    yy=752+j*37;d.text((24,yy),title,font=font(21),fill=ink)
    for i,role in enumerate(['reference','candidate_render']):d.text((710+i*250,yy),f'{measure[role][key]:.2f}',font=font(24),fill=ink)
d.text((24,918),'수동 홍채 중심·윤곽 추정 ±3px + 시선/고개 각도 오차. 최대 광대 폭을 잰 값이 아님.',font=font(20),fill=ink)
d.text((24,951),'눈선–턱: 현재 약 3.7% 짧게 투영됨. 작은 차이만으로 3D 수정량을 확정하지 않음.',font=font(20),fill=ink)
front.save(OUT/'face-front-ipd-comparison.png')
(OUT/'front-ratio-measurements.json').write_text(json.dumps({'native_sha256':pkg['candidate_native']['sha256'],'method':'Manual visible iris center proxies in original raw source/current pixels; eye-line de-roll; uniform IPD scale and translation only, chin not fitted.','uncertainty':'Approx +/-3px anchors plus drawing pose/gaze. Lower-jaw sample is one section at0.80IPD below eye line, not maximum cheek width.','measurements':measure},indent=2),encoding='utf-8')

if args.body:
    ref=Image.open(ROOT/'asset/mia/references/body-foundation/v06/mia-body-turnaround-v06.png')
    body=Image.new('RGB',(1840,2270),'#f7f9fb');d=ImageDraw.Draw(body)
    d.text((24,10),'본체 비율 비교 · Body Foundation v06 원화 후보 / 현재 모델',font=font(29),fill=ink)
    d.text((24,56),'머리카락 최상단–발바닥 높이로 균일 표시 · 의상/포즈 차이 포함 · 전체 높이 자체의 검증 아님',font=font(21),fill=ink)
    body_meta=[]
    for j,(name,crop,index) in enumerate([('정면',(30,50,432,952),0),('측면',(472,50,710,952),18),('사선',(1148,50,1482,952),9),('후면',(730,50,1118,952),36)]):
        x=(j%2)*920;y=110+(j//2)*1070;d.text((x+16,y),name,font=font(27),fill=ink)
        raw=Image.open(OUT/'body'/f'{index:03}.png').convert('RGBA');bb=raw.getchannel('A').getbbox();raw=raw.crop(bb)
        for col,im in enumerate([ref.crop(crop),raw]):
            scale=900/im.height;new=im.resize((round(im.width*scale),900),Image.Resampling.LANCZOS)
            pane=Image.new('RGBA',(460,920),bg);pane.alpha_composite(new.convert('RGBA'),((460-new.width)//2,10));pd=ImageDraw.Draw(pane)
            for h in [0,.25,.5,.75,1]:line(pd,10+900*h,460,'#8ba0b1')
            body.paste(pane.convert('RGB'),(x+col*460,y+80));d.text((x+col*460+16,y+44),'v06 원화 후보' if col==0 else '현재 본체 · 의상 미적용',font=font(20),fill=ink)
        body_meta.append({'view':name,'reference_crop':crop,'model_frame':index,'model_alpha_bbox':bb})
        d.text((x+16,y+1015),'가이드: 표시 높이 0 / 25 / 50 / 75 / 100% · 신체 부위 기준선 아님',font=font(18),fill=ink)
    body.save(OUT/'body-multiview-comparison.png');(OUT/'body-comparison-registration.json').write_text(json.dumps({'method':'Uniform display height from source crop and current alpha bounds; no anisotropic resizing. Includes hair height and differing pose/underwear, not body-height validation.','views':body_meta},indent=2),encoding='utf-8')
print('COMPARISONS_DONE')
