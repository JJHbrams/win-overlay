"""Record generated studies without replacing the selected v06 source authority."""
from pathlib import Path
import json,hashlib
from PIL import Image
P=Path(__file__).resolve().parent;R=P.parents[1]/'references';D=R/'body-foundation/v06/supplements';catalog=R/'reference-catalog.json';j=json.loads(catalog.read_text(encoding='utf-8'))
for name,id,status in [('upper-body-8views-v01','MIA-BODY-V06-SUPPLEMENT-8-V01','generated_supplement_partial_hold_E_F'),('low-pelvis-E2-F2-v01','MIA-BODY-V06-SUPPLEMENT-LOW-E2-F2-V01','generated_correction_under_review')]:
 f=D/(name+'.png');im=Image.open(f);digest=hashlib.sha256(f.read_bytes()).hexdigest();p=f.with_suffix('.provenance.json')
 row=dict(id=id,status=status,role='auxiliary_views_and_pose_continuity_study',path=str(f.relative_to(R)).replace('\\','/'),sha256=digest,size=list(im.size),mode=im.mode,origin='Built-in image_gen; original generated file preserved',derived_from='MIA-BODY-V06-USER-CONFIRMED-20261102',prompt=str(f.with_suffix('.prompt.txt').relative_to(R)).replace('\\','/'),limits='Illustrated inference, not measured projections or model renders. Prompt angles are not calibrated camera evidence; G/H arms appear closer to horizontal than requested60degrees. v06 remains authority. E/F initial narrow-pelvis feedback applies to reference art only, not model hip widening.')
 p.write_text(json.dumps(row,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');row['provenance']=str(p.relative_to(R)).replace('\\','/');j['assets']=[a for a in j['assets'] if a['id']!=id]+[row]
catalog.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
file=R/'files.json';inventory=json.loads(file.read_text(encoding='utf-8'))
for f in [D/'upper-body-8views-v01.png',D/'low-pelvis-E2-F2-v01.png',R/'received/mia-body-v06-confirmed-20261102.png']:
 im=Image.open(f);path=str(f.relative_to(R)).replace('\\','/');row=dict(path=path,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),size=list(im.size),mode=im.mode)
 inventory['images']=[r for r in inventory['images'] if r['path']!=path]+[row]
file.write_text(json.dumps(inventory,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print('SUPPLEMENTS_RECORDED')
