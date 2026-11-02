"""Coarse source-constrained BELOW-HEAD section + limb-branch scaffold.
No body mutation. Visible/inferred bounds retain pose/occlusion confidence.
"""
from pathlib import Path
import json,copy,hashlib
import numpy as np
P=Path(__file__).resolve().parent;O=P/'scaffold-fullbody';O.mkdir(exist_ok=True);g=copy.deepcopy(json.loads((P/'scaffold-D/guide-data.json').read_text()));g['revision']=3;g['revision_note']='Full below-head coarse section/branch cage; upper-body revision2 reused. No model hip change inferred from supplementary E/F.';mpp=g['height_registration']['metres_per_source_pixel'];zc=g['height_registration']['crown_z'];Z=lambda y:zc-(y-54)*mpp;X=lambda x:(x-239)*mpp;Y=lambda x:(x-568)*mpp-.018
mapping=np.load((Path(__file__).resolve().parent/'inputs/mapping-frame1.npz'));q0=mapping['q0_world'];bodyweights=np.load(P/'current-body-weights.npz');groupnames=bodyweights['names'].tolist();bodyW=bodyweights['weights']
g['curves']=[c for c in g['curves'] if '.humeral_rail.' not in c['name']]
for item in g['curves']:
    if item['name'] in ['support.section.06','support.section.07']:item['kind']='inferred'
evidence=[]
def curve(name,kind,points,closed=False,limit='Inferred coarse3D guide between explicit observed bounds; not uniqueCT recovery.'):
    g['curves'].append(dict(name=name,kind=kind,points=np.asarray(points).tolist(),closed=closed,limitation=limit))
def ring(cx,cy,zz,hx,hy):
    # Explicit rounded section control polygon, not breast primitives.
    return [[cx,cy-hy,zz],[cx-hx*.50,cy-hy*.86,zz],[cx-hx*.90,cy-hy*.45,zz],[cx-hx,cy,zz],[cx-hx*.78,cy+hy*.65,zz],[cx-hx*.42,cy+hy*.95,zz],[cx,cy+hy,zz],[cx+hx*.42,cy+hy*.95,zz],[cx+hx*.78,cy+hy*.65,zz],[cx+hx,cy,zz],[cx+hx*.90,cy-hy*.45,zz],[cx+hx*.50,cy-hy*.86,zz]]
def controlnet(name,rings,kind):
    nr=len(rings);nc=len(rings[0]);g['branch_controlnets'].append(dict(name=name,kind=kind,vertices=[p for r in rings for p in r],faces=[[r*nc+j,r*nc+(j+1)%nc,(r+1)*nc+(j+1)%nc,(r+1)*nc+j] for r in range(nr-1) for j in range(nc)],limitation='Open section/control loft. Branch corridor is not a membrane or final watertight body.'))
def series(name,rows,kind='inferred',closed=True):
    rings=[]
    for j,row in enumerate(rows):
        r=ring(*row);rings.append(r);curve(f'{name}.section.{j:02d}',kind,r,True)
    for k in [0,3,6,9]:curve(f'{name}.rail.{k:02d}',kind,[r[k] for r in rings])
    curve(name+'.envelope_axis',kind,[[r[0][0],(r[0][1]+r[6][1])/2,r[0][2]] for r in rings],False,'Envelope centerline, NOT a directly observed internal bone axis.')
    controlnet(name+'.controlnet',rings,kind);return rings
# Waist/pelvis common-height bounds derive ONLY from original confirmed v06.
pelvis=[]
for py,front,side in [(385,[184,295],[519,615]),(410,[170,307],[514,622]),(440,[159,316],[528,631]),(455,[156,320],[530,630])]:
    cx=X(sum(front)/2);cy=Y(sum(side)/2);hx=(front[1]-front[0])*mpp/2;hy=(side[1]-side[0])*mpp/2;pelvis.append([cx,cy,Z(py),hx,hy]);evidence.append(dict(region='waist/pelvis',source_y=py,front_bounds=front,profile_bounds=side,kind='visible exterior/brief envelope, hipjoint inside inferred',uncertainty_px=8,confidence_front=.75,confidence_profile=.55,restriction='Original v06 only; auxiliary E/F hip feedback does not prescribe model hip widening.'))
