import bpy,json,hashlib,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).parent;ROOT=P.parent;S=ROOT/'candidate8/corrected';SRC=S/'Mia_BodyContinuous_v22_candidate8_corrected.blend';H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert H(SRC)=='8a5bc113690ab336dd9fd990d42a5e656c86a701c8dda9483e6df0c085e378fa'
# Recover exact original parameter-to-vertex correspondence, without saving or
# modifying the parent/source native. Prefix reconstructs only domain + fit data.
D=P/'domain-recovery';D.mkdir(exist_ok=True);recipe=(S/'reconstruct_continuous_thorax.py').read_text(encoding='utf-8');prefix=recipe[:recipe.index('newworld=[pts[i].copy()')];g={'__file__':str(D/'recipe.py')};exec(compile(prefix,str(D/'recipe.py'),'exec'),g)
prov=json.loads((S/'patch-provenance.json').read_text());canonical=g['pts'].copy();domain={int(n):g['param'][int(old)].copy() for old,n in prov['source_to_new_preserved_vertices'].items()};ni=len(prov['source_to_new_preserved_vertices'])
for k,q in enumerate(g['cv']):
 if any(i<g['N'] for i in g['origv'][k]):continue
 domain[ni]=np.array([float(q.x),float(q.y)]);ni+=1
assert ni==3957;oldloft=g['loft'];pchip=g['pchip']
# Full primary target: lower dominant mass, shorter/less broad upper ramp.
profile_z=np.array([1.18,1.20,1.215,1.225,1.235,1.245,1.255,1.265,1.275,1.285,1.295,1.315,1.335,1.355,1.375,1.395]);profile_depth=np.array([0.,0.,.002,.008,.026,.048,.057,.056,.051,.042,.029,.014,.003,0.,0.,0.]);ph=np.diff(profile_z);A=np.zeros((len(ph)+1,len(ph)+1));rhs=np.zeros(len(ph)+1);A[0,0]=A[-1,-1]=1
for k in range(1,len(ph)):
 A[k,k-1]=ph[k-1];A[k,k]=2*(ph[k-1]+ph[k]);A[k,k+1]=ph[k];rhs[k]=6*((profile_depth[k+1]-profile_depth[k])/ph[k]-(profile_depth[k]-profile_depth[k-1])/ph[k-1])
second=np.linalg.solve(A,rhs)
def depth(t):
 if t<profile_z[0] or t>profile_z[-1]:return 0.
 k=max(0,min(len(ph)-1,int(np.searchsorted(profile_z,t)-1)));h=ph[k];a=(profile_z[k+1]-t)/h;b=(t-profile_z[k])/h;return a*profile_depth[k]+b*profile_depth[k+1]+((a*a*a-a)*second[k]+(b*b*b-b)*second[k+1])*h*h/6
shift_t=np.array([1.18,1.20,1.215,1.225,1.235,1.245,1.255,1.265,1.275,1.285,1.295,1.315,1.395]);shift_z=np.array([0.,0.,-.004,-.008,-.013,-.018,-.020,-.020,-.016,-.010,-.004,0.,0.]);return_t=np.array([1.18,1.20,1.215,1.225,1.235,1.245,1.255,1.265,1.275,1.285,1.395]);return_z=np.array([0.,0.,.002,.008,-.001,-.006,-.004,-.002,0.,0.,0.])
def newloft(u,t):
 levels=np.array([1.18,1.22,1.26,1.30,1.34,1.36,1.38,1.395]);anterior=np.array([.117,.111,.106,.100,.094,.0867,.0707,.054]);lateral=np.array([.119,.122,.129,.137,.148,.155,.159,.160]);theta=u/.1;x=float(pchip(levels,lateral,t))*math.sin(theta);base=float(pchip(levels,anterior,t))*math.cos(theta)
 upper=.5*(1+math.tanh((t-1.300)/.022));centre=.059-.007*upper
 def lobe(side):
  dx=side*x-centre;w=(.067-.012*upper) if dx<0 else (.082-.016*upper);q=abs(dx)/w;return (1-q*q)**3 if q<1 else 0.
 mass=lobe(1)+lobe(-1);full=depth(t)*mass;shift=float(pchip(shift_t,shift_z,t))*min(1.,mass/.45)
 ret=float(pchip(return_t,return_z,t));fw=.045 if ret>0 else .060;support=sum(max(0.,1-((x-side*centre)/fw)**2)**3 for side in [-1,1] if abs(x-side*centre)<fw)
 # Lower pole rises gently toward medial/lateral wall, not a full-width groove.
 phase=0.
 for side in [-1,1]:
  dx=side*x-centre;m=lobe(side)
  if m<=0:continue
  rx=.052 if dx<0 else .065;hz=.018 if dx<0 else .026;q=min(abs(dx)/rx,.96);edge=min(1.,m/.20);edge=edge*edge*(3-2*edge);phase+=hz*(1-math.sqrt(1-q*q))*edge
 band=float(pchip(np.array([1.18,1.215,1.235,1.26,1.285,1.315,1.395]),np.array([0.,.2,1.,1.,.3,0.,0.]),t))
 return np.array([-.00047769+x,-base-full,t+shift+ret*min(1.,support)+phase*band])
