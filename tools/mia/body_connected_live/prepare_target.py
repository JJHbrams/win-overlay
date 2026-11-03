"""One broad source-guided design proposal on the connected original cage.

Front reference uses ordered meridian arc length, not height correspondence;
shoulder reference uses source roof observations, not failed H cap geometry.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from scope import load_scope,ROOT,BODY,CACHE
from meridians import Sections

smooth=lambda t:(t:=np.clip(t,0.,1.))**3*(10-15*t+6*t*t)


def main():
    s=load_scope();q0=s['q'];N=len(q0);selected=s['selected'];free=np.zeros(N,bool);free[selected]=True
    baseline=dict(np.load(BODY/'current-body-limit.npz'))
    guide_path=ROOT/'.mia-cache/body-h/shape/H-guide.npz';guide=dict(np.load(guide_path))
    raw=Sections(q0,s['topology']['triangles']);evaluated=Sections(baseline['world'],baseline['triangles']);supported=Sections(guide['world'],guide['triangles'])
    angles=np.linspace(-.98,.98,29)+1.01e-5
    oldraw=[];oldeval=[];target=[]
    for i,angle in enumerate(angles):
        oldraw.append(raw.front(angle));oldeval.append(evaluated.front(angle));target.append(supported.front(angle))
        print('MERIDIAN',i,flush=True)
    oldraw=np.array(oldraw);oldeval=np.array(oldeval);target=np.array(target)
    theta=np.arctan2(q0[:,0],-q0[:,1]);delta_observed=np.zeros_like(q0);observation=np.zeros((N,3))
    front_ids=selected[(abs(theta[selected])<.95)&(q0[selected,2]>1.115)&(q0[selected,2]<1.355)&(q0[selected,1]<-.02)]
    for vi in front_ids:
        i=int(np.clip(np.searchsorted(angles,theta[vi])-1,0,len(angles)-2));t=(theta[vi]-angles[i])/(angles[i+1]-angles[i])
        curve=(1-t)*oldraw[i]+t*oldraw[i+1]
        # Ordered same-front-meridian segment correspondence cannot jump to
        # the opposite axillary wall or replace a real under-bowl by Y(Z).
        a,b=curve[:-1],curve[1:];d=b-a
        u=np.clip(np.sum((q0[vi]-a)*d,axis=1)/np.maximum(np.sum(d*d,axis=1),1e-20),0,1)
        j=int(np.argmin(np.linalg.norm(a+u[:,None]*d-q0[vi],axis=1)));h=u[j]
        old=(1-t)*oldeval[i]+t*oldeval[i+1];new=(1-t)*target[i]+t*target[i+1]
        delta_observed[vi]=(1-h)*(new[j]-old[j])+h*(new[j+1]-old[j+1])
        confidence=smooth((q0[vi,2]-1.115)/.025)*smooth((1.355-q0[vi,2])/.015)*smooth((.95-abs(theta[vi]))/.15)
        observation[vi]=16*confidence
    # Broad source skin-roof correspondence, with one shared local width
    # hypothesis supported by SOURCE_GATE_C's two independent ~14–15% spans.
    # Target Z comes from original source observations, not the cap mesh.
    roof=json.loads((ROOT/'.mia-cache/body-h/shape/roof-fit.json').read_text())['observations']
    ux=np.array([abs(x['u'])for x in roof]);zz=np.array([x['z']for x in roof])
    roof_ids=[]
    for vi in selected:
        x=abs(q0[vi,0])
        if not .045<x<.145 or q0[vi,2]<1.35:continue
        neighbors=selected[(abs(abs(q0[selected,0])-x)<.009)&(q0[selected,2]>1.32)]
        if q0[vi,2]<q0[neighbors,2].max()-.007:continue
        tx=x*1.15
        nearby=np.argsort(abs(ux-tx))[:4]
        tz=float(np.median(zz[nearby]))
        delta_observed[vi,0]=np.sign(q0[vi,0])*tx-q0[vi,0]
        delta_observed[vi,2]=tz-q0[vi,2]
        observation[vi,[0,2]]=16;roof_ids.append(int(vi))
    # Whole connected intrinsic bi-Laplacian interpolation. No ambient
    # Gaussian, old06 interior coordinates, or hard small-patch exterior rows.
    edges=s['edges'];a,b=edges.T
    ew=1/np.maximum(np.linalg.norm(q0[a]-q0[b],axis=1),.006)
    degree=np.bincount(np.r_[a,b],weights=np.r_[ew,ew],minlength=N)
    inv=1/np.sqrt(np.maximum(degree,1e-12));ww=ew*inv[a]*inv[b]
    def L(x):
        result=x.copy()
        for k in range(3):
            result[:,k]-=np.bincount(a,weights=ww*x[b,k],minlength=N)+np.bincount(b,weights=ww*x[a,k],minlength=N)
        return result
    rhs=observation*delta_observed
    def A(x):
        y=L(L(x))+observation*x;y[~free]=0.;return y
    diag=1+np.bincount(np.r_[a,b],weights=np.r_[ww*ww,ww*ww],minlength=N)
    diag=diag[:,None]+observation
    x=np.zeros_like(q0);r=rhs.copy();r[~free]=0.;z=r/diag;p=z.copy();rz=np.sum(r*z,axis=0);initial=np.linalg.norm(r,axis=0)
    for iteration in range(2000):
        Ap=A(p);den=np.sum(p*Ap,axis=0);alpha=np.divide(rz,den,out=np.zeros(3),where=abs(den)>1e-30)
        x+=p*alpha;r-=Ap*alpha;new=np.sum(r*r,axis=0)
        if np.max(np.sqrt(new)/np.maximum(initial,1e-20))<1e-7:break
        z=r/diag;next_rz=np.sum(r*z,axis=0)
        p=z+p*np.divide(next_rz,rz,out=np.zeros(3),where=abs(rz)>1e-30);rz=next_rz
    else:raise RuntimeError('One connected solve did not converge; no tuning candidate produced')
    q=q0+x
    # Source graphic cues locate a weak anatomical construction hypothesis,
    # not exact bones or engraved lines. Broad ridge/fossa amplitudes are
    # deliberately small; maps and final light response remain separate.
    paths=json.loads((ROOT/'asset/mia/blender/mia-fit-v003/underwear-source/source-paths.json').read_text())['paths']
    curves=[np.array(row['points_px'],float)for row in paths if row['id'].startswith('front.neck.')]
    mpp=.001845870535714286;z0=971.9137795513633
    curve=np.vstack([np.column_stack([(p[:,0]-239)*mpp,(z0-p[:,1])*mpp])for p in curves])
    p=q[:,[0,2]];distance=np.min(np.linalg.norm(p[:,None]-curve[None],axis=2),axis=1)
    upper_curve=curve.copy();upper_curve[:,1]+=.012
    fossa=np.min(np.linalg.norm(p[:,None]-upper_curve[None],axis=2),axis=1)
    notch=np.sqrt((q[:,0]/.016)**2+((q[:,2]-1.3788)/.020)**2)
    anterior=smooth((-.008-q[:,1])/.022)*smooth((.14-abs(q[:,0]))/.025)
    feature=(-.0012*smooth((.014-distance)/.014)+.0018*smooth((.018-fossa)/.018)+.0025*smooth(1-notch))*anterior
    feature[~free]=0.;q[:,1]+=feature
    q[~free]=q0[~free]
    local_delta=np.einsum('nij,nj->ni',s['mapping']['local_from_world'],q-q0)
    local=s['mapping']['control_local']+local_delta
    posed_local=(q-s['mapping']['matrix_world'][:3,3])@np.linalg.inv(s['mapping']['matrix_world'][:3,:3]).T
    assert np.array_equal(q[~free],q0[~free]) and np.isfinite(q).all()
    assert np.linalg.norm(q-q0,axis=1).max()<.10
    out=CACHE/'proposal.npz'
    assert not out.exists(),'Never overwrite this single design proposal'
    np.savez_compressed(out,baseline_world=q0,target_world=q,target_posed_local=posed_local.astype(np.float32),
        additive_local_delta=local_delta.astype(np.float32),original_control_local=s['mapping']['control_local'],
        selected=selected,protected=s['protected'],front_ids=front_ids,roof_ids=np.array(roof_ids),
        observation=observation,observation_delta=delta_observed,clavicle_feature=feature,
        meridian_angles=angles,meridian_original_raw=oldraw,meridian_original_eval=oldeval,meridian_supported_target=target)
    report=dict(scope='ONE broad connected original-cage DESIGN proposal, not production migration',
        selected_controls=len(selected),front_meridian_observations=len(front_ids),roof_observations=len(roof_ids),
        meridian_method='29 ordered same-front half-plane paths, top->pole->lowerroot arc-length; old control/limit offset retained',
        supported_guide=dict(path=str(guide_path),sha256=hashlib.sha256(guide_path.read_bytes()).hexdigest(),used_region='Front supported envelope onlyZ1.11..1.355/azimuth±.95; NO H cap/leaf or neck'),
        source_roof_method='Original source33skinroof observations + provisional local1.15width from SOURCE_GATE_C; not an art acceptance',
        connected_solver=dict(iterations=iteration+1,relative_residual=(np.sqrt(new)/np.maximum(initial,1e-20)).tolist()),
        maximum_control_move_mm=float(np.linalg.norm(q-q0,axis=1).max()*1000),
        maximum_clavicle_ridge_fossa_adjustment_mm=float(abs(feature).max()*1000),
        clavicle_limit='Graphic cues only place broad1.2mmridge/1.8mmfossa/2.5mmnotch construction; not exact bones/ink-anchor reuse or etched groove',
        all_protected_controls_exact=True,original47_UV_weights_drivers_unmodified=True,
        armature_inverse_only=True,post_subsurf_head_surface_and_sheet_strain='UNVERIFIED until actual evaluation',
        proposal_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),live_applied=False,native_saved=False,ART=False)
    (CACHE/'proposal.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report),flush=True)


if __name__=='__main__':main()
