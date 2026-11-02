"""Source2D constraints -> explicit inferred3D section/control scaffold.

Diagnostic diagrams, not painted anatomy. No unique3D/CT recovery is claimed.
"""
from pathlib import Path
import json,hashlib,html,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;O=P/'scaffold-D';O.mkdir(exist_ok=True);REF=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/references/received/mia-body-v06-confirmed-20261102.png');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(REF)=='6d88d1bc6b579d1ac53436d9f1fa50f903117ac244e307b8e08a9d1e270080e1'
colors=dict(observed_skin='#20e4f4',garment='#ffd13b',inferred='#f46bcb',occluded='#acb7c5',structural_core='#6b9fff')
features=[]
def f(name,view,kind,pts,limit):features.append(dict(name=name,view=view,kind=kind,points=pts,limitation=limit))
# Solid runs follow only visible external skin, never a lighting boundary.
f('front.left_outer_deltoid_arm','front','observed_skin',[(174,223),(160,230),(154,240),(150,250),(144,262),(142,288),(137,310),(132,332),(128,350),(120,376)],'Hair hides parts of shoulder apex and inner axilla; contour samples are visible skin runs, about3–6px uncertainty.')
f('front.right_outer_deltoid_arm','front','observed_skin',[(302,225),(313,230),(323,241),(330,252),(332,274),(336,294),(335,312),(341,334),(345,359),(360,380)],'Short hair-obscured gaps are not directly measured bone positions.')
f('front.left_waist','front','observed_skin',[(191,337),(195,350),(195,365),(185,382),(180,396)],'Visible skin boundary; small hair overlaps remain local.')
f('front.right_waist','front','observed_skin',[(288,338),(285,353),(288,370),(296,388),(306,404)],'Visible skin boundary, not a ribcage cross-section by itself.')
f('front.scoop','front','garment',[(182,251),(190,265),(207,279),(226,286),(242,289),(263,286),(284,276),(300,259)],'Cloth neckline, NOT a naked anatomical breast root.')
f('front.underband','front','garment',[(175,331),(193,326),(216,323),(239,323),(263,326),(286,331),(300,334)],'Cloth lower edge, not a directly observed inframammary fold.')
f('front.clavicle_ink','front','inferred',[(213,222),(226,219),(239,225),(251,220),(270,222)],'Drawn structural/line cue. Internal clavicle and skin relief cannot be recovered uniquely.')
f('front.pectoral_left','front','inferred',[(230,228),(211,245),(190,264),(176,286)],'Inferred pectoral fan/root continuity toward anterior axillary fold; not a traced shadow boundary.')
f('front.pectoral_right','front','inferred',[(248,228),(269,246),(290,265),(307,286)],'Inferred source-supported structural continuity; preserve thickness at arm attachment.')
f('profile.anterior_neckline_skin','profile','observed_skin',[(553,247),(543,255),(532,264),(521,273)],'Visible short anterior skin run; hair hides the upper root.')
f('profile.cup_outer','profile','garment',[(520,273),(509,280),(502,289),(500,298),(503,309),(512,320),(520,326)],'Observed cloth silhouette gives an outer depth bound; body skin inside is inferred.')
f('profile.anterior_abdomen','profile','observed_skin',[(516,334),(516,350),(519,368),(519,385),(516,402)],'Visible anterior skin run; no lighting edge is used as geometry.')
f('profile.deltoid_arm','profile','observed_skin',[(598,219),(610,223),(619,237),(628,256),(630,271),(625,288),(620,310),(616,333),(615,355)],'Observed skin silhouette; arm pose differs from native and must not be baked into torso dimensions.')
f('profile.hidden_back_ribs','profile','occluded',[(615,248),(609,274),(601,300),(589,327),(580,350)],'Back/rib surface hidden by hair and arm. These points show uncertainty corridor only, not measured surface.')
f('back.left_deltoid_arm','back','observed_skin',[(866,225),(853,234),(843,251),(838,270),(839,291),(834,316),(830,340),(822,365),(811,391)],'Visible skin runs. Hair occludes shoulder blade and posterior fold.')
f('back.right_deltoid_arm','back','observed_skin',[(997,235),(1012,242),(1022,257),(1025,280),(1024,305),(1028,330),(1035,349),(1039,369),(1050,391)],'Visible skin runs; source pose asymmetry retained as uncertainty.')
f('back.posterior_folds_hidden','back','occluded',[(865,264),(892,289),(931,304),(974,291),(1005,266)],'Entire central back/posterior axillary anatomy is hidden. Inferred using continuity and professional anatomy, not source pixels.')
f('oblique.near_shoulder_arm','oblique','observed_skin',[(1370,220),(1387,229),(1397,243),(1401,264),(1403,287),(1401,312),(1403,335),(1409,360),(1420,387)],'Visible contour; do not normalize this view separately.')
f('oblique.cup_outer','oblique','garment',[(1256,279),(1241,291),(1232,306),(1236,318),(1251,326),(1281,326),(1317,333),(1350,330)],'Garment contour bounds supported outer surface; far root hidden.')
f('oblique.waist_near','oblique','observed_skin',[(1348,337),(1344,356),(1346,373),(1355,393),(1367,409)],'Visible waist silhouette; no inferred light terminator.')
f('oblique.anterior_root_fan','oblique','inferred',[(1306,231),(1331,251),(1348,275),(1358,297)],'Inferred curved pectoral-to-axilla connection; checked in3D projections, not claimed direct wireframe recovery.')
source=dict(reference=str(REF),sha256=sha(REF),size=[1536,1024],coordinate_system='Original pixels; no aspect or per-feature stretch',authority='User-confirmed v06',features=features,legend=colors,warning='2D observed runs + explicit inferred constraints, NOT true3D/CT reconstruction. Garment, hair, pose and lighting leave local uncertainty.')
(O/'source-contours.json').write_text(json.dumps(source,indent=2)+'\n',encoding='utf-8')
im=Image.open(REF).convert('RGB');draw=ImageDraw.Draw(im);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
def dashed(draw,pts,color,width=2,dash=7):
    for a,b in zip(pts[:-1],pts[1:]):
        a=np.asarray(a,float);b=np.asarray(b,float);dist=np.linalg.norm(b-a);steps=max(1,int(math.ceil(dist/dash)))
        for j in range(steps):
            if j%2==0:draw.line([tuple(a+(b-a)*j/steps),tuple(a+(b-a)*min(j+1,steps)/steps)],fill=color,width=width)