def smooth(t):
 t=float(np.clip(t,0,1));return t*t*t*(10-15*t+6*t*t)
bpy.ops.wm.open_mainfile(filepath=str(SRC),use_scripts=False);o=bpy.data.objects['MIA_V06_BODY_SKIN'];m=o.data;before=np.array([list(o.matrix_world@v.co) for v in m.vertices]);inv=o.matrix_world.inverted();changes=[];stage=[]
for i,q in enumerate(before):
 x,y,z=q
 if not (1.18<z<1.395 and y<.005 and abs(x+.00047769)<.16):continue
 u,t=domain[i];weight=smooth((z-1.18)/.025)*smooth((1.395-z)/.025)*smooth((.16-abs(x+.00047769))/.025)*smooth((.005-y)/.025)
 delta=(newloft(u,t)-oldloft(u,t))*weight;target=q+delta
 if np.linalg.norm(delta)>1e-8:
  m.vertices[i].co=inv@Vector(target);changes.append({'vertex':i,'domain_u_t':[float(u),float(t)],'before_world':q.tolist(),'target_world':target.tolist(),'delta_world':delta.tolist(),'outer_region_weight':weight});stage.append([i,float(z),float(delta[1]),float(delta[2])])
m.update()
for i,q in enumerate(before):
 if q[2]>=1.395 or q[2]<=1.18:assert (o.matrix_world@m.vertices[i].co-Vector(q)).length<2e-7
bodydelta=json.loads((S/'body-contour-deltas.json').read_text());declared={}
for old,new in prov['source_to_new_preserved_vertices'].items():
 delta=np.array(o.matrix_world@m.vertices[new].co)-canonical[int(old)]
 if np.linalg.norm(delta)>1e-8:declared[old]=delta.tolist()
bodydelta['source_vertex_deltas']=declared;bodydelta['primary_rebuild']='full fitted-surface primary contribution replaced post-fit with C2 outer fade; c5 waist<=1.18 exact';prov['authorized_changed_retained_ids']=sorted(int(i) for i in declared)
DST=P/'Mia_BodyPrimary_v22_candidate12.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));assert H(SRC)=='8a5bc113690ab336dd9fd990d42a5e656c86a701c8dda9483e6df0c085e378fa'
for r in prov['new_patch_vertices']:r['target_world']=list(o.matrix_world@m.vertices[r['new_vertex']].co)
prov['parent_native']=str(SRC);prov['parent_sha256']=H(SRC);prov['native_sha256']=H(DST);prov['post_fit_primary_rebuild']='primary-controls.json and primary-vertex-deltas.json; same topology/UV/weights, full primary contribution replaced post-fit without RBF refit';(P/'patch-provenance.json').write_text(json.dumps(prov,indent=2),encoding='utf-8');(P/'body-contour-deltas.json').write_text(json.dumps(bodydelta,indent=2),encoding='utf-8');(P/'primary-vertex-deltas.json').write_text(json.dumps(changes,indent=2),encoding='utf-8');(P/'primary-controls.json').write_text(json.dumps({'profile_t':profile_z.tolist(),'profile_depth':profile_depth.tolist(),'mass_shift_t':shift_t.tolist(),'mass_shift_z':shift_z.tolist(),'upper_centre':'absX .059-.007*upper','upper_medial_width':'.067-.012*upper','upper_lateral_width':'.082-.016*upper','upper':'.5*(1+tanh((t-1.300)/.022))','method':'replace full XYZ primary contribution on actual fitted parent, including shared lower/side thorax, without recomputing/canceling boundary residual','reference_design':'reference-registration.json; ±15mm art/pose uncertainty, garment not exact anatomy'},indent=2),encoding='utf-8');print('C12_NATIVE',H(DST),'MOVED',len(changes),'DELTA_YZ',min(v[2] for v in stage),max(v[2] for v in stage),min(v[3] for v in stage),max(v[3] for v in stage))
