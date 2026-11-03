"""ONE bounded five-shape/shared-panel-pose RAM interval solve.

Direct projected zero envelopes, not field-value distances. No SciPy/install,
parameter grid, mesh, Blender, GPU, native, bake or immutable input copy.
"""
from pathlib import Path
import sys,json,time,hashlib,importlib.util
import numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from field_numpy import Model
CANONICAL=Path('D:/MiaWorkCache/mia-reference-work/win-overlay')
ASSET=CANONICAL/'asset/mia/blender/mia-fit-v003'
TARGET=np.array([0.,-.018,.86]);GUIDE_CUT=1.445
LOW=np.array([.15,.15,0.,0.,.8,-4.,-6.,176.,-6.,77.,-6.])
HIGH=np.array([1.,1.,.08,.06,1.,4.,6.,184.,6.,93.,6.])
NAMES=['cap_scale','trap_scale','RXshift_m','RYshift_m','fan_scale','front_yaw','front_pitch','back_yaw','back_pitch','profile_yaw','profile_pitch']
STOP_FILE=CANONICAL/'.mia-cache/body-h/shape/STOP_SOLVE1'

class Projection:
    def __init__(self,model,params,yaw,pitch,quality=0):
        self.model=model;self.params=params;self.quality=quality
        a,b=np.radians([yaw,pitch]);ca,sa,cb,sb=np.cos(a),np.sin(a),np.cos(b),np.sin(b)
        self.right=np.array([ca,sa,0.]);self.up=np.array([-sa*sb,ca*sb,cb]);self.depth=np.array([sa*cb,-ca*cb,sb]);self.ds=np.linspace(-.25,.25,31 if quality==0 else 121)
    def points(self,u,z,d):
        return TARGET+np.asarray(u)[...,None]*self.right+(np.asarray(z)-TARGET[2])[...,None]*self.up+np.asarray(d)[...,None]*self.depth
    def min_depth(self,u,z,details=False):
        u=np.asarray(u).ravel();z=np.asarray(z).ravel();q=self.points(u[:,None],z[:,None],self.ds[None,:]);f=self.model.evaluate(q.reshape(-1,3),self.params).reshape(len(u),-1)
        # Mathematical upper guide cut only; no final loft/head is claimed.
        f=np.maximum(f,q[:,:,2]-GUIDE_CUT);j=np.argmin(f,axis=1);ii=np.arange(len(u));v=f[ii,j];jm=np.maximum(j-1,0);jp=np.minimum(j+1,len(self.ds)-1);den=f[ii,jm]-2*v+f[ii,jp];off=np.zeros(len(u));ok=(j>0)&(j<len(self.ds)-1)&(den>1e-15);off[ok]=np.clip(.5*(f[ii[ok],jm[ok]]-f[ii[ok],jp[ok]])/den[ok],-1.,1.)
        d=self.ds[j]+off*(self.ds[1]-self.ds[0]);point=self.points(u,z,d);fine=np.maximum(self.model.evaluate(point,self.params),point[:,2]-GUIDE_CUT);use=fine<v;v=np.minimum(v,fine);d=np.where(use,d,self.ds[j]);point=self.points(u,z,d)
        return (v,d,point) if details else v
    def roof(self,u):
        u=np.asarray(u).ravel();zz=np.linspace(1.15,1.49,43 if self.quality==0 else 97);qU=np.repeat(u,len(zz));qZ=np.tile(zz,len(u));f=self.min_depth(qU,qZ).reshape(len(u),-1);cross=(f[:,:-1]<=0)&(f[:,1:]>=0);valid=cross.any(1);j=np.maximum(np.where(cross,np.arange(len(zz)-1),-1).max(1),0);lo=zz[j];hi=zz[j+1]
        for _ in range(12 if self.quality==0 else 24):
            mid=(lo+hi)/2;v=self.min_depth(u,mid);lo=np.where(v<=0,mid,lo);hi=np.where(v>0,mid,hi)
        z=(lo+hi)/2;v,d,point=self.min_depth(u,z,True);z[~valid]=np.nan
        return z,dict(field_residual=v,depth=d,world=point,valid=valid,guidecut_active=abs(point[:,2]-GUIDE_CUT)<2e-5)
    def sides(self,z):
        z=np.asarray(z).ravel();uu=np.linspace(-.14,.16,65 if self.quality==0 else 161);F=self.min_depth(np.tile(uu,len(z)),np.repeat(z,len(uu))).reshape(len(z),-1);inside=F<=0;valid=inside.any(1);first=np.argmax(inside,axis=1);last=len(uu)-1-np.argmax(inside[:,::-1],axis=1);output=[]
        for left in [True,False]:
            j=np.maximum(first-1,0) if left else np.minimum(last,len(uu)-2);lo=uu[j];hi=uu[j+1]
            for _ in range(12 if self.quality==0 else 24):
                mid=(lo+hi)/2;v=self.min_depth(mid,z)
                if left:lo=np.where(v>0,mid,lo);hi=np.where(v<=0,mid,hi)
                else:lo=np.where(v<=0,mid,lo);hi=np.where(v>0,mid,hi)
            u=(lo+hi)/2;u[~valid]=np.nan;output.append(u)
        return output[0],output[1]

