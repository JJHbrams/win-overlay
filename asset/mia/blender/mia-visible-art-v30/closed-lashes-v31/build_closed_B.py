"""Closed-only source-informed temporal lash transport; neutral immutable.

One character-space construction for all views. Existing skin/E/brows/maps stay.
"""
import bpy,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parent;CAN=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=CAN/'asset/mia/blender/mia-visible-art-v30/integrated/brows-C-outer-E/Mia_SourceLook_v31_Review.blend';SHA='c3557e9eaa2163ae0d6f712a8c51362c0a6abdab628bcabe3e9673511323813c';assert hashlib.sha256(N.read_bytes()).hexdigest()==SHA
sys.path.insert(0,str(P.parent/'mia-eye-lash-v29'));from audit_mesh_helpers import snapshot
bo,_,bm,bi=snapshot(N);master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;kn=[k.name for k in keys];closed_i=kn.index('Face.M_F00_000_00_Fcl_EYE_Close');meta=json.loads((P.parent/'mia-eye-visible-v30/lash-M-audit.json').read_text());rimmeta=json.loads((CAN/'asset/mia/blender/mia-face-finish-v29/parts/medial-C2/proof/medial-baseline-inspection.json').read_text());infos=[d for d in meta['created'] if 'Upper' in d['owner']];names=[d['owner'] for d in infos];before={n:np.array([[v.co[:] for v in k.data] for k in bpy.data.objects[n].data.shape_keys.key_blocks]) for n in names};raw={n:np.array([v.co[:] for v in bpy.data.objects[n].data.vertices]) for n in names};after={n:a.copy() for n,a in before.items()}
def unit(v):return v/max(np.linalg.norm(v),1e-12)
def interp(c,t):return np.array([np.interp(t,np.linspace(0,1,len(c)),c[:,j]) for j in range(3)])
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
states={}
for label,idx in [('neutral',0),('closed',closed_i)]:
    for k in keys:k.value=1 if idx and k==keys[idx] else 0
    bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();q=np.array([ev.matrix_world@v.co for v in me.vertices]);norm=np.array([ev.matrix_world.to_3x3()@v.normal for v in me.vertices]);bv=BVHTree.FromPolygons(q,[list(f.vertices) for f in me.polygons]);states[label]={'q':q,'norm':norm,'bv':bv};ev.to_mesh_clear()
reports=[];max_contact=0.;source_ref=CAN/'asset/mia/references/mia-expression-style-confirmed-20261031.png'
for info in infos:
    name=info['owner'];side=int(name.rsplit('_',1)[1]);ids=rimmeta['evaluated_openings'][str(side)]['upper_evaluated_indices'];curve0=states['neutral']['q'][ids];curveC=states['closed']['q'][ids];normC=states['closed']['norm'][ids];q0=before[name][0];old=before[name][closed_i];new=old.copy()
    for station in info['station_bindings']:
        # A shortened onlytheterminalwing but left thecentral closed fan's
        # broad anterior U-sheet. B rebuilds thewhole attached closed fringe,
        # retaining the nasal Ipoint and every neutral/nonclosed coordinate.
        t=station['t'];g=float(smooth((t-.08)/.12))
        if g==0:continue
        vi=np.array(station['vertex_indices']);p0=q0[vi].reshape(-1,2,3);pC=old[vi].reshape(-1,2,3);c0=p0.mean(1);cC=pC.mean(1);r0=interp(curve0,t);rC=interp(curveC,t)
        nn=unit(interp(normC,t));probe=states['closed']['bv'].ray_cast(Vector((rC[0],-.20,rC[2]+.00065)),Vector((0,1,0)))
        if probe[0] is not None and probe[1].y<-.05:nn=unit(np.array(probe[1]))
        if nn[1]>0:nn=-nn
        # Head-space outward/down axis is projected onto actual socket skin.
        # It does not inherit the degenerate closed short-turn tangent.
        desired=unit(np.array([side,0.,-.20]));T=unit(desired-nn*(desired@nn));U=unit(side*np.cross(nn,T))
        if U[2]<0:U=-U
        if station['attached']:
            anchor0=c0[0];anchorC=cC[0]
        else:anchor0=r0;anchorC=rC
        d=c0-anchor0;dx=d[:,0]*side;dz=d[:,2];anterior=-d[:,1]
        target=anchorC+dx[:,None]*T*.75+dz[:,None]*U*.35+anterior[:,None]*nn*.30
        centres=cC*(1-g)+target*g
        oldvec=pC[:,0]-pC[:,1];thickness=np.linalg.norm(oldvec,axis=1);vec=oldvec*(1-g)+nn[None,:]*thickness[:,None]*g;vec=vec/np.maximum(np.linalg.norm(vec,axis=1)[:,None],1e-12)*thickness[:,None]
        pair=np.stack([centres+vec/2,centres-vec/2],1)
        # Actual forward skin envelope, paired translation, not a camera fit.
        shifts=[]
        for row in range(len(pair)):
            if station['attached'] and row==0:continue
            front=pair[row,0];centre=pair[row].mean(0);dy=0.
            for qp,clearance in [(front,.00013),(centre,.000075)]:
                h=states['closed']['bv'].ray_cast(Vector((qp[0],-.20,qp[2])),Vector((0,1,0)))
                if h[0] is not None and h[1].y<-.05:dy=min(dy,h[0].y-clearance-qp[1])
            if dy<0:
                assert -dy<.005,(name,station['t'],row,dy)
                pair[row,:,1]+=dy;max_contact=max(max_contact,-dy)
            shifts.append(dy*1000)
        if station['attached']:
            assert np.linalg.norm(pair[0].mean(0)-cC[0])<1e-10
        new[vi]=pair.reshape(-1,3)
        reports.append({'owner':name,'station_t':t,'attached':station['attached'],'blend':g,'target_outward_tangent':T.tolist(),'skin_normal':nn.tolist(),'maximum_coordinate_change_mm':float(np.linalg.norm(new[vi]-old[vi],axis=1).max()*1000),'paired_forward_contact_shifts_mm':shifts})
    affected=[closed_i,kn.index('Face.M_F00_000_00_Fcl_EYE_Close_'+('R' if side<0 else 'L'))]
    for idx in affected:after[name][idx]=new
    ob=bpy.data.objects[name]
    for idx in affected:ob.data.shape_keys.key_blocks[idx].data.foreach_set('co',new.ravel())
    ob.data.update()