for f0 in features:
    col=colors[f0['kind']];pts=f0['points']
    if f0['kind'] in ['inferred','occluded']:dashed(draw,pts,col)
    else:draw.line(pts,fill=col,width=2)
    draw.text(tuple(pts[0]),f0['name'].split('.')[-1],fill=col,font=font,stroke_width=1,stroke_fill='#273039')
im.save(O/'source-contours-overlay.png')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" viewBox="0 0 1536 1024">',f'<image href="{html.escape(str(REF))}" width="1536" height="1024"/>']
for item in features:
    pts=' '.join(f'{x},{y}' for x,y in item['points']);dash=' stroke-dasharray="7 7"' if item['kind'] in ['inferred','occluded'] else '';svg.append(f'<polyline points="{pts}" fill="none" stroke="{colors[item["kind"]]}" stroke-width="2"{dash}><title>{html.escape(item["name"]+": "+item["limitation"])}</title></polyline>')
svg.append('</svg>');(O/'source-contours-overlay.svg').write_text('\n'.join(svg),encoding='utf-8')
# Common stations use the same whole-height registration as current/source4.
measure=json.loads((P/'current-proportions.json').read_text());zsole=measure['body_bounds']['minimum'][2];zcrown=max(q['maximum'][2] for q in measure['visible_mesh_bounds'].values());mpp=(zcrown-zsole)/896;Z=lambda py:zcrown-(py-54)*mpp
sections=[
    # y, coreHalfWidth, frontY, backY, outerHalfWidth, lobeY, centerFrontY, provenance
    (220,.040,-.050,.039,.040,-.050,-.050,'neck/clavicle region inferred from drawn cue; hidden skin limits'),
    (240,.113,-.063,.073,.116,-.071,-.063,'upper thorax/pec inferred; shoulder visible bounds constrain width'),
    (265,.112,-.077,.078,.120,-.118,-.078,'upper/lateral root inferred; garment neckline and profile skin bound exterior'),
    (290,.108,-.082,.080,.125,-.148,-.084,'maxcup cloth bounds frontx173..307 / profilex~500; core behind cloth inferred'),
    (310,.106,-.091,.067,.122,-.131,-.095,'lower supported cup envelope from garment, core inferred'),
    (328,.104,-.105,.049,.113,-.116,-.106,'underband garment bound; anatomical fold NOT directly observed'),
    (350,.090,-.112,.025,.090,-.112,-.112,'visible waist/anterior skin; back obscured'),
    (365,.087,-.107,.020,.087,-.107,-.107,'visible waist side/anterior; inferred hidden arc')]