class Problem:
    def __init__(self,model):
        self.model=model;self.calls=0;self.start=time.time();self.best=None;self.history=[]
        path=ASSET/'body/shoulder11/source-rails.json';r=json.loads(path.read_text(encoding='utf-8'));self.rails=r;self.mpp=r['registration']['metres_per_pixel'];self.sigma=2*self.mpp;zero=r['registration']['zero_world_z_pixel'];self.panels={};self.observations=[]
        for name,pts in r['traces_original_pixels'].items():
            panel='back' if name.startswith('back') else'front';axis=935 if panel=='back' else 239
            for px,py in pts:
                if abs(px-axis)*self.mpp<.05:continue
                rec=dict(panel=panel,path=name,pixel=[px,py],u=(px-axis)*self.mpp,z=(zero-py)*self.mpp);self.observations.append(rec);self.panels.setdefault(panel,[]).append(rec)
        self.profile=[dict(pixel_y=py,left_pixel=left,right_pixel=right,z=(zero-py)*self.mpp,left=(left-568)*self.mpp,right=(right-568)*self.mpp) for py,left,right in [[195,574,615],[205,576,618],[215,574,623]]]
    def evaluate(self,x,quality=0,record=False):
        if STOP_FILE.exists():raise InterruptedError('Root stop marker present; no further fit evaluation')
        self.calls+=1;physical=LOW+np.asarray(x)*(HIGH-LOW);params=physical[:5];res=[];details=[];step=np.linspace(-self.sigma,self.sigma,3 if quality==0 else 9)
        for panel,yi,pi in [('front',5,6),('back',7,8)]:
            projection=Projection(self.model,params,physical[yi],physical[pi],quality);obs=self.panels[panel];u=np.array([r['u'] for r in obs]);target=np.array([r['z'] for r in obs]);roofs,diag=projection.roof((u[:,None]+step[None,:]).ravel());roofs=roofs.reshape(len(obs),-1)
            # Box/continuous-curve intersection: both interval sides matter.
            low=np.nanmin(roofs,axis=1);high=np.nanmax(roofs,axis=1);missing=~np.isfinite(low);low[missing]=1.15;high[missing]=1.15
            rh=np.maximum(low-target-self.sigma,0)/self.sigma;rl=np.maximum(target-self.sigma-high,0)/self.sigma;res.extend(rh);res.extend(rl)
            if record:
                for i,r in enumerate(obs):details.append(dict(**r,model_roof_interval=[float(low[i]),float(high[i])],excess_above_box_m=float(rh[i]*self.sigma),deficit_below_box_m=float(rl[i]*self.sigma),no_hit=bool(missing[i])))
                details.append(dict(panel=panel,diagnostic='numeric projected zero envelope, sampled/refined depth minimization',maximum_absolute_root_field_value_not_distance=float(np.max(abs(diag['field_residual']))),guidecut_active_count=int(diag['guidecut_active'].sum()),depth_boundary_count=int((abs(diag['depth'])>.2499).sum())))
        projection=Projection(self.model,params,physical[9],physical[10],quality);z=np.array([r['z'] for r in self.profile]);left,right=projection.sides((z[:,None]+step[None,:]).ravel());left=left.reshape(len(z),-1);right=right.reshape(len(z),-1)
        for side,values in [('left',left),('right',right)]:
            low=np.nanmin(values,axis=1);high=np.nanmax(values,axis=1);target=np.array([r[side] for r in self.profile]);bad=~np.isfinite(low);low[bad]=-.14;high[bad]=-.14;rh=np.maximum(low-target-self.sigma,0)/self.sigma;rl=np.maximum(target-self.sigma-high,0)/self.sigma;res.extend(rh);res.extend(rl)
            if record:
                for i,r in enumerate(self.profile):details.append(dict(panel='profile',side=side,pixel=[r[side+'_pixel'],r['pixel_y']],source_u=target[i],source_z=r['z'],model_u_interval=[float(low[i]),float(high[i])],excess_right_m=float(rh[i]*self.sigma),excess_left_m=float(rl[i]*self.sigma),no_hit=bool(bad[i])))
        residual=np.asarray(res,float)
        assert np.isfinite(residual).all()
        if record:return residual,details,physical
        return residual

