import bpy,numpy as np,json
from pathlib import Path
O=Path(__file__).parent;OUT=O/'face-final-r2';OUT.mkdir(exist_ok=True);bpy.ops.wm.open_mainfile(filepath=str(O/'face-final-work/Mia_Foundation_FinalWork.blend'));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_ContinuousSkin'];ks=master.data.shape_keys.key_blocks;old=np.array([[v.co[:] for v in k.data] for k in ks]);p=old[0];a=np.load(O/'foundation-data.npz',allow_pickle=True);loops=np.load(O/'skin-boundaries.npz',allow_pickle=True);ids=np.array(loops['skin_ids'],int);src=a['keycoords'][0];groups=[];lookup={};vid={}
for i in ids:
 t=tuple(np.round(src[i],6))
 if t not in lookup:lookup[t]=len(groups);groups.append([])
 vid[i]=lookup[t];groups[vid[i]].append(i)
adj=[set() for g in groups]
for f in a['faces'][a['mat']==7]:
 for u,v in zip(f,np.roll(f,-1)):
  u=vid[u];v=vid[v]
  if u!=v:adj[u].add(v);adj[v].add(u)
paths=[([2060,2093,1827,1824,1822,1821,1820,1819,1818,1817,1816,2095],[2060,2059,1790,1791,1796,1797,1801,1800,1802,1804,1806,1807,2096,2095]),([2086,1994,1990,1988,1987,1986,1985,1984,1983,1982,1981,1979],[2086,2087,1998,2001,2002,2006,2005,2010,2009,2012,2013,2015,2017,1979])]
mi={m:np.unique(np.concatenate(a['faces'][a['mat']==m])).astype(int) for m in [1,5]};centers={sign:p[mi[5][p[mi[5],0]*sign>0]].mean(0) for sign in [-1,1]};fixed={}
for j,g in enumerate(groups):
 q=p[g].mean(0)
 if not adj[j] or q[2]<1.522 or q[2]>1.568 or abs(q[0])<.010 or abs(q[0])>.069:fixed[j]=0.
for up,lo in paths:
 sign=int(np.sign(p[up,0].mean()));cx=centers[sign][0]
 for i in set(up+lo):fixed[vid[i]]=.27*(p[i,0]-cx)
n=len(groups);L=np.zeros((n,n));rhs=np.zeros(n)
for j,ns in enumerate(adj):
 if j in fixed:L[j,j]=1;rhs[j]=fixed[j]
 else:
  L[j,j]=len(ns)
  for k in ns:L[j,k]=-1
sol=np.linalg.solve(L,rhs);dx=np.zeros(len(p))
for j,g in enumerate(groups):dx[g]=sol[j]
new=old.copy();new[:,:,0]+=dx
for sign in [-1,1]:
 white=mi[1][p[mi[1],0]*sign>0];iris=mi[5][p[mi[5],0]*sign>0];c=centers[sign];new[:,white,0]=c[0]+1.27*(old[:,white,0]-c[0]);new[:,iris,:]=c+.78*(old[:,iris,:]-c)
for key,c in zip(ks,new):
 for v,co in zip(key.data,c):v.co=co
 key.value=0
for v,c in zip(master.data.vertices,new[0]):v.co=c
for ki,key in enumerate(skin.data.shape_keys.key_blocks):
 for j in range(len(groups)):key.data[j].co.x+=sol[j]
for v,c in zip(skin.data.vertices,skin.data.shape_keys.key_blocks[0].data):v.co=c.co
# Rebuild ribbons: normalized visible core is about half source, so a bounded
# 1.83x width increase; original upper/lower opening heights remain unchanged.
def smoothpath(q):
 out=[]
 for i in range(len(q)-1):
  a=q[max(i-1,0)];b=q[i];c=q[i+1];d=q[min(i+2,len(q)-1)]
  for t in [0,.25,.5,.75]:out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 out.append(q[-1]);return np.array(out)
for up,lo in paths:
 sign=int(np.sign(p[up,0].mean()))
 for label,path,width,direction in [('Upper',up,.0042,1),('Lower',lo,.00032,-1)]:
  ob=next(o for o in bpy.context.scene.objects if o.name.startswith('V27_'+label+'_BoundaryRibbon') and o.name.endswith('_'+str(sign)))
  for ki,c in enumerate(new):
   curve=smoothpath(c[path]);u=np.linspace(0,1,len(curve));w=width*np.sin(np.pi*u)**.6
   if 'Fcl_EYE_Close' in ks[ki].name:w*=.60
   vv=[]
   for pt,ww in zip(curve,w):pt=pt.copy();pt[1]-=.0002;vv.extend([pt,pt+np.array([0,0,direction*ww])])
   if label=='Upper':
    tip=curve[-1]+np.array([sign*.0025,-.0002,.0007]);vv.extend([tip,tip])
   for v,co in zip(ob.data.shape_keys.key_blocks[ki].data,vv):v.co=co
   if ki==0:
    for v,co in zip(ob.data.vertices,vv):v.co=co
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'))
(OUT/'eye-proportion-audit.json').write_text(json.dumps({'source_measurements':'Independent actual pixels: aperture width/IPD about.59-.61; brightheight/IPD.15-.17; iriswidth/IPD.286-.323; darkpupil.045-.075. R1 height.147 already close, no Z restoration.','aperture_width_multiplier':1.27,'iris_uniform_scale':.78,'iris_center_world_before':{str(k):v.tolist() for k,v in centers.items()},'iris_center_world_after':{str(k):new[0,mi[5][p[mi[5],0]*k>0]].mean(0).tolist() for k in [-1,1]},'iris_pupil_shader_compensation':False,'skin_eye_z_changed':False,'upper_width_m':.0042,'primary_cheek_lowerface_changed':False,'max_orbit_support_x_mm':float(abs(sol).max()*1000),'limits':'Actual fresh source/neutral/half/full must be viewed; figures are approximate source measurements, not art approval.'},indent=2));print('R2_PROPORTIONS_SAVED')