for k in keys:k.value=0
bpy.context.view_layer.update();out=P/'Mia_LashPose_v31_B.blend';assert not out.exists();bpy.ops.wm.save_as_mainfile(filepath=str(out));ao,_,am,ai=snapshot(out)
checks={'all_nonupper_mesh_records_exact':all(bo[n]==ao[n] for n in bo if n not in names),'all_upper_noncoordinate_fields_exact':all(all(bo[n][k]==ao[n][k] for k in bo[n] if k!='coordinates') for n in names),'all_material_graphs_exact':bm==am,'all_images_maps_exact':bi==ai,'source_native_immutable':hashlib.sha256(N.read_bytes()).hexdigest()==SHA}
for n in names:
    side=int(n.rsplit('_',1)[1]);allowed=[closed_i,kn.index('Face.M_F00_000_00_Fcl_EYE_Close_'+('R' if side<0 else 'L'))];ob=bpy.data.objects[n];q=np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks]);checks[n+'_neutral_raw_exact']=np.array_equal(raw[n],np.array([v.co[:] for v in ob.data.vertices]));checks[n+'_all_nontarget_keys_exact']=all(np.array_equal(before[n][i],q[i]) for i in range(42) if i not in allowed)
assert all(checks.values()),checks
np.savez_compressed(P/'upper-B-coordinates.npz',**{n:a.astype(np.float32) for n,a in after.items()})
report={'input':str(N),'input_sha256':SHA,'native':str(out),'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':checks,'source_expression_sheet':str(source_ref),'source_expression_sheet_sha256':hashlib.sha256(source_ref.read_bytes()).hexdigest(),'source_panel':'02; nearlyclosed eyes, source hidespartsunderbangs; guidesfinishnot exactfullyclosedanatomy','parameters':{'whole_fan_blend_start':.08,'full_blend_by':.20,'outward_closed_length_factor':.75,'closed_crossfringe_width_factor':.35,'normal_offset_factor':.30,'outward_headspace_slopeZ':-.20},'maximum_forward_contact_reseat_mm':max_contact*1000,'station_records':reports,'method':'Closedkeysonly: wholeattachedfringe andtemporalwing solidsections mappedfrom unchangedneutral design toclosedactualskin tangentframe withsideward/downlongaxis. Nasalpointheld; no shortturntangentinheritance. Attachedrootcentres exact; pairedthickness preserved. Actualskin-enveloperecontactmovespairedfront/backtogether. Bilateral andmatchingunilateral endpointarrayssame. Neutral/allnonclosedkeys/Ewall/ocular/body/brows/mapsunchanged.','pending':'SmallactualGPUsource02/before/Bfront/profile/grazingfullandHalf, manifold/volume/contactthroughglobalandunilateral interpolation. BnotartPASSfromnumbers.'}
(P/'closed-B-build.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('CLOSED_B_SAVED',report['sha256'],checks,'maxcontactmm',max_contact*1000)