pelvisrings=series('pelvis',pelvis,'inferred')
trunk_rings=[g['support_loft_rings'][-1],((np.asarray(g['support_loft_rings'][-1])+np.asarray(pelvisrings[0]))/2).tolist(),pelvisrings[0]]
for j in range(12):curve(f'trunk_to_pelvis.rail.{j:02d}','inferred',[r[j] for r in trunk_rings])
controlnet('trunk_to_pelvis.continuity',trunk_rings,'inferred')
# Per-leg front bounds + shared profile silhouette. Side view overlap prevents
# independent bilateral depths; this inferred mirroring is explicitly recorded.
legdata=[(485,[149,233],[244,327],[530,623]),(540,[153,221],[256,329],[523,618]),(600,[165,215],[260,317],[536,612]),(650,[162,215],[266,316],[550,613]),(680,[159,205],[274,324],[558,622]),(730,[145,204],[275,338],[569,640]),(780,[151,199],[288,334],[576,636]),(840,[161,185],[297,328],[580,623]),(885,[154,186],[294,326],[565,618])]
legrings={}
for side,column in [('R',1),('L',2)]:
    rows=[]
    for row in legdata:
        py=row[0];front=row[column];prof=row[3];rows.append([X(sum(front)/2),Y(sum(prof)/2),Z(py),(front[1]-front[0])*mpp/2,(prof[1]-prof[0])*mpp/2]);evidence.append(dict(region=side+'.leg',source_y=py,front_bounds=front,profile_bounds=prof,uncertainty_px=6 if py>600 else 8,confidence_front=.80,confidence_profile=.55,limitation='Profile legs overlap; common depth bounds are mirrored inference. Knee level is an external contour interval, not a measured bone pivot.'))
    legrings[side]=series(side+'.leg',rows)
    # Explicit pelvis fork rails: anterior, posterior and medial crotch paths.
    sign=-1 if side=='R' else 1
    curve(side+'.pelvis_fork.anterior','inferred',[[sign*.050,-.080,Z(435)],[sign*.095,-.078,Z(462)],legrings[side][0][0],legrings[side][1][0]])
    curve(side+'.pelvis_fork.posterior','inferred',[[sign*.040,.070,Z(435)],[sign*.100,.095,Z(465)],legrings[side][0][6],legrings[side][1][6]])
    curve(side+'.pelvis_fork.medial','inferred',[[sign*.008,-.030,Z(480)],[sign*.020,-.020,Z(495)],legrings[side][1][9 if side=='R' else 3]],False,'Open leg/crotch branch corridor. No membrane/Boolean filler is implied.')
# Coarse ankle/foot horizontal envelopes explicitly include visible sole/toe
# silhouette, without toe sculpt detail or assuming identical front/profile pose.
footdata=[(900,[149,189],[293,331],[545,618]),(925,[129,178],[308,350],[498,632]),(940,[126,180],[304,357],[504,624]),(947,[144,180],[314,341],[530,615])]
for side,column in [('R',1),('L',2)]:
    rows=[]
    for row in footdata:
        py=row[0];front=row[column];prof=row[3];rows.append([X(sum(front)/2),Y(sum(prof)/2),Z(py),(front[1]-front[0])*mpp/2,(prof[1]-prof[0])*mpp/2]);evidence.append(dict(region=side+'.foot',source_y=py,front_bounds=front,profile_bounds=prof,uncertainty_px=10,confidence_front=.60,confidence_profile=.70,limitation='Visible foot envelope, no toe topology. Source front feet turn out; profile/source pose differs. Do NOT turn projected whole-foot width into an anatomical foot-width scalar.'))
    footrings=series(side+'.foot',rows,'inferred');curve(side+'.ankle_foot_link','inferred',[legrings[side][-1][0],footrings[0][0],footrings[1][0]])
