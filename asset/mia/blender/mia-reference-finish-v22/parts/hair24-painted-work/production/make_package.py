import json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
P=Path(sys.argv[1]);native=Path(sys.argv[2]);OLD=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/parts/hair-ink-paint/reference-review.json')
old=json.loads(OLD.read_text());cams=json.loads((P/'review-cameras.json').read_text())
def art(p):return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
rows=[]
for refrow in old['views']:
 name=refrow['id'];refpath=(OLD.parent/refrow['reference']['path']).resolve();crop=refrow['reference']['crop_xyxy'];ref=Image.open(refpath).convert('RGB').crop(crop);r=refrow['reference_registration'];scale=r['uniform_scale']*1.52;tx,ty=[v*1.52 for v in r['translation_xy']]
 panel=ref.transform((760,760),Image.Transform.AFFINE,(1/scale,0,-tx/scale,0,1/scale,-ty/scale),resample=Image.Resampling.BICUBIC,fillcolor=(225,228,230))
 board=Image.new('RGB',(2280,824),(235,237,239));board.paste(panel,(0,64));board.paste(Image.open(P/('baseline_'+name+'.png')).convert('RGB'),(760,64));board.paste(Image.open(P/('candidate_'+name+'.png')).convert('RGB'),(1520,64));draw=ImageDraw.Draw(board)
 for x,title in [(12,'SOURCE ART - registered uniform scale'),(772,'HAIR0D BASELINE - ORTHO'),(1532,'V24 CANDIDATE - ORTHO / WIP')]:draw.text((x,14),title,fill=(20,25,30))
 draw.text((12,38),name+' | Source pose estimated; opposite oblique is limited. Ear/nape extraction defects remain.',fill=(80,35,25));bp=P/('reference-board_'+name+'.png');board.save(bp)
 reg={'uniform_scale':scale,'translation_xy':[tx,ty],'rotation_degrees':0,'normalization_basis':r['normalization_basis'],'notes':'Inherited hair0d registration scaled uniformly from 500px panel to760px panel; matched ortho .48m centerZ1.55; no local warp. '+r['notes']}
 modelreg={'uniform_scale':1,'translation_xy':[0,0],'rotation_degrees':0,'normalization_basis':'Actual saved 760px camera render, same framing and pose baseline/candidate. No image normalization counted as validation.'}
 differences='Central tiny cord replaced by three overlapping closed gathered curls, shallow unequal strand banks, source-directed pigment if paint candidate. Main detailed hair unchanged.' if name in ['back','profile'] else 'Rear gathering change is occluded or marginal; main silhouette and forward hair preserved.'
 rows.append({'id':name,'reference':{**art(refpath),'crop_xyxy':crop},'baseline_render':art(P/('baseline_'+name+'.png')),'candidate_render':art(P/('candidate_'+name+'.png')),'comparison_board':art(bp),'baseline_camera':cams[name],'candidate_camera':cams[name],'reference_registration':reg,'baseline_registration':modelreg,'candidate_registration':modelreg,'pose_uncertainty':refrow['pose_uncertainty']+' Current model yaw front0/profile82/back180/obliques+35,-35; drawings not exact orthographic geometry.','observed_differences':differences,'unresolved':['ART UNAPPROVED; source size/gathering continuity needs independent review','Main ear/nape extraction sheets remain cut and jagged; rejected boundary relaxation excluded','No final rig/physics or full hair atlas repair'],'material_mode':'Actual toon shader; source constant ash or generated projected pigment documented in native map inventory; matte and UV supplements separate.'})
package={'schema_version':1,'part':'surface','baseline_native':art(Path(json.loads((P.parent/'sculpt2/manifest.json').read_text())['source']['path'])),'candidate_native':art(native),'required_views':[r['id'] for r in rows],'views':rows,'art_status':'UNAPPROVED WIP, no AC5/AC6 PASS claim'}
(P/'reference-review.json').write_text(json.dumps(package,indent=2));print(P/'reference-review.json')