def solve(problem,x,max_iterations=24):
    """Single bounded LM run; no starts/grid or artist coefficient batches."""
    lam=.1;r=problem.evaluate(x);cost=float(r@r);history=[];reason='iteration_limit';last_rank=None
    for iteration in range(max_iterations):
        if time.time()-problem.start>900:reason='900_second_budget';break
        J=np.empty((len(r),len(x)));h=.005
        for k in range(len(x)):
            q=x.copy();q[k]=min(x[k]+h,1.) if x[k]<1-h/2 else max(x[k]-h,0.);J[:,k]=(problem.evaluate(q)-r)/(q[k]-x[k])
        sv=np.linalg.svd(J,compute_uv=False);rank=int((sv>max(sv[0]*1e-6,1e-8)).sum());last_rank=rank
        accepted=False;stepnorm=0.
        for attempt in range(4):
            diagonal=np.maximum(np.sum(J*J,axis=0),1.);A=J.T@J+lam*np.diag(diagonal);delta=np.linalg.solve(A,-J.T@r);norm=np.linalg.norm(delta)
            if norm>.5:delta*=.5/norm
            q=np.clip(x+delta,0,1);stepnorm=float(np.linalg.norm(q-x));rr=problem.evaluate(q);newcost=float(rr@rr)
            if newcost<cost-1e-10:
                x=q;r=rr;cost=newcost;lam=max(lam/3,1e-6);accepted=True;break
            lam*=10
        row=dict(iteration=iteration,cost=cost,maximum_normalized_interval_violation=float(r.max()),rank=rank,lambda_value=lam,accepted=accepted,stepnorm=stepnorm,physical_parameters=(LOW+x*(HIGH-LOW)).tolist(),seconds=time.time()-problem.start,evaluations=problem.calls);history.append(row);print('H_RAM_ITER',json.dumps(row),flush=True)
        # Small recovery receipt only, never shape arrays or whole-scene data.
        (CANONICAL/'.mia-cache/body-h/shape/solve1-progress.json').write_text(json.dumps(dict(status='RUNNING_UNSELECTED',latest=row,history=history),indent=2)+'\n',encoding='utf-8',newline='\n')
        if r.max()<.02:reason='coarse_interval_feasibility';break
        if not accepted:reason='no_meaningful_progress_or_rank';break
        if rank==0:reason='rank_zero';break
    return x,history,reason,last_rank

def main():
    path=ASSET/'integration/workspace-storage-20261103/storage_guard.py';spec=importlib.util.spec_from_file_location('H_fit_capacity',path);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);capacity=guard.inspect(10*1024*1024)
    if capacity['violations']:raise RuntimeError(json.dumps(capacity))
    out=CANONICAL/'.mia-cache/body-h/shape/solve1.json';assert not out.exists(),'One solve only; do not overwrite/retune'
    assert not (out.parent/'solve1-stopped.json').exists(),'Solve1 stopped pending independent registration audit; no automatic rerun'
    model=Model();problem=Problem(model)
    # Small source-independent hinge-onset seed; scales neutral. It avoids a
    # zero derivative at the C2 hinge origin, not a HALF/source target.
    physical=np.array([1.,1.,.001,.0025,1.,0.,0.,180.,0.,85.,0.]);x=(physical-LOW)/(HIGH-LOW)
    initial_r,initial_details,_=problem.evaluate(x,record=True);x,history,reason,rank=solve(problem,x);coarse_r,_,physical=problem.evaluate(x,record=True)
    print('H_RAM_FINAL_VERIFY_BEGIN',flush=True);fine_r,details,physical=problem.evaluate(x,quality=1,record=True)
    from diagnostics import analyze
    diagnostics=analyze(model,physical[:5],CANONICAL)
    result=dict(status='RAM_INTERVAL_FIT_UNSELECTED_NO_MESH',stop_reason=reason,parameter_names=NAMES,parameters=physical.tolist(),parameter_bounds=[LOW.tolist(),HIGH.tolist()],initial_seed=[1.,1.,.001,.0025,1.,0.,0.,180.,0.,85.,0.],initial_maximum_normalized_violation=float(initial_r.max()),coarse_maximum_normalized_violation=float(coarse_r.max()),fine_maximum_normalized_violation=float(fine_r.max()),fine_violated_sides=int((fine_r>.02).sum()),fine_raw_residual_vector=fine_r.tolist(),local_solver_rank=rank,iterations=history,actual_observations=details,source_observations=problem.observations,profile_observations=problem.profile,source_registration=problem.rails['registration'],trace_uncertainty='2px inBOTHaxes, interval/curve intersection; no perpoint fit variables. Each panel shares exactly one yaw/pitch.',camera_model='Rigid orthographic right/up/depth about frozen target(0,-.018,.86), original uniform wholeheight SRT. No source warp/refit.',model=model.metadata(physical[:5]),physical_diagnostics=diagnostics,minimum_change_secondary='Not claimed: feasibility must be established first; no source fit inferred from loss minimum.',solver='One bounded NumPy LM, finite-difference Jacobian, single hinge-onset seed, max24iterations/900seconds. No parameter/amplitude/mesh grid. Field values are never distance residuals; objective uses projectedzero envelopes.',numeric_verification='Final9samples across each tracebox/121depthsamples with parabolic refinement/24rootbisections; report root field residuals separately. This is numerical envelope verification, not ART/native evidence.',capacity=capacity,raw_cache_only=True,mesh_created=False,GPU_used=False,native_saved=False,baked=False,inputs_copied=False)
    out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n');print('H_RAM_SOLVE1_READY',str(out),out.stat().st_size,'fine max',float(fine_r.max()),flush=True)

if __name__=='__main__':main()