# Complete upperarm -> elbow -> forearm -> wrist -> coarse hand. Front
# external bounds are observed; profile thickness is weak where arm/hand
# overlaps torso/thigh. Different poses are retained as uncertainty.
arms=[(260,[142,170],[315,335],[567,630]),(320,[137,172],[305,336],[583,620]),(370,[121,149],[326,349],[581,613]),(430,[91,119],[347,377],[579,606]),(485,[72,95],[378,399],[575,617])]
hands=[(510,[48,83],[391,419]),(540,[45,76],[394,420]),(565,[54,74],[397,416])]
for side,column in [('R',1),('L',2)]:
    rows=[]
    for row in arms:
        py=row[0];front=row[column];prof=row[3];cy=Y(sum(prof)/2);hy=(prof[1]-prof[0])*mpp/2
        if py==260:hy=min(hy,.047) # occluded source width is an exterior bound, not a fully observed muscle diameter
        rows.append([X(sum(front)/2),cy,Z(py),(front[1]-front[0])*mpp/2,hy]);evidence.append(dict(region=side+'.arm',source_y=py,front_bounds=front,profile_exterior_bounds=prof,uncertainty_px=10,confidence_front=.65,confidence_profile=.35,limitation='Inner arm partly hair/torso-occluded; source pose differs. Ring centerline is envelope axis, not a directly measured humerus/elbow/wrist pivot.'))
    ar=series(side+'.arm',rows);last=rows[-1]
    hr=[]
    for row in hands:
        py=row[0];front=row[column];hr.append([X(sum(front)/2),last[1]-.006,Z(py),(front[1]-front[0])*mpp/2,.014]);evidence.append(dict(region=side+'.hand',source_y=py,front_bounds=front,profile_visible_outer_run=[[610,520],[617,550],[601,585],[587,615]],uncertainty_px=12,confidence_front=.65,confidence_profile=.20,limitation='Coarse hand/palm/finger envelope only. Profile hand overlaps same-colored thigh: inner depth and exact finger length are unobserved; .028m AP thickness is inferred, not a measured source span.'))
    ha=series(side+'.hand',hr,'inferred');curve(side+'.wrist_hand_link','inferred',[ar[-1][0],ha[0][0],ha[-1][0]])
    sign=1 if side=='L' else -1
    curve(side+'.shoulder_arm_link.anterior','inferred',[[sign*.139,-.024,1.344],ar[0][0],ar[1][0]])
    curve(side+'.shoulder_arm_link.posterior','occluded',[[sign*.139,.026,1.344],ar[0][6],ar[1][6]],False,'Open axillary branch corridor; source posterior fold hidden, no membrane target.')
# Full current skeleton axes are CONTEXT, distinct from observed skin bounds.
rest=json.loads((P/'current-rig-rest.json').read_text());M=np.asarray(rest['matrix_world'])
for side in ['L','R']:
    for part in ['Shoulder','UpperArm','LowerArm','Hand','UpperLeg','LowerLeg','Foot']:
        name='J_Bip_'+side+'_'+part;b=rest['pose_endpoints_world'][name];pts=[b[k] for k in ['head','tail']];curve('current_rig.'+side+'.'+part,'structural_core',pts,False,'CURRENT frame1 POSED internal rig axis for context only; never compared directly to source outer skin width as equivalent landmarks.')
g['fullbody_bound_evidence']=evidence;g['scope']='Complete below-head coarse section/branch scaffold through neck, torso, shoulders, arms, hands, waist/pelvis fork, legs and feet';g['joint_level_intervals_px']=dict(shoulder=[225,240],elbow=[350,385],wrist=[475,505],crotch=[478,490],knee=[655,690],ankle=[875,900],sole=[944,952]);g['joint_interval_limit']='External contour bend intervals, NOT calibrated internal joint pivots. Native rig axes are separate context. Match pose before changing limb lengths.';g['status']='FULLBODY_SCAFFOLD_GATE; NO GLOBAL FIT OR BODY/HEAD CHANGE';g['supplements']='Upper-body8views and corrected E/F remain qualitative only. Original v06 controls quantitative bounds.'
(O/'guide-data-sourcepose.json').write_text(json.dumps(g,indent=2)+'\n',encoding='utf-8')
# Canonical editing pose is the exact native frame1 low-A. Source section
# station coordinates are converted to limb-local t and rotated radial planes.
# Existing segment lengths are preserved for this POSE REGISTRATION gate;
# source global joint/length intervals remain separately unresolved constraints.
transport=[]
def align(a,b):
    a=np.asarray(a,float);b=np.asarray(b,float);a/=np.linalg.norm(a);b/=np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b)
    if np.linalg.norm(v)<1e-10:return np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K/(1+c)
