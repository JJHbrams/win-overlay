from pathlib import Path
import json,math,hashlib,textwrap
from PIL import Image,ImageDraw,ImageFont
OUT=Path(__file__).resolve().parent
ROOT=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay')
REF=ROOT/'asset/mia/references/mia-clean-master-v22.png';VIS=ROOT/'asset/mia/references/body-foundation/v06/mia-body-visibility-guide-v06.png';TURN=ROOT/'asset/mia/references/body-foundation/v06/mia-body-turnaround-v06.png'
REV=ROOT/'asset/mia/blender/mia-reference-finish-v17/integrated-v18/fresh-review'
land=json.loads((OUT/'front-landmarks.json').read_text())['landmarks'];pupils=[a['points'][0]['world_m'] for a in land['iris_pupil_uv_centers'] if a['kind']=='pupil_shader_center'];chin=land['chin_actual_mesh_min_z']['world_m'];mouth=land['mouth_geometric_boundary']['center_mean']['world_m']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
font=lambda n:ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',n)
BG=(239,242,244);INK=(24,33,42);MUTED=(62,76,88);CW=440;CH=378;GAP=22;X0=150
records=[]
def proj(p,yaw):
 y=math.radians(yaw);return [448+(p[0]*math.cos(y)+p[1]*math.sin(y))*896/.48,448-(p[2]-1.555)*896/.48]
def average(ps):return [sum(p[i] for p in ps)/len(ps) for i in [0,1]]
def row_data(label,source,crop,eye,chinref,yaw,model,notes,back=False):
 if back:
  ma=[448,237];mb=[448,448-(1.490-1.555)*896/.48];ra=eye;rb=chinref
 else:
  ma=average([proj(p,yaw) for p in pupils]);mb=proj(chin,yaw);ra=eye;rb=chinref
 scale=(rb[1]-ra[1])/(mb[1]-ma[1]);translation=[ra[i]-scale*ma[i] for i in [0,1]]
 # SAME isotropic raster mapping for model and reference coordinates. No rotation.
 display=min(CW/(crop[2]-crop[0]),CH/(crop[3]-crop[1]));pad=[(CW-display*(crop[2]-crop[0]))/2,(CH-display*(crop[3]-crop[1]))/2]
 sourceim=Image.open(source).convert('RGB');modelim=Image.open(model).convert('RGB')
 refaff=(1/display,0,crop[0]-pad[0]/display,0,1/display,crop[1]-pad[1]/display)
 modelaff=(1/(display*scale),0,(crop[0]-pad[0]/display-translation[0])/scale,0,1/(display*scale),(crop[1]-pad[1]/display-translation[1])/scale)
 refout=sourceim.transform((CW,CH),Image.Transform.AFFINE,refaff,Image.Resampling.BICUBIC,fillcolor=BG)
 modout=modelim.transform((CW,CH),Image.Transform.AFFINE,modelaff,Image.Resampling.BICUBIC,fillcolor=BG)
 overlay=Image.blend(refout,modout,.5)
 def targetpoint(p):return [pad[i]+display*(p[i]-crop[i]) for i in [0,1]]
 for im in [refout,modout,overlay]:
  dr=ImageDraw.Draw(im)
  for p in [ra,rb]:
   x,y=targetpoint(p);dr.line((x-5,y,x+5,y),fill=(0,150,165),width=2);dr.line((x,y-5,x,y+5),fill=(0,150,165),width=2)
 rec={'label':label,'reference':str(source),'reference_sha':sha(source),'reference_crop_original_pixels':crop,'reference_anchor_a':ra,'reference_anchor_b':rb,'reference_anchor_confidence':'low: nape hidden, +-12 source pixels' if back else 'medium-low: tiny original panel, manual+-2 source pixels; eye midpoint/visible pupil to chin','model_render':str(model),'model_render_sha':sha(model),'camera':{'yaw_deg':yaw,'elevation_deg':0,'roll_deg':0,'ortho_scale_m':.48,'target':[0,0,1.555],'resolution':[896,896]},'model_anchor_a_pixels':ma,'model_anchor_b_pixels':mb,'model_to_reference_transform':{'isotropic_scale':scale,'translation_pixels':translation,'rotation_deg':0,'anisotropic_warp':False},'display_crop_scale':display,'normalized_dimension':'hair-crown to estimated nape vertical height' if back else 'visible pupil/eye-midpoint to geometric chin VERTICAL height','remaining_dimensions':'Horizontal silhouette width, nose/lip projection, hair volume and lateral arc are NOT normalized; reference roll/pitch remains unmatched.','notes':notes}
 if not back:rec['model_mouth_after_transform_reference_pixels']=[scale*v+translation[i] for i,v in enumerate(proj(mouth,yaw))];rec['model_chin_after_transform_reference_pixels']=[scale*v+translation[i] for i,v in enumerate(mb)]
 records.append(rec);return refout,modout,overlay,rec
