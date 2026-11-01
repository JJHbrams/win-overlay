"""Eye contour E1: actual dense boundary paths, independently shaped upper/lower arcs.

No eye sphere scaling, UV editing, or feature-ID reuse. Every key receives a
closure-aware orbital delta so different upper/lower neutral deltas do not
introduce a new full-blink gap. Existing eyes and hidden legacy cards stay exact.
"""
import argparse,sys,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector

ROOT=Path(__file__).parent
DEFAULT=r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-connected-v26/Mia_ConnectedLoft_Q7_SurfaceFit.blend'
SKIN='MIA_V14_SculptedSkin'
UP_T=np.array([0,.12,.28,.48,.68,.85,1.])
UP_D=np.array([0,.0012,.0014,-.0004,-.0009,-.0007,-.0005])
LO_T=np.array([0,.14,.35,.52,.70,.88,1.])
LO_D=np.array([0,.0003,.0013,.00135,.0001,-.0004,-.0005])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smooth(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def curve(t,x,y):
 # C1 cubic Hermite interpolation; knot values are documented artistic targets.
 d=np.diff(y)/np.diff(x);m=np.zeros_like(y);m[0]=d[0];m[-1]=d[-1]
 for i in range(1,len(y)-1):
  if d[i-1]*d[i]>0:m[i]=2/(1/d[i-1]+1/d[i])
 tt=np.clip(np.asarray(t),0,1);j=np.clip(np.searchsorted(x,tt,side='right')-1,0,len(x)-2);h=x[j+1]-x[j];u=(tt-x[j])/h
 return (2*u**3-3*u*u+1)*y[j]+(u**3-2*u*u+u)*h*m[j]+(-2*u**3+3*u*u)*y[j+1]+(u**3-u*u)*h*m[j+1]

def eye_loops(mesh,P):
 ec=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%len(f.vertices)]))) for f in mesh.polygons for i in range(len(f.vertices)))
 ad=defaultdict(set)
 for (a,b),n in ec.items():
  if n==1:ad[a].add(b);ad[b].add(a)
 remaining=set(ad);loops=[]
 while remaining:
  stack=[min(remaining)];group=set()
  while stack:
   i=stack.pop()
   if i in group:continue
   group.add(i);stack.extend(ad[i])
  remaining-=group;c=P[list(group)].mean(0)
  if len(group)>40 and .01<abs(c[0])<.06 and c[1]>.035 and 1.525<c[2]<1.555:
   inner=min(group,key=lambda i:abs(P[i,0]));outer=max(group,key=lambda i:abs(P[i,0]));paths=[]
   for first in ad[inner]:
    path=[inner,first]
    while path[-1]!=outer:
     nx=ad[path[-1]]-{path[-2]};assert len(nx)==1;path.append(next(iter(nx)));assert len(path)<1000
    paths.append(path)
   paths.sort(key=lambda p:P[p,2].mean(),reverse=True)
   loops.append({'side':int(np.sign(c[0])),'upper':np.array(paths[0]),'lower':np.array(paths[1]),'x0':abs(P[inner,0]),'x1':abs(P[outer,0])})
 assert len(loops)==2
 return loops

def key_closure(loop,P,K,t):
 def z(pts,ids):
  xs=(abs(P[ids,0])-loop['x0'])/(loop['x1']-loop['x0']);ix=np.argsort(xs)
  return np.interp(np.clip(t,.08,.94),xs[ix],pts[ids[ix],2])
 gap=z(P,loop['upper'])-z(P,loop['lower']);gk=z(K,loop['upper'])-z(K,loop['lower'])
 return np.clip(1-gk/np.maximum(gap,.001),0,1)

