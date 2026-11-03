"""One roof-only RAM fit; profile placement belongs to a fresh neck loft.

Neutral new seed, five common shape variables and one camera pair per panel.
No profile edge is silently accepted: previous failed constraints are preserved
in solve1-stopped.json. No mesh/GPU/native/bake or input copy here.
"""
from pathlib import Path
import sys,json,time,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from field_numpy import Model
from ram_fit import Projection,GUIDE_CUT
from diagnostics import analyze
C=Path(__file__).resolve().parents[3];A=C/'asset/mia/blender/mia-fit-v003';CACHE=C/'.mia-cache/body-h/shape'
LO=np.array([.15,.15,0.,0.,.8,-4.,-6.,176.,-6.]);HI=np.array([1.,1.,.08,.06,1.,4.,6.,184.,6.]);NEUTRAL=np.array([1.,1.,0.,0.,1.,0.,0.,180.,0.]);X0=(NEUTRAL-LO)/(HI-LO)
NAMES=['cap_scale','trap_scale','RXshift_m','RYshift_m','fan_scale','front_yaw','front_pitch','back_yaw','back_pitch']
REG=.05

def cap_field(model,params,q):return np.maximum(model.evaluate(q,params),q[:,2]-GUIDE_CUT)

def tangent_refinement(proj,u,z,diag):
    """Refine F=0 and F_depth=0 on each already bracketed highest branch."""
    z=z.copy();d=diag['depth'].copy();valid=np.isfinite(z)&~diag['guidecut_active'];h=1e-5;h2=2e-4;largest=0.
    for _ in range(9):
        p=proj.points(u,z,d);F=cap_field(proj.model,proj.params,p);vp=cap_field(proj.model,proj.params,p+h*proj.up);vm=cap_field(proj.model,proj.params,p-h*proj.up);dp=cap_field(proj.model,proj.params,p+h*proj.depth);dm=cap_field(proj.model,proj.params,p-h*proj.depth);Fv=(vp-vm)/(2*h);Fd=(dp-dm)/(2*h)
        ddp=cap_field(proj.model,proj.params,p+h2*proj.depth);ddm=cap_field(proj.model,proj.params,p-h2*proj.depth);Fdd=(ddp-2*F+ddm)/(h2*h2)
        pp=cap_field(proj.model,proj.params,p+h2*(proj.up+proj.depth));pm=cap_field(proj.model,proj.params,p+h2*(proj.up-proj.depth));mp=cap_field(proj.model,proj.params,p+h2*(-proj.up+proj.depth));mm=cap_field(proj.model,proj.params,p-h2*(proj.up+proj.depth));Fvd=(pp-pm-mp+mm)/(4*h2*h2);det=Fv*Fdd-Fd*Fvd;ok=valid&(abs(det)>1e-8)&(Fdd>0)&(Fv>0)
        dz=np.zeros(len(z));dd=np.zeros(len(z));dz[ok]=(-F[ok]*Fdd[ok]+Fd[ok]**2)/det[ok];dd[ok]=(-Fv[ok]*Fd[ok]+F[ok]*Fvd[ok])/det[ok];dz=np.clip(dz,-.002,.002);dd=np.clip(dd,-.004,.004);z+=dz;d=np.clip(d+dd,-.25,.25);largest=max(largest,float(np.max(abs(dz))));valid&=ok
    p=proj.points(u,z,d);F=cap_field(proj.model,proj.params,p);Fd=(cap_field(proj.model,proj.params,p+h*proj.depth)-cap_field(proj.model,proj.params,p-h*proj.depth))/(2*h)
    return z,dict(converged=int((valid&(abs(F)<1e-7)&(abs(Fd)<1e-4)).sum()),total=len(z),excluded_guidecut=int(diag['guidecut_active'].sum()),max_abs_field_value_not_distance=float(np.max(abs(F))),max_abs_depth_derivative=float(np.max(abs(Fd))),max_single_newton_Z_step_m=largest,max_change_from_dense_roof_m=float(np.nanmax(abs(z-diag['initial_z']))),world_points=p.tolist())