rows=[('FRONT',REF,[220,0,430,180],[325,73.5],[331,111],0,REV/'close_front_hair.png','Top FRONT panel; head roll about -12 deg remains. Vertical eye-to-chin normalized; width remains measurable.',False),('SIDE',REF,[495,0,705,180],[558,70],[557,107],90,REV/'close_profile_hair.png','True 90 deg model profile; art may be slightly short of90. Eye-to-chin normalized; nose/lip/back-head depth remains.',False),('BACK',REF,[730,0,950,190],[836,19],[836,115],180,REV/'close_back_hair.png','LOW confidence: hair crown to estimated hidden nape. Crown anchor excludes loose spikes. Does NOT validate bare skull height.',True),('3/4 LABEL',REF,[990,0,1210,190],[1085,73.5],[1097,111],20,OUT/'multi-view-model-yaw20.png','20 deg candidate, NOT a solved camera. Art reads near-front (roughly0-20); see20/35/45 bracket. Roll/pitch unmatched.',False)]
W=X0+3*CW+2*GAP+30;RH=465;H=125+4*RH+90;canvas=Image.new('RGB',(W,H),BG);draw=ImageDraw.Draw(canvas)
draw.text((28,18),'MIA v22 MULTIVIEW REGISTRATION | actual v18 model',font=font(27),fill=INK)
draw.text((28,55),'Uniform scale + translation only. Shape comparison, not lighting/color calibration. No model or reference edits.',font=font(18),fill=MUTED)
for i,t in enumerate(['v22 original top-panel crop','Actual model / registered','50% overlay / same transform']):draw.text((X0+i*(CW+GAP),92),t,font=font(19),fill=INK)
for row,args in enumerate(rows):
 a,b,c,r=row_data(*args);y=125+row*RH;draw.text((18,y+12),args[0],font=font(21),fill=INK)
 for col,im in enumerate([a,b,c]):canvas.paste(im,(X0+col*(CW+GAP),y))
 for j,line in enumerate(textwrap.wrap(args[7],145)):draw.text((X0,y+CH+8+j*22),line,font=font(17),fill=MUTED)
draw.text((28,H-64),'Normalized height cannot independently prove height accuracy. No pass: side planes, silhouette, hair framing and camera ambiguity stay visible.',font=font(18),fill=INK)
draw.text((28,H-36),'Source model87334607 unchanged. Cyan crosses are registration anchors. Original reference pixels and every transform are in multi-view-registration.json.',font=font(17),fill=MUTED)
canvas.save(OUT/'multi-view-registered-comparison.png')
# Supplemental1: true camera bracket; same reference eye/chin anchors, no per-feature warp.
yawfig=Image.new('RGB',(4*CW+3*GAP+40,CH+145),BG);dr=ImageDraw.Draw(yawfig);dr.text((20,15),'v22 3/4 label: camera bracket (not a45-degree assumption)',font=font(26),fill=INK)
refcrop=None
for i,yaw in enumerate([20,35,45]):
 model=OUT/('multi-view-model-yaw'+str(yaw)+'.png') if yaw!=45 else REV/'close_left_hair.png'
 aa,bb,cc,rr=row_data('YAW_BRACKET_'+str(yaw),REF,[990,0,1210,190],[1085,73.5],[1097,111],yaw,model,'Same reference anchors and vertical scale basis; no independent eye/face reshaping.')
 if refcrop is None:refcrop=aa;yawfig.paste(aa,(20,65));dr.text((20,CH+76),'Original top 3/4 panel',font=font(19),fill=INK)
 x=20+(i+1)*(CW+GAP);yawfig.paste(bb,(x,65));dr.text((x,CH+76),str(yaw)+' deg actual camera yaw',font=font(19),fill=INK)
