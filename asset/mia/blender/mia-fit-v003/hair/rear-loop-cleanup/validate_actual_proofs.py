"""Validate actual runtime evidence and build source-neutral pair review; no ART verdict."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np,json,hashlib,re
P=Path(__file__).resolve().parent;reports=[];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for folder,count in [('actual-first4',4),('actual-final6',6)]:
 records=json.loads((P/folder/'records.json').read_text());assert len(records)==count;log=(P/(folder+'.log')).read_text(encoding='utf-8',errors='replace');assert not re.search(r'(?i)error|traceback|failed|too many|unsupported',log);assert 'LOOP_ACTUAL_DONE '+str(count) in log
 for view in sorted({r['view'] for r in records}):
  b=next(r for r in records if r['view']==view and r['stage']=='baseline');c=next(r for r in records if r['view']==view and r['stage']=='candidate')
  for key in ['camera','actual_lights','actual_pose','world','base_native_sha256','mask_payload_sha256']+(['actual_render_sampling'] if folder=='actual-final6' else []):assert b[key]==c[key],(folder,view,key)
  assert b['selected_faces']==c['selected_faces']==1781 and not b['native_saved'] and not c['native_saved'];assert sha(b['path'])==b['image_sha256'] and sha(c['path'])==c['image_sha256'];a=np.array(Image.open(b['path']).convert('RGBA'),int);z=np.array(Image.open(c['path']).convert('RGBA'),int);assert a.shape==z.shape;delta=np.abs(a-z);reports.append(dict(folder=folder,view=view,resolution=list(a.shape[:2]),pixels_max_channel_difference_over8=int((delta.max(2)>8).sum()),max_channel_difference=int(delta.max()),paired_fixture_exact=True,shader_runtime_error_free=True))
f=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',20);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',16);board=Image.new('RGB',(1536,1760),(237,241,244));dr=ImageDraw.Draw(board)
for row,view in enumerate(['018','021','000']):
 y=15+row*570;a=Image.open(P/'actual-final6'/('baseline-'+view+'.png')).convert('RGBA');z=Image.open(P/'actual-final6'/('candidate-'+view+'.png')).convert('RGBA')
 for x,im,title in [(0,a,'BASELINE'),(512,z,'CANDIDATE')]:board.paste(im.convert('RGB'),(x,y+35));dr.text((x+10,y),view+' '+title,font=f,fill=(20,30,40))
 d=np.abs(np.array(a,dtype=int)-np.array(z,dtype=int)).max(2);diff=np.zeros((512,512,3),np.uint8);diff[d>2]=[75,95,115];diff[d>8]=[235,160,45];diff[d>32]=[240,65,45];board.paste(Image.fromarray(diff),(1024,y+35));dr.text((1035,y),'DELTA >2 / >8 gold / >32 red',font=small,fill=(20,30,40))
dr.text((10,1732),'Actual512-square/32TAA pairs; same camera/lights/world/pose. Root/nape mask only; original geometry/UV/normals/identity held. No whole-hair ART claim.',font=small,fill=(20,30,40));board.save(P/'ACTUAL_ROOT_FRONT_REVIEW.png');out=dict(status='TECHNICAL_EVIDENCE_VALID; ROOT_ART_SELECTION_REQUIRED',pairs=reports,scope='Bounded unsupported U cleanup only',native_saved=False,ART=False);(P/'ACTUAL_PROOF_VALIDATION.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,indent=2))