class RoofProblem:
    def __init__(self):
        self.model=Model();self.start=time.time();self.calls=0;self.rails=json.loads((A/'body/shoulder11/source-rails.json').read_text(encoding='utf-8'));r=self.rails['registration'];self.sigma=2*r['metres_per_pixel'];self.panels={}
        for name,points in self.rails['traces_original_pixels'].items():
            panel='back' if name.startswith('back') else'front';axis=935 if panel=='back' else 239
            for px,py in points:
                if abs(px-axis)*r['metres_per_pixel']<.05:continue
                self.panels.setdefault(panel,[]).append(dict(panel=panel,path=name,pixel=[px,py],u=(px-axis)*r['metres_per_pixel'],z=(r['zero_world_z_pixel']-py)*r['metres_per_pixel']))
    def geometry(self,x,quality=0,record=False):
        self.calls+=1
        if (CACHE/'STOP_ROOF_FIT').exists():raise InterruptedError('Root stop request; no further evaluations')
        p=LO+x*(HI-LO);raw=[];details=[];proof=[];offset=np.linspace(-self.sigma,self.sigma,3 if quality==0 else 9)
        for panel,j in [('front',5),('back',7)]:
            proj=Projection(self.model,p[:5],p[j],p[j+1],quality);obs=self.panels[panel];u=np.array([q['u'] for q in obs]);target=np.array([q['z'] for q in obs]);uu=(u[:,None]+offset[None,:]).ravel();z,diag=proj.roof(uu)
            if quality:
                diag['initial_z']=z.copy();z,pr=tangent_refinement(proj,uu,z,diag);pr['panel']=panel;proof.append(pr)
            z=z.reshape(len(obs),-1);low=np.nanmin(z,axis=1);high=np.nanmax(z,axis=1);missing=~np.isfinite(low);low[missing]=1.15;high[missing]=1.15;above=np.maximum(low-target-self.sigma,0)/self.sigma;below=np.maximum(target-self.sigma-high,0)/self.sigma;raw.extend(above);raw.extend(below)
            if record:
                for k,q in enumerate(obs):details.append(dict(**q,model_roof_range_Z=[float(low[k]),float(high[k])],above_interval_m=float(above[k]*self.sigma),below_interval_m=float(below[k]*self.sigma),no_hit=bool(missing[k])))
        raw=np.array(raw);assert np.isfinite(raw).all();return raw,details,proof,p
    def residual(self,x):
        raw,_,_,_=self.geometry(x)
        # Fixed robust soft-L1 transform; both sides are retained. This is a
        # compromise objective when illustrated intervals are incompatible.
        robust=np.sqrt(2*(np.sqrt(1+raw*raw)-1));regularization=REG*(x-X0)
        return np.r_[robust,regularization],raw

def fit(problem):
    x=X0.copy();r,geo=problem.residual(x);initial=geo.copy();cost=float(r@r);lam=.1;history=[];reason='24_iteration_limit';last_rank=0
    for it in range(24):
        if time.time()-problem.start>174:reason='180_second_budget';break
        J=np.zeros((len(r),len(x)));h=.01
        for k in range(len(x)):
            if time.time()-problem.start>178:reason='180_second_budget';break
            q=x.copy();q[k]=x[k]+h if x[k]<=1-h else x[k]-h;rr,_=problem.residual(q);J[:,k]=(rr-r)/(q[k]-x[k])
        if reason=='180_second_budget':break
        sv=np.linalg.svd(J[:-len(x)],compute_uv=False);rank=int((sv>max(sv[0]*1e-6,1e-8)).sum());last_rank=rank;accepted=False;step=0.
        for _ in range(4):
            D=np.maximum(np.sum(J*J,axis=0),1.);delta=np.linalg.solve(J.T@J+lam*np.diag(D),-J.T@r);n=np.linalg.norm(delta)
            if n>.5:delta*=.5/n
            q=np.clip(x+delta,0,1);rr,g=problem.residual(q);newcost=float(rr@rr);step=float(np.linalg.norm(q-x))
            if newcost<cost-1e-10:x=q;r=rr;geo=g;cost=newcost;lam=max(lam/3,1e-6);accepted=True;break
            lam*=10
        row=dict(iteration=it,cost_with_robust_and_regularizer=cost,max_geometric_interval_violation_mm=float(geo.max()*problem.sigma*1000),geometric_rank=rank,regularized_rank=len(x),accepted=accepted,stepnorm=step,params=(LO+x*(HI-LO)).tolist(),seconds=time.time()-problem.start,evaluations=problem.calls);history.append(row);print('H_ROOF_ITER',json.dumps(row),flush=True)
        (CACHE/'roof-fit-progress.json').write_text(json.dumps(dict(status='RUNNING_UNSELECTED',history=history,latest=row),indent=2)+'\n',encoding='utf-8',newline='\n')
        if not accepted:reason='no_meaningful_progress';break
        if step<1e-4:reason='small_step';break
        if geo.max()<.02:reason='coarse_interval_feasibility';break
    return x,initial,history,reason,last_rank