def snapshot():
 out={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data
  geom=hashlib.sha256();uv=hashlib.sha256();top=hashlib.sha256();keys=hashlib.sha256()
  for v in m.vertices:geom.update(np.asarray(v.co,np.float32).tobytes())
  for p in m.polygons:top.update(np.asarray(p.vertices,np.int32).tobytes());top.update(str(p.material_index).encode())
  for layer in m.uv_layers:
   uv.update(layer.name.encode())
   for p in layer.data:uv.update(np.asarray(p.uv,np.float32).tobytes())
  if m.shape_keys:
   for k in m.shape_keys.key_blocks:
    keys.update(k.name.encode())
    for v in k.data:keys.update(np.asarray(v.co,np.float32).tobytes())
  out[o.name]={'geometry':geom.hexdigest(),'uv':uv.hexdigest(),'topology':top.hexdigest(),'keys':keys.hexdigest(),'materials':[m.name if m else None for m in o.data.materials],'matrix':np.asarray(o.matrix_world).tolist()}
 return out

def target_deltas(loop,P,t,variant):
 if variant=='e1':return curve(t,UP_T,UP_D),curve(t,LO_T,LO_D)
 def current(ids):
  xs=(abs(P[ids,0])-loop['x0'])/(loop['x1']-loop['x0']);ix=np.argsort(xs)
  return np.interp(np.clip(t,0,1),xs[ix],P[ids[ix],2])
 z0=P[loop['upper'][0],2];end=P[loop['upper'][-1],2]-z0-.0005
 ut=np.array([0,.15,.35,.55,.75,.90,1.]);uz=np.array([0,.0026,.00435,.00465,.00445,.0040,end])
 lt=np.array([0,.15,.30,.50,.65,.80,.90,1.]);lz=np.array([0,-.00135,-.0028,-.0030,-.0020,.0001,.0020,end])
 return z0+curve(t,ut,uz)-current(loop['upper']),z0+curve(t,lt,lz)-current(loop['lower'])

def apply_eye_contour(variant='e2'):
 skin=bpy.data.objects[SKIN];keys=skin.data.shape_keys.key_blocks
 assert len(skin.data.vertices)>10000,'Expected verified dense surface, never legacy vertex IDs'
 for k in keys:k.value=0
 P=np.array([v.co[:] for v in keys[0].data]);loops=eye_loops(skin.data,P);fields=[];rim_report=[]
 for loop in loops:
  t=(abs(P[:,0])-loop['x0'])/(loop['x1']-loop['x0']);upper=loop['upper'];lower=loop['lower'];side=(P[:,0]*loop['side']>0)
  # Distance to the actual rim in 3D, not a height-band guess.
  du=np.sqrt(((P[:,None,:]-P[upper][None,:,:])**2).sum(2)).min(1);dl=np.sqrt(((P[:,None,:]-P[lower][None,:,:])**2).sum(2)).min(1)
  choose_upper=du<=dl;dist=np.minimum(du,dl)
  weight=(1-smooth(.0005,.0035,dist))*side
  d_up,d_lo=target_deltas(loop,P,t,variant)
  neutral=np.where(choose_upper,d_up,d_lo);common=(d_up+d_lo)/2 if variant=='e1' else np.zeros_like(t)
  fields.append((loop,t,weight,neutral,common))
  rim_report.append({'side':loop['side'],'upper':upper.tolist(),'lower':lower.tolist(),'inner_x':loop['x0'],'outer_x':loop['x1'],'upper_delta_range_mm':[float(d_up[upper].min()*1000),float(d_up[upper].max()*1000)],'lower_delta_range_mm':[float(d_lo[lower].min()*1000),float(d_lo[lower].max()*1000)]})
 delta_keys={};beforekeys={k.name:np.array([v.co[:] for v in k.data]) for k in keys}
 for k in keys:
  K=beforekeys[k.name];d=np.zeros_like(P)
  for loop,t,weight,neutral,common in fields:
   close=key_closure(loop,P,K,t)
   if variant!='e1':close=np.where(close>.97,1.,close)
   d[:,2]+=weight*((1-close)*neutral+close*common)
  k.data.foreach_set('co',(K+d).astype(np.float32).ravel());delta_keys[k.name]=d
 skin.data.vertices.foreach_set('co',np.array([v.co[:] for v in keys[0].data],np.float32).ravel());skin.data.update()
 close_name=next(k.name for k in keys if k.name.endswith('Fcl_EYE_Close'));closed=beforekeys[close_name]
 follower_reports={}
 for side in (-1,1):
  loop=next(l for l in loops if l['side']==side)
  for prefix in ('MIA_V14_UpperLash_','MIA_V14_OuterWing_'):
   o=bpy.data.objects[prefix+str(side)];sourcekeys=o.data.shape_keys.key_blocks;basis=np.array([v.co[:] for v in sourcekeys[0].data]);mat=skin.matrix_world.inverted()@o.matrix_world
   local=np.array([(mat@Vector(v)).to_tuple() for v in basis]);t=(abs(local[:,0])-loop['x0'])/(loop['x1']-loop['x0'])
   upper,lower=target_deltas(loop,P,t,variant);common=(upper+lower)/2 if variant=='e1' else np.zeros_like(t)
   reports=[]
   for j,k in enumerate(sourcekeys):
    K=np.array([v.co[:] for v in k.data]);closure=key_closure(loop,P,closed,t) if j else np.zeros(len(t))
    if variant!='e1':closure=np.where(closure>.97,1.,closure)
    ds=np.zeros_like(K);ds[:,2]=(1-closure)*upper+closure*common
    # Outer wing remains attached; its far tip is shortened rather than
    # translating a whole rigid wing away from its new curved base.
    if prefix.endswith('OuterWing_'):
     extension=np.maximum(abs(local[:,0])-loop['x1'],0);ds[:,0]=-side*.10*extension*(1-closure if variant!='e1' else 1)
    convert=o.matrix_world.inverted().to_3x3()@skin.matrix_world.to_3x3();do=np.array([(convert@Vector(v)).to_tuple() for v in ds]);k.data.foreach_set('co',(K+do).astype(np.float32).ravel());reports.append(float(np.linalg.norm(do,axis=1).max()))
   o.data.vertices.foreach_set('co',np.array([v.co[:] for v in sourcekeys[0].data],np.float32).ravel());o.data.update();follower_reports[o.name]={'max_delta_mm':max(reports)*1000,'keys':len(sourcekeys)}
 bpy.context.view_layer.update()
 return {'rim':rim_report,'followers':follower_reports,'eye_surface':'unchanged; aperture controls sclera visibility, no eye-surface scale','hidden_legacy_lower_cards':'unchanged; visible lower rim is actual skin aperture','neutral_vertices_changed':int(np.count_nonzero(np.linalg.norm(delta_keys[keys[0].name],axis=1)>1e-9)),'neutral_max_mm':float(np.linalg.norm(delta_keys[keys[0].name],axis=1).max()*1000),'keys':len(keys)},delta_keys

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--source',default=DEFAULT);ap.add_argument('--output-dir',default=str(ROOT/'e2-q7'));ap.add_argument('--variant',default='e2',choices=['e1','e2']);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
 source=Path(a.source);out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);native=out/('Mia_EyeContour_'+a.variant.upper()+'.blend');assert not native.exists()
 source_sha=sha(source);bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);before=snapshot();report,deltas=apply_eye_contour(a.variant);after=snapshot();allowed={SKIN,'MIA_V14_UpperLash_-1','MIA_V14_UpperLash_1','MIA_V14_OuterWing_-1','MIA_V14_OuterWing_1'}
 for n,row in before.items():
  if n not in allowed:assert after[n]==row,n
  else:
   for field in ('uv','topology','materials','matrix'):assert after[n][field]==row[field],(n,field)
 bpy.ops.wm.save_as_mainfile(filepath=str(native));bpy.ops.wm.open_mainfile(filepath=str(native),use_scripts=False);assert snapshot()==after
 np.savez_compressed(out/'eye-deltas.npz',**deltas)
 design={'method':'additive contour delta','upper_t':UP_T.tolist(),'upper_dz_m':UP_D.tolist(),'lower_t':LO_T.tolist(),'lower_dz_m':LO_D.tolist()} if a.variant=='e1' else {'method':'single absolute upper/lower target arcs in skin local Z, anchored at actual inner canthus','upper_t':[0,.15,.35,.55,.75,.90,1.],'upper_z_offset_m':[0,.0026,.00435,.00465,.00445,.0040,'actual outer-minus-inner minus .0005'],'lower_t':[0,.15,.30,.50,.65,.80,.90,1.],'lower_z_offset_m':[0,-.00135,-.0028,-.0030,-.0020,.0001,.0020,'actual outer-minus-inner minus .0005'],'closure':'near-full closure returns to original closed surface, not the neutral arc'}
 report.update({'source':{'path':str(source),'sha256':source_sha},'native':{'path':str(native),'sha256':sha(native)},'source_unchanged':sha(source)==source_sha,'technical_guards':'actual non-target mesh/UV/key/material/transform exact; target UV/topology/material/transform exact; saved native reopened exact','variant':a.variant,'design':design,'recipe':{'path':str(Path(__file__)),'sha256':sha(__file__)},'limitations':['Artistic contour hypothesis guided by source upper plateau/outer curl and shallower lower center; not a pixel-perfect 2D fit.','Closure-aware full-key delta is not complete expression validation; actual half/full blink rendering is still required.','Adjacent midface annulus can overlap Q7 correction; combined actual matte/contact review required.']})
 (out/'manifest.json').write_text(json.dumps(report,indent=2));print('EYE_CONTOUR_DONE',a.variant,report['neutral_vertices_changed'],report['neutral_max_mm'])