dr.text((20,CH+112),'Art may be nearer0-20 deg and has head roll/pitch. 35/45 are shown to expose view sensitivity, not to claim a fitted camera.',font=font(18),fill=MUTED);yawfig.save(OUT/'multi-view-yaw-bracket.png')
# Supplemental2: actual short-hair visibility guide, not inferred missing references.
supp=Image.new('RGB',(W,125+2*RH+55),BG);dr=ImageDraw.Draw(supp);dr.text((24,16),'v06 VISIBILITY GUIDE | same model with hair hidden',font=font(27),fill=INK);dr.text((24,55),'Reference retains short hair; bare model exposes skull. Crown silhouette is therefore not an exact bare-skull target.',font=font(18),fill=MUTED)
for i,t in enumerate(['v06 actual head crop','Actual bare model / registered','50% overlay']):dr.text((X0+i*(CW+GAP),92),t,font=font(19),fill=INK)
for row,args in enumerate([('FRONT',VIS,[140,55,320,220],[229.5,140],[232,185],0,REV/'close_front_bald.png','Eye-to-chin vertical normalization; hair occlusion and art roll remain. No direct crown-height claim.',False),('PROFILE',VIS,[495,55,675,220],[552,135],[545,181],90,REV/'close_profile_bald.png','Actual left-profile guide: eye-to-chin normalized; nose/lip/chin and rear-skull depth remain unwarped.',False)]):
 aa,bb,cc,rr=row_data('VISIBILITY_'+args[0],*args[1:]);y=125+row*RH;dr.text((18,y+12),args[0],font=font(21),fill=INK)
 for col,im in enumerate([aa,bb,cc]):supp.paste(im,(X0+col*(CW+GAP),y))
 for j,line in enumerate(textwrap.wrap(args[7],145)):dr.text((X0,y+CH+8+j*22),line,font=font(17),fill=MUTED)
supp.save(OUT/'multi-view-visibility-supplement.png')
jsonout={'source_native_sha':json.loads((OUT/'front-landmarks.json').read_text())['source_sha_after'],'model_geometry_unchanged':True,'source_reference_hashes':{str(p):sha(p) for p in [REF,VIS,TURN]},'v06_turnaround_status':'Viewed actual full turnaround; main comparison uses v22 top four panels, supplementary comparison uses actual v06 visibility guide.','registration_policy':'Uniform scale and translation only, no2Drotation and noanisotropic/per-feature warp. Camera yaw explicit. Art roll/pitch unresolved, especially top3/4 label.','rows':records,'limitations':['Top v22 heads are low resolution; manual anchors+-2px matter.','Eye-to-chin height is normalized and cannot independently be scored for length. Root detailed front pupil-distance registration is separate.','Back nape is hair-occluded; approximate anchor makes back row low confidence.','Bare visibility supplement contains short-hair reference crown; do not infer bare skull height from that contour.','Existing source lighting is unchanged; figure does not validate albedo/diffuse/specular maps.'],'figures':['multi-view-registered-comparison.png','multi-view-yaw-bracket.png','multi-view-visibility-supplement.png']}
(OUT/'multi-view-registration.json').write_text(json.dumps(jsonout,indent=2));print('MULTIVIEW_FIGURES_DONE')
