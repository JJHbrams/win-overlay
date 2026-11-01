from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json,hashlib
P=Path(__file__).parent;O=P/'source-soft-L';font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
def art(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
records={r:json.loads((P/'renders'/r/'owner-clay-orbit/render-records.json').read_text()) for r in ['I-true-core','L-core-plus-soft']}
frames={r:[] for r in records};paired=[]
for i in range(36):
 key='orbit_'+str(i).zfill(3);pair=Image.new('RGB',(1024,558),(36,36,36));pd=ImageDraw.Draw(pair)
 for j,role in enumerate(records):
  record=records[role]['records'][key];p=Path(record['path']);assert art(p)['sha256']==record['sha256'];tile=Image.open(p).convert('RGBA');bg=Image.new('RGBA',tile.size,(36,36,36,255));bg.alpha_composite(tile);im=bg.convert('RGB');single=Image.new('RGB',(512,558),(36,36,36));single.paste(im,(0,42));d=ImageDraw.Draw(single);label='ACTUAL true core' if j==0 else 'ACTUAL core + breast tissue';d.text((8,5),label,font=font,fill='white');d.text((8,24),f"Yaw {record['camera']['yaw']:.0f} / pitch {record['camera']['pitch']:.1f} | ORTHO",font=font,fill='white');frames[role].append(single);pair.paste(single,(j*512,0))
 paired.append(pair)
manifest={}
for role,items in list(frames.items())+[('L-core-versus-soft',paired)]:
 path=O/(role+'-orbit.gif');items[0].save(path,save_all=True,append_images=items[1:],duration=140,loop=0,optimize=False,disposal=2);manifest[role]=art(path)
sheet=Image.new('RGB',(1536,1116),(36,36,36))
for col,i in enumerate([0,6,12]):sheet.paste(paired[i].resize((768,419),Image.Resampling.LANCZOS),(col%2*768,col//2*419))
# Separate six equally spaced pairs at reduced uniform scale, all actualframes.
sheet=Image.new('RGB',(1536,558),(36,36,36))
for j,i in enumerate([0,6,12,18,24,30]):sheet.paste(paired[i].resize((512,279),Image.Resampling.LANCZOS),((j%3)*512,(j//3)*279))
sheet.save(O/'orbit-contact-sheet.png');manifest['contact_sheet']=art(O/'orbit-contact-sheet.png');manifest['frame_records']={role:art(P/'renders'/role/'owner-clay-orbit/render-records.json') for role in records};(O/'orbit-artifacts.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print('L_ORBIT_GIFS_ASSEMBLED')