def ring(hw,front,back,lobe,centerfront,z):
    side=-.004;outerfront=(front+side)*.55
    return [[0,centerfront,z],[-hw*.50,lobe,z],[-hw*.90,outerfront,z],[-hw,side,z],[-hw*.75,back*.78,z],[-hw*.4,back,z],[0,back,z],[hw*.4,back,z],[hw*.75,back*.78,z],[hw,side,z],[hw*.90,outerfront,z],[hw*.50,lobe,z]]
curves=[];stations=[];core_rings=[];support_rings=[];branch_controlnets=[]
def c(name,kind,pts,closed=False,limit='Inferred3D structural guide; not a directly observed source surface.'):
    curves.append(dict(name=name,kind=kind,points=np.asarray(pts).tolist(),closed=closed,limitation=limit))
for i,(py,hw,front,back,ohw,lobe,cf,prov) in enumerate(sections):
    zz=Z(py);quarter_front=front*.85+(-.004)*.15;cr=ring(hw,front,back,quarter_front,front,zz);sr=ring(ohw,front,back,lobe,cf,zz);core_rings.append(cr);support_rings.append(sr);c(f'core.section.{i:02d}','structural_core',cr,True,prov+'; rounded core quarter/front curvature is inferred, not a directly observed cloth/body equality');c(f'support.section.{i:02d}','garment',sr,True,prov);stations.append(dict(id=i,source_y=py,z=zz,core_half_width=hw,outer_half_width=ohw,front_core_y=front,front_core_quarter_y=quarter_front,front_outer_y=lobe,back_y=back,uncertainty_m=[.010,.020] if py<340 else [.006,.015],evidence=prov))
for j in range(12):
    c(f'core.meridian.{j:02d}','structural_core',[r[j] for r in core_rings]);c(f'support.meridian.{j:02d}','inferred',[r[j] for r in support_rings])