posed=rest['pose_endpoints_world'];mappers={}
for side,sign in [('R',-1),('L',1)]:
    def axis(part):return np.asarray(posed['J_Bip_'+side+'_'+part]['head']),np.asarray(posed['J_Bip_'+side+'_'+part]['tail'])
    def getcenter(name):
        c=next(c for c in g['curves'] if c['name']==name);r=np.asarray(c['points']);return np.array([r[:,0].mean(),(r[:,1].min()+r[:,1].max())/2,r[0,2]])
    shoulder,elbow=axis('UpperArm');_,wrist=axis('LowerArm');shift=np.array([sign*.015,0,-.012]);targetS=shoulder+shift;targetE=elbow+shift;targetW=wrist+shift
    sourceS=np.array([sign*.132,.025,Z(235)]);sourceE=getcenter(side+'.arm.section.02');sourceW=getcenter(side+'.arm.section.04')
    handS=sourceW;handE=getcenter(side+'.hand.section.02');boneTip=np.asarray(posed['J_Bip_'+side+'_Middle3_end']['tail']);handAxis=boneTip-wrist;handAxis/=np.linalg.norm(handAxis)
    middle=[i for i,nm in enumerate(groupnames) if nm.startswith('J_Bip_'+side+'_Middle')];midids=np.flatnonzero(bodyW[:,middle].sum(1)>.25);tipLength=float(((q0[midids]-wrist)@handAxis).max());targetHandEnd=targetW+handAxis*tipLength
    hip,knee=axis('UpperLeg');_,ankle=axis('LowerLeg');sourceHip=hip.copy();sourceKnee=getcenter(side+'.leg.section.04');sourceKnee[2]=Z(675);sourceAnkle=getcenter(side+'.leg.section.08')
    def make_segment(s0,s1,t0,t1):
        s0,s1,t0,t1=[np.asarray(q,float) for q in [s0,s1,t0,t1]];us=(s1-s0)/np.linalg.norm(s1-s0);ut=(t1-t0)/np.linalg.norm(t1-t0);R=align(us,ut);lt=np.linalg.norm(t1-t0)
        def fn(p):
            p=np.asarray(p,float);tt=(p[:,2]-s0[2])/(s1[2]-s0[2]);centerline=s0+tt[:,None]*(s1-s0);rad=p-centerline;rad-=(rad@us)[:,None]*us;return t0+tt[:,None]*(t1-t0)+rad@R.T
        transport.append(dict(side=side,source_axis=[s0.tolist(),s1.tolist()],target_axis=[t0.tolist(),t1.tolist()],source_length=float(np.linalg.norm(s1-s0)),canonical_length=float(lt),rotation_matrix=R.tolist(),rule='Limb-local normalized t; radial section projected perpendicular to source axis then rotated to actual frame1 axis. Existing segment length retained; not a shape acceptance.'))
        return fn
    upper=make_segment(sourceS,sourceE,targetS,targetE);fore=make_segment(sourceE,sourceW,targetE,targetW);hand=make_segment(handS,handE,targetW,targetHandEnd);thigh=make_segment(sourceHip,sourceKnee,hip,knee);calf=make_segment(sourceKnee,sourceAnkle,knee,ankle)
    def combine(points,split,top,bottom):
        p0=np.asarray(points,float);out=p0.copy();mask=p0[:,2]>=split;out[mask]=top(p0[mask]);out[~mask]=bottom(p0[~mask]);return out
    # Bind function defaults so each side retains its own axes.
    mappers[side+'.arm']=lambda p,sp=sourceE[2],a=upper,b=fore:combine(p,sp,a,b)
    mappers[side+'.hand']=hand;mappers[side+'.leg']=lambda p,sp=sourceKnee[2],a=thigh,b=calf:combine(p,sp,a,b)
    sourceToe=np.array([sourceAnkle[0]+sign*.047,-.145,Z(947)]);footHead,footTail=axis('Foot');sv=sourceToe[:2]-sourceAnkle[:2];tv=footTail[:2]-footHead[:2];angle=np.arctan2(tv[0],-tv[1])-np.arctan2(sv[0],-sv[1]);Rz=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]]);mapped=Rz@sv;yaw_residual=float(np.arctan2(mapped[0],-mapped[1])-np.arctan2(tv[0],-tv[1]));assert abs(yaw_residual)<1e-10;sole=g['height_registration']['sole_z'];zf=(footHead[2]-sole)/(sourceAnkle[2]-sole)
    def foot(points,s0=sourceAnkle.copy(),t0=footHead.copy(),R=Rz.copy(),zf0=zf):
        q=np.asarray(points,float).copy();q[:,:2]=t0[:2]+(q[:,:2]-s0[:2])@R.T;q[:,2]=t0[2]+(q[:,2]-s0[2])*zf0;return q
    mappers[side+'.foot']=foot;transport.append(dict(side=side,region='foot',rule='Yaw registration to current Foot axis, ankle-to-sole height registration; source turnout is pose, not a foot-width scalar.',yaw_radians=float(angle),mapped_axis_yaw_residual_radians=yaw_residual,height_registration=float(zf)))