def main():
    path=A/'integration/workspace-storage-20261103/storage_guard.py';s=importlib.util.spec_from_file_location('H_roof_capacity',path);guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard);capacity=guard.inspect(10*1024*1024)
    if capacity['violations']:raise RuntimeError(json.dumps(capacity))
    out=CACHE/'roof-fit.json';assert not out.exists(),'One bounded roof fit only, never overwrite';problem=RoofProblem();x,initial,history,reason,rank=fit(problem)
    print('H_ROOF_FINAL_TRUE_ENVELOPE_BEGIN',flush=True);raw,observations,tangent,p=problem.geometry(x,quality=1,record=True);diagnostics=analyze(problem.model,p[:5],C)
    above=np.array([q['above_interval_m'] for q in observations]);below=np.array([q['below_interval_m'] for q in observations]);violations=above+below
    report=dict(status='RAM_ROOF_ONLY_UNSELECTED_NOT_ART',stop_reason=reason,parameter_names=NAMES,params=p.tolist(),bounds=[LO.tolist(),HI.tolist()],neutral_seed=NEUTRAL.tolist(),source33_count=len(observations),source_interval_inequalities=66,initial_max_violation_mm=float(initial.max()*problem.sigma*1000),final_max_violation_mm=float(violations.max()*1000),final_median_violation_mm=float(np.median(violations)*1000),final_violated_observation_count=int((violations>1e-5).sum()),observations=observations,shared_camera_parameters={'front':p[5:7].tolist(),'back':p[7:9].tolist()},geometric_rank=rank,robust_objective='softL1 geometric interval hinges, fixed; no HALF or uncertainty expansion',neutral_regularizer=dict(weight=REG,normalized_distance=float(np.linalg.norm(x-X0)),meaning='Fixed small neutral penalty to resolve roof-unobservable modes, separate from reported geometric interval errors'),history=history,source_registration=problem.rails['registration'],source_hash=problem.rails['sha256'],source_uncertainty='Same2pxboxinBOTHaxes +declaredsharedcamera bounds; no perpoint camera/translation',profile_status='FULLPROFILEEDGECONSTRAINTSDEFERREDTOFRESHNECKLOFTBYROOT; previousfailedrunpreserved, no globalCY/headmove; this is not a profile fit',model=problem.model.metadata(p[:5]),bound_hits=[NAMES[i] for i in range(len(p)) if min(abs(p[i]-LO[i]),abs(p[i]-HI[i]))<1e-7],tangent_verification=tangent,physical_diagnostics=diagnostics,numeric_limits='Dense depth sampling/parabolic bracket then F=0/Fdepth=0Newton refinement; no finite mesh/native exists. Branch/cut flags and numerical root residuals are not ART acceptance.',capacity=capacity,mesh_created=False,GPU_used=False,native_saved=False,baked=False,inputs_copied=False)
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');print('H_ROOF_FIT_READY',str(out),out.stat().st_size,'max_mm',report['final_max_violation_mm'],flush=True)

if __name__=='__main__':main()
