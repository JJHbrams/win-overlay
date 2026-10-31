from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib
O=Path(__file__).resolve().parent
R=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def artifact(p):return {'path':str(p.resolve()),'sha256':sha(p)}
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
master=R/'mia-clean-master-v22.png';expression=R/'mia-expression-style-confirmed-20261031.png'
# Source anchors are manually observed, with uncertainty. Registration never warps a feature.
rows=[
 ('front',master,[220,0,430,180],(325,73.5),(331,111),(500,516),(500,672),'Art roll roughly -12 degrees; yaw near front. Source anchors +/-2px, model +/-5px.'),
 ('profile',master,[495,0,705,180],(558,70),(557,107),(333,515),(365,669),'Art roughly 80-90deg versus model90; eye under hair. Source +/-3px, model eye is occluded by hair and estimated +/-12px; chin visible +/-3px.'),
 ('back',master,[730,0,950,190],(836,19),(836,115),(500,250),(500,600),'Rear crown to estimated covered nape only; low confidence. Not skull-height evidence.'),
 ('left_oblique',expression,[1190,0,1510,245],(1305,91),(1320,156),(404,511),(403,667),'Panel04 estimated yaw30-45deg with nonzero roll/pitch; model45deg neutral. Anchors +/-4/6px.'),
 ('right_oblique',expression,[810,0,1135,245],(940,99),(958,167),(590,512),(589,670),'Panel03 is a subtle angle, NOT a solved opposite45deg reference. Opposite-side color correspondence limited; no mirrored or warped art. ART UNVERIFIED for exact view.')]
manifest=json.loads((O/'manifest.json').read_text());cams=json.loads((O.parents[1]/'camera-records.json').read_text());review=[]
for key,ref,crop,a,b,ma,mb,uncertain in rows:
 scale=.5*(mb[1]-ma[1])/(b[1]-a[1]);tx=ma[0]*.5-(a[0]-crop[0])*scale;ty=ma[1]*.5-(a[1]-crop[1])*scale
 canvas=Image.new('RGB',(1500,580),(235,235,235));draw=ImageDraw.Draw(canvas)
 ci=Image.open(ref).convert('RGB').crop(crop);ci.resize((round(ci.width*scale),round(ci.height*scale)),Image.Resampling.LANCZOS)
 pane=Image.new('RGB',(500,500),(210,215,217));pane.paste(ci.resize((round(ci.width*scale),round(ci.height*scale)),Image.Resampling.LANCZOS),(round(tx),round(ty)));canvas.paste(pane,(0,40))
 for j,p in enumerate([O.parents[1]/('candidate_'+key+'.png'),O/('candidate_'+key+'.png')],1):canvas.paste(Image.open(p).convert('RGB').resize((500,500),Image.Resampling.LANCZOS),(j*500,40))
 for j,label in enumerate(['SOURCE ART (raw crop)','BASELINE 396 / light toon','CANDIDATE / projected art']):draw.text((j*500+12,10),label,font=font,fill=(20,20,20))
 draw.text((12,546),key.upper()+': fixed model ORTHO .48m; uniform registration only. Art angle/occlusion limits in JSON.',font=small,fill=(20,20,20));path=O/('reference-board_'+key+'.png');canvas.save(path)
 reference=artifact(ref);reference['crop_xyxy']=crop
 reg={'uniform_scale':scale,'translation_xy':[tx,ty],'rotation_degrees':0,'normalization_basis':'Vertical eye-to-chin height only; back uses crown-to-estimated-nape. This distance is excluded from proportion validation.','notes':'Manual source/model anchors '+str([a,b,ma,mb])+'; crop-relative translation; no mirroring, per-feature warp or anisotropic scale.'}
 modelreg={'uniform_scale':.5,'translation_xy':[0,0],'rotation_degrees':0,'normalization_basis':'Same unchanged 1000-square model frame to 500-square comparison panel.'}
 review.append({'id':key,'reference':reference,'baseline_render':artifact(O.parents[1]/('candidate_'+key+'.png')),'candidate_render':artifact(O/('candidate_'+key+'.png')),'comparison_board':artifact(path),'baseline_camera':cams[key],'candidate_camera':cams[key],'reference_registration':reg,'baseline_registration':modelreg,'candidate_registration':modelreg,'pose_uncertainty':uncertain,'observed_differences':'Generated fixed-view paint adds selective overlap lines and sheen. Visible surface pigment projected to existing UV and blended across views with depth visibility. No new source detail recovery; input panels only 512 square.','unresolved':'Reference thin deliberate contours and nonuniform selected sheen remain incompletely matched. Source geometry roughness and incorrect rear knot unchanged. Exact opposite-oblique art correspondence is not established.','material_mode':'Same actual EEVEE light-responsive toon rig and diffuse ramp. Candidate uses painted sheen and disables main extra Glossy term. Unseen UV areas retain checkpoint pigment.'})
pack={'schema_version':1,'part':'surface','baseline_native':artifact(Path(manifest['source'])),'candidate_native':artifact(Path(manifest['native'])),'required_views':[x[0] for x in rows],'views':review,'art_status':'UNAPPROVED; package validity does not assert likeness','diagnostics':'projection-provenance.json'};(O/'reference-review.json').write_text(json.dumps(pack,indent=2),encoding='utf8')