for item in g['curves']:
    name=item['name']
    for side in ['R','L']:
        if name==side+'.wrist_hand_link':item['points']=mappers[side+'.hand'](item['points']).tolist()
        elif name==side+'.ankle_foot_link':
            points=np.asarray(item['points']);points[:1]=mappers[side+'.leg'](points[:1]);points[1:]=mappers[side+'.foot'](points[1:]);item['points']=points.tolist()
        elif name.startswith(side+'.shoulder_arm_link.'):
            points=np.asarray(item['points']);points[1:]=mappers[side+'.arm'](points[1:]);item['points']=points.tolist()
        elif name.startswith(side+'.pelvis_fork.'):
            points=np.asarray(item['points']);points[-1:]=mappers[side+'.leg'](points[-1:]);item['points']=points.tolist()
    for prefix,fn in mappers.items():
        if name.startswith(prefix+'.'):item['points']=fn(item['points']).tolist();item['limitation']+=' POSE-REGISTERED in canonical frame1 low-A, source intervals retained separately.';break
for item in g['branch_controlnets']:
    for prefix,fn in mappers.items():
        if item['name'].startswith(prefix+'.'):item['vertices']=fn(item['vertices']).tolist();break
# Conservative hand caps use actual POSED skin geometry, not a virtual bone
# end or all illustrated finger endpoints as simultaneous exact constraints.
for side,sign in [('R',-1),('L',1)]:
    wrist=np.asarray(posed['J_Bip_'+side+'_Hand']['head']);tip=np.asarray(posed['J_Bip_'+side+'_Middle3_end']['tail']);u=tip-wrist;u/=np.linalg.norm(u);v0=np.cross(u,[0,1,0]);v0/=np.linalg.norm(v0);v1=np.cross(u,v0);groups=[i for i,nm in enumerate(groupnames) if nm.startswith('J_Bip_'+side+'_') and any(k in nm for k in ['Hand','Thumb','Index','Middle','Ring','Little'])];ids=np.flatnonzero(bodyW[:,groups].sum(1)>.3);qq=q0[ids];ax=(qq-wrist)@u;maxlen=float(ax.max());radii=[]
    for j,t in enumerate([.3125,.6875,1.]):
        near=qq[abs(ax/maxlen-t)<(.18 if j<2 else .12)];center0=wrist+u*(t*maxlen);rad=near-center0
        rx=max(.004,float(np.max(abs(rad@v0))) if len(rad) else .008);ry=max(.003,float(np.max(abs(rad@v1))) if len(rad) else .008);radii.append([rx,ry])
        item=next(c for c in g['curves'] if c['name']==side+'.hand.section.'+str(j).zfill(2));pts=np.asarray(item['points']);centerline=pts.mean(0);rr=pts-centerline;proposal=np.array([max(abs(rr@v0)),max(abs(rr@v1))]);cap=.75*np.array([rx,ry])+.25*proposal;rr0=rr@v0;rr1=rr@v1;rr=rr0[:,None]*v0*(cap[0]/max(proposal[0],1e-9))+rr1[:,None]*v1*(cap[1]/max(proposal[1],1e-9));item['points']=(centerline+rr).tolist();item['limitation']+=' Hand radial cap75percent actual current posed mesh /25percent uncertain source proposal; distal length uses actual middle-finger skin extent, not bone end.'
    rings=[next(c for c in g['curves'] if c['name']==side+'.hand.section.'+str(j).zfill(2))['points'] for j in range(3)]
    for k in [0,3,6,9]:next(c for c in g['curves'] if c['name']==side+'.hand.rail.'+str(k).zfill(2))['points']=[r[k] for r in rings]
    next(m for m in g['branch_controlnets'] if m['name']==side+'.hand.controlnet')['vertices']=[p0 for r in rings for p0 in r]
    transport.append(dict(side=side,region='hand',fit_source_radial_weight=.25,fit_current_mesh_radial_weight=.75,current_mesh_tip_length_m=maxlen,current_radial_bounds_m=radii,limit='Conservative coarse hand envelope; does not prescribe a hand lengthening or individual finger changes.'))
g['canonical_pose']='Exact current recorded frame1 low-A directions. Provisional widened-shoulder transport15mm/side,-12mmZ remains a source-fit guide hypothesis; current model/rig NOT edited.';g['pose_transport']=transport;g['source_pose_data_file']='guide-data-sourcepose.json';g['pose_registration_limit']='Source section heights are not imposed globally on limbs; normalized limb-local t establishes corresponding stations. Current segment lengths are NOT declared correct. Source projected joint intervals/pose discrepancy remain separate review constraints.'
g['revision']=4;g['revision_note']='Full canonical low-A below-head guide; foot yaw sign analytically corrected, conservative posed-mesh hand caps, trunk/waist/pelvis continuity linked.'
(O/'guide-data.json').write_text(json.dumps(g,indent=2)+'\n',encoding='utf-8');print('FULLBODY_GUIDE_DATA_DONE',len(g['curves']),len(g['branch_controlnets']),len(evidence),flush=True)
