"""Catalogue all original panels and initial rig hypotheses; never warp source art."""
from pathlib import Path
import json, hashlib
from PIL import Image
P=Path(__file__).resolve().parent; M=P.parents[2]
source=M/'references/mia-expression-style-confirmed-20261031.png'
im=Image.open(source); assert im.size==(1536,1024)
rows=[
 ('neutral_observe','피곤한 기본 관찰',{},[0,0,0],[0,0],'Closed neutral mouth; retain source fatigue.'),
 ('near_closed_weary','눈을 거의 감은 피로',{'EYE_Close':.88,'BRW_Sorrow':.12,'MTH_Sorrow':.08},[0,0,3],[0,0],'Keep a narrow ocular sliver; source02 is not full blink.'),
 ('skeptical_question','의아한 질문',{'BRW_Sorrow':.18,'EYE_Angry':.08,'MTH_A':.12},[0,-2,-3],[0,0],'Small parted lips and unequal-looking lids; head tilt is separate.'),
 ('aside_attention','옆쪽을 주시',{'MTH_Down':.1},[0,18,0],[-8,0],'Gaze/head turn, not a different face mesh.'),
 ('downward_irritated','아래를 보는 불만',{'BRW_Angry':.35,'EYE_Close':.12,'MTH_Sorrow':.18},[7,0,-2],[0,-4],'Inner brow and lip corners carry tension; do not shrink cheeks.'),
 ('upward_uncertain','올려다보는 망설임',{'BRW_Sorrow':.35,'EYE_Surprised':.08,'MTH_A':.13},[-7,-18,0],[6,3],'Pose/gaze and small opening are independent.'),
 ('thinking','생각하는 표정',{'BRW_Angry':.18,'EYE_Close':.06,'MTH_Sorrow':.2,'MTH_U':.07},[3,0,-2],[0,-2],'Source chin-hand gesture requires a separate body pose; not facial geometry.'),
 ('closed_smirk','입을 다문 미소',{'MTH_Fun':.35,'MTH_Up':.12},[0,0,-2],[0,0],'Closed asymmetric smile needs actual lip-seal review.'),
 ('concerned','걱정스러운 눈썹',{'BRW_Sorrow':.4,'EYE_Surprised':.18,'MTH_Sorrow':.1},[0,0,2],[0,0],'Raised inner brow with restrained mouth.'),
 ('toothy_grin','치아가 드러난 장난스러운 웃음',{'MTH_Fun':.9,'MTH_Joy':.15,'BRW_Fun':.2,'EYE_Angry':.15},[0,0,-4],[0,0],'Wide oblique tooth band; generic donor laugh/fangs may need actual correction.'),
 ('flustered_down','시선을 내린 당황',{'BRW_Sorrow':.25,'EYE_Close':.15,'MTH_Down':.08},[6,0,-2],[0,-5],'Blush impression also comes from paint; do not fake gaze with eye aperture.'),
 ('surprised','놀라서 눈을 크게 뜸',{'EYE_Surprised':.8,'BRW_Surprised':.6,'MTH_A':.28},[-2,0,0],[0,0],'Open eye/cap/lash and small mouth need combination testing.'),
 ('sulky','무뚝뚝한 불만',{'BRW_Angry':.12,'MTH_Down':.12,'EYE_Sorrow':.08},[0,0,0],[0,0],'Subtle variation, not a large angry caricature.'),
 ('weary_speaking','피곤하게 말함',{'EYE_Close':.08,'BRW_Sorrow':.2,'MTH_A':.18,'MTH_O':.08},[1,0,-2],[0,0],'Small relaxed mouth opening with visible cavity.'),
 ('stern','가라앉은 단호함',{'BRW_Angry':.3,'EYE_Angry':.15,'MTH_Down':.14},[2,0,0],[0,0],'Retain lower-rim volume and broad rounded-parallelogram opening.'),
 ('gentle_smile','조용한 미소',{'MTH_Fun':.22,'MTH_Up':.1,'EYE_Joy':.08},[0,0,-2],[0,0],'Small corners/cheek response, not a separate alternate face.')]
out=[];(P/'source-panels').mkdir(exist_ok=True)
for i,(name,label,keys,head,gaze,note) in enumerate(rows,1):
 x=((i-1)%4)*384;y=((i-1)//4)*256;crop=[x,y,x+384,y+256]
 f=P/'source-panels'/f'{i:02}-{name}.png';im.crop(crop).save(f)
 out.append(dict(panel=i,id=name,label=label,source_crop=crop,source_panel=str(f.relative_to(P)),
   panel_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),initial_key_recipe=keys,
   estimated_head_delta_xyz_deg=head,estimated_gaze_xy_deg=gaze,observation=note,
   acceptance='UNVERIFIED initial rig hypothesis, not a calibrated drawing measurement'))
(P/'expression-intents.json').write_text(json.dumps(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    source_aspect_unchanged=True,panels=out),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('EXPRESSION_INTENTS_16_CREATED')
