import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;ROOT=P.parent;S=ROOT/'candidate12';SRC=S/'Mia_BodyPrimary_v22_candidate12.blend';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert H(SRC)=='16be84111b922c2ee712553bdcdedc402601dfcd568e746d3b3d2b022087daf3'
prov=json.loads((S/'patch-provenance.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False);o=bpy.data.objects['MIA_V06_BODY_SKIN'];m=o.data;before=np.array([list(o.matrix_world@v.co) for v in m.vertices]);oldfaces=[list(f.vertices) for f in m.polygons]
def smooth(t):
 t=np.clip(t,0,1);return t*t*t*(10-15*t+6*t*t)
def smin(a,b,k):
 h=np.maximum(k-np.abs(a-b),0)/k;return np.minimum(a,b)-k*h*h*h/6
zt=np.array([1.16,1.18,1.20,1.24,1.28,1.32,1.36,1.39,1.41]);xr=np.array([.081,.085,.096,.112,.126,.140,.155,.160,.158]);front=np.array([.120,.117,.115,.108,.102,.097,.085,.055,.040]);mid=-.025
def spline_coeff(values):
 h=np.diff(zt);A=np.zeros((len(zt),len(zt)));rhs=np.zeros(len(zt));A[0,0]=A[-1,-1]=1
 for k in range(1,len(zt)-1):
  A[k,k-1]=h[k-1];A[k,k]=2*(h[k-1]+h[k]);A[k,k+1]=h[k];rhs[k]=6*((values[k+1]-values[k])/h[k]-(values[k]-values[k-1])/h[k-1])
 return np.linalg.solve(A,rhs)
xr_second=spline_coeff(xr);front_second=spline_coeff(front)
def cubic(z,values,second):
 k=np.clip(np.searchsorted(zt,z)-1,0,len(zt)-2);h=zt[k+1]-zt[k];a=(zt[k+1]-z)/h;b=(z-zt[k])/h
 return a*values[k]+b*values[k+1]+((a*a*a-a)*second[k]+(b*b*b-b)*second[k+1])*h*h/6
# Plain volumetric primary forms, smoothly joined to source-fitted thorax.
# Their zero surface has genuine curvature in all directions, not a repeated
# Y(Z) profile extrusion. Dimensions are approximate source-guided art targets.
def field(q):
 x=q[:,0]+.00047769;y=q[:,1];z=q[:,2];rx=cubic(z,xr,xr_second);ry=cubic(z,front,front_second)+mid
 thorax=(np.sqrt((x/rx)**2+((y-mid)/ry)**2)-1)*np.minimum(rx,ry)
 lobes=[]
 for side in [-1,1]:
  dx=x-side*.058;dy=y+.075;dz=z-1.250;angle=side*math.radians(6);lx=math.cos(angle)*dx+math.sin(angle)*dz;lz=-math.sin(angle)*dx+math.cos(angle)*dz
  lobes.append((np.sqrt((lx/.058)**2+(dy/.076)**2+(lz/.058)**2)-1)*.058)
 pair=smin(lobes[0],lobes[1],.008);upper=smooth((z-1.245)/.055);outer=smooth((np.abs(x)-.065)/.045);blend=.020+.020*upper+.008*outer
 return smin(thorax,pair,blend)
def project(q,steps=45):
 q=q.copy()
 for _ in range(steps):
  f=field(q)
  if np.max(np.abs(f))<2e-7:break
  grad=np.zeros_like(q);eps=1e-5
  for axis in range(3):
   a=q.copy();b=q.copy();a[:,axis]+=eps;b[:,axis]-=eps;grad[:,axis]=(field(a)-field(b))/(2*eps)
  step=grad*(f/np.maximum(np.sum(grad*grad,axis=1),1e-9))[:,None];length=np.linalg.norm(step,axis=1);step*=np.minimum(1,.008/np.maximum(length,1e-12))[:,None];q-=step
 return q
x=before[:,0]+.00047769;y=before[:,1];z=before[:,2];w=smooth((z-1.18)/.025)*smooth((1.340-z)/.030)*smooth((.160-np.abs(x))/.030)*smooth((.015-y)/.035);ids=np.where(w>1e-8)[0];target=project(before[ids]);after=before.copy();after[ids]=before[ids]+w[ids,None]*(target-before[ids])
# Redistribute tangentially on the fixed implicit target, not normal smoothing.
# Reprojection preserves the designed primary volume while unclumping the cage.
adj=[set() for _ in m.vertices]
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
for iteration in range(16):
 q=after[ids].copy();mean=np.array([np.mean(after[list(adj[int(i)])],axis=0) for i in ids]);grad=np.zeros_like(q);eps=1e-5
 for axis in range(3):
  a=q.copy();b=q.copy();a[:,axis]+=eps;b[:,axis]-=eps;grad[:,axis]=(field(a)-field(b))/(2*eps)
 grad/=np.maximum(np.linalg.norm(grad,axis=1),1e-12)[:,None];delta=mean-q;delta-=grad*np.sum(delta*grad,axis=1)[:,None];delta*=.45;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1.,.0035/np.maximum(length,1e-12))[:,None]
 projected=project(q+delta,steps=20);after[ids]=before[ids]+w[ids,None]*(projected-before[ids])
inv=o.matrix_world.inverted()
for i in ids:m.vertices[int(i)].co=inv@Vector(after[i])
m.update();changes=[{'vertex':int(i),'before_world':before[i].tolist(),'after_world':after[i].tolist(),'delta_world':(after[i]-before[i]).tolist(),'fit_weight':float(w[i]),'implicit_target_residual':float(field(after[i:i+1])[0])} for i in ids if np.linalg.norm(after[i]-before[i])>1e-8]
for i,q in enumerate(before):
 if q[2]>=1.340 or q[2]<=1.18:assert (o.matrix_world@m.vertices[i].co-Vector(q)).length<2e-7
edge_ratios=[]
for e in m.edges:
 a,b=e.vertices;old=np.linalg.norm(before[a]-before[b]);new=np.linalg.norm(after[a]-after[b]);edge_ratios.append(new/max(old,1e-12))
m.calc_loop_triangles();degenerate=sum(t.area<1e-10 for t in m.loop_triangles)
canonical=np.array(json.loads((ROOT.parent/'mia-body-surface-v20-r2/inspect.json').read_text())['vertices']);bodydelta=json.loads((S/'body-contour-deltas.json').read_text());declared={}
for old,new in prov['source_to_new_preserved_vertices'].items():
 delta=np.array(o.matrix_world@m.vertices[new].co)-canonical[int(old)]
 if np.linalg.norm(delta)>1e-8:declared[old]=delta.tolist()
bodydelta['source_vertex_deltas']=declared;bodydelta['primary_rebuild']='XYZ cage fitted to smooth volumetric union; c5 waist<=1.18 exact';prov['authorized_changed_retained_ids']=sorted(int(i) for i in declared)
DST=P/'Mia_BodyVolumetric_v22_candidate14.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));assert H(SRC)=='16be84111b922c2ee712553bdcdedc402601dfcd568e746d3b3d2b022087daf3'
for r in prov['new_patch_vertices']:r['target_world']=list(o.matrix_world@m.vertices[r['new_vertex']].co)
prov['parent_native']=str(SRC);prov['parent_sha256']=H(SRC);prov['native_sha256']=H(DST);prov['volumetric_fit']='volumetric-controls.json + volumetric-vertex-deltas.json; inherited topology/UV/group weights preserved without resampling';(P/'patch-provenance.json').write_text(json.dumps(prov,indent=2),encoding='utf-8');(P/'body-contour-deltas.json').write_text(json.dumps(bodydelta,indent=2),encoding='utf-8');(P/'volumetric-vertex-deltas.json').write_text(json.dumps(changes,indent=2),encoding='utf-8');controls={'method':'smooth minimum of thorax varying ellipse cylinder and two rotated ellipsoid signed-distance approximations; XYZ finite-gradient projection of existing continuous cage; C2 outer blend to parent','centres_world':[[-.05847769,-.075,1.250],[.05752231,-.075,1.250]],'ellipsoid_radii_xyz':[.058,.076,.058],'upper_axis_tilt_degrees':6,'tilt_direction':'upper longitudinal axis toward medial centre; bilateral mirrored','thorax_z':zt.tolist(),'thorax_radius_x':xr.tolist(),'thorax_anterior_depth':front.tolist(),'thorax_y_mid':mid,'union_blend_m':{'breast_pair':.008,'thorax_lower':.020,'upper_add':.020,'outer_add':.008},'reference_basis':'candidate12/reference-registration.json; profile supported projection nearZ1.24±.015, lower rounding around1.21±.015, front bilateral centres~absX.058; clothing does not define exact bare crease/volume','mapping':'Same parent vertex IDs; canonical source cap mapping in patch-provenance.json','fit_quality':{'core_max_abs_field':float(max(abs(field(after[ids[w[ids]>.999]])))),'minimum_edge_length_ratio':float(min(edge_ratios)),'degenerate_triangles_area_lt_1e_10':int(degenerate)},'redistribution':'16 tangential relaxation/reprojection steps on same volumetric target; C2 thorax-radius interpolation; no primitive radius/centre change','primary_change':'centre moved inside thorax; compensating Y radius preserves frontmost-.151. C2 smooth union, source-guided c12 upper collar>=1.34 fixed; no further primitive loop planned without review','art_acceptance':'NOT_EVALUATED'};(P/'volumetric-controls.json').write_text(json.dumps(controls,indent=2),encoding='utf-8');print('C13_NATIVE',H(DST),'MOVED',len(changes),'FIT',controls['fit_quality'])