# Integrated fan/root/fold network: no hard border at old breast-vs-arm masks.
for sign,side in [(-1,'R'),(1,'L')]:
    def mirror(points):return [[sign*x,y,z] for x,y,z in points]
    c(f'{side}.clavicle_to_deltoid','inferred',mirror([[.018,-.043,Z(220)],[.060,-.038,Z(224)],[.104,-.020,Z(229)],[.141,.000,Z(234)]]))
    c(f'{side}.trapezius_ridge','inferred',mirror([[.027,.026,1.437],[.045,.030,1.405],[.083,.025,Z(224)],[.141,.005,Z(234)]]),'','Source upper shoulder skin constrains lateral extent; neck/back arcs inferred and face/chin stays frozen.')
    fan=[]
    for n,(rootz,rooty) in enumerate([(Z(238),-.067),(Z(263),-.080),(Z(285),-.086)]):
        endpoint=[.138+n*.001,-.029+n*.004,1.347-n*.010]
        row=mirror([[.005,rooty,rootz],[.052,rooty-.004,rootz+.003],[.100,-.052,rootz+.010],endpoint]);fan.append(row)
        c(f'{side}.pectoral_fan.{n}','inferred',row,False,'Inferred clavicular/sternal fan toward a finite20mm-thick insertion; endpoints do NOT collapse to one point.')
    branch_controlnets.append(dict(name=side+'.anterior_fan_web',kind='inferred',vertices=[p for row in fan for p in row],faces=[[r*4+j,r*4+j+1,(r+1)*4+j+1,(r+1)*4+j] for r in range(2) for j in range(3)],limitation='Open branch-aware pectoral control web, NOT a finished anatomical surface; root/axilla inferred behind cloth.'))
    c(f'{side}.anterior_axillary_fold','inferred',mirror([[.082,-.067,Z(302)],[.112,-.056,Z(281)],[.137,-.030,Z(254)],[.149,-.015,Z(243)]]),'','Gradual pectoral/fat-to-humerus support; hidden source root, no fixed textbook angle.')
    c(f'{side}.posterior_axillary_fold','occluded',mirror([[.083,.052,Z(302)],[.115,.047,Z(280)],[.140,.027,Z(255)],[.149,.010,Z(243)]]),'','Source back/hair and arm hide this arc; inferred posterior fold kept explicit.')
    c(f'{side}.lateral_breast_root','inferred',mirror([[.075,-.105,Z(315)],[.112,-.090,Z(295)],[.124,-.065,Z(274)],[.137,-.030,Z(254)]]))
    c(f'{side}.lower_return','inferred',mirror([[.014,-.101,Z(325)],[.049,-.124,Z(317)],[.082,-.116,Z(317)],[.112,-.080,Z(302)]]),'','Anatomical return is inferred behind supportive bra; bridge/underband remain separate garment constraints.')
    c(f'{side}.shoulder_cap','inferred',mirror([[.105,-.044,Z(235)],[.131,-.040,Z(228)],[.150,-.006,Z(238)],[.146,.030,Z(249)],[.116,.046,Z(244)]]))
    # Two-sided fold web and finite arm rails explicitly supply the branch
    # missing from a torso-only stack of horizontal sections.
    anterior=mirror([[.082,-.067,Z(302)],[.112,-.056,Z(281)],[.137,-.030,Z(254)],[.149,-.015,Z(243)]])
    posterior=mirror([[.083,.052,Z(302)],[.115,.047,Z(280)],[.140,.027,Z(255)],[.149,.010,Z(243)]])
    branch_controlnets.append(dict(name=side+'.axillary_fold_bridge',kind='occluded',vertices=anterior+posterior,faces=[[j,j+1,4+j+1,4+j] for j in range(3)],limitation='Anterior/posterior fold branch corridor around axillary opening. Hidden arcs inferred; NOT an underarm membrane target.'))
    upperarm=measure['bones']['J_Bip_'+side+'_UpperArm'];head=np.asarray(upperarm['head']);tail=np.asarray(upperarm['tail']);head[0]+=sign*.015;head[2]-=.012;tail[0]+=sign*.015;tail[2]-=.012
    axis=tail-head;axis/=np.linalg.norm(axis);front=np.array([0.,-1.,0.]);out=np.cross(axis,front);out/=np.linalg.norm(out)
    for n,offset in enumerate([front*.030,-front*.030,out*.024,-out*.024]):
        c(f'{side}.humeral_rail.{n}','inferred',[head+offset,head+axis*.060+offset*.95,head+axis*.120+offset*.90],False,'Current native arm orientation transported to provisional widened shoulder. Source arm pose differs; this is not a source limb-length fit.')
guide=dict(schema=1,reference=source['reference'],reference_sha256=source['sha256'],units='metres in current scene world',height_registration=dict(crown_z=zcrown,sole_z=zsole,source_crown_y=54,source_sole_y=950,metres_per_source_pixel=mpp),camera_assumption='Provisional orthographic yaw0/90/180/30 matching review cameras, not recovered true source camera. Pose and silhouette constraints retain uncertainty; no uniqueCT inference.',stations=stations,curves=curves,core_loft_rings=core_rings,support_loft_rings=support_rings,branch_controlnets=branch_controlnets,colors=colors,head='Face690/head unchanged; guide stops below chin; true head scale remains separate root review.',status='SCAFFOLD_FOR_ROOT_REVIEW; NO D BODY MUTATION',sources=[dict(title='Proko How to Draw Breasts – Form & Motion',url='https://www.proko.com/course-lesson/how-to-draw-breasts-form-and-motion/',access='Public Lesson Notes only',application='Gradual pectoral/soft-mass/axillary continuity and shoulder-motion coupling; not a fixed45degree rule.'),dict(title='Proko How to Draw Pecs – Form',url='https://www.proko.com/course-lesson/how-to-draw-pecs-form/',access='Public Lesson Notes only',application='Curved upper front plane; clavicular/sternal fan toward arm; lateral upturn and retained tendon-region thickness. Mia-supported art determines shape bounds.')])
guide['revision']=2;guide['revision_note']='Inferred core front-quarter depths recede toward lateral ribs, avoiding a flat anterior core segment. Observed cloth bounds unchanged.'
(O/'guide-data.json').write_text(json.dumps(guide,indent=2)+'\n',encoding='utf-8');print('SOURCE_CONTOUR_SCAFFOLD_DATA_DONE',len(features),len(curves),len(stations),flush=True)
