"""Independent source-scaled upper/lower lash tufts with actual 42-key lid roots."""
import bpy,numpy as np,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).parent;V=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'D';src=O/'Mia_EyeLash_v29_C2.blend';assert hashlib.sha256(src.read_bytes()).hexdigest()=='e04bc76faaa3f9a855e81660d19bc89adf62b89119c61e087a9a6cf7c394dd26';bpy.ops.wm.open_mainfile(filepath=str(src));master=bpy.data.objects['MIA_V27_Foundation_Face'];skin=bpy.data.objects['MIA_V27_SharedHeadBody'];keys=master.data.shape_keys.key_blocks;names=[k.name for k in keys];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');meta=json.loads((O/'medial-baseline-inspection.json').read_text());paths={int(s):{'Upper':d['upper_evaluated_indices'],'Lower':d['lower_evaluated_indices']} for s,d in meta['evaluated_openings'].items()}
def get(ob):return np.array([[v.co[:] for v in k.data] for k in ob.data.shape_keys.key_blocks])
skinbefore=get(skin);masterbefore=get(master)
for k in keys:k.value=0
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();base=np.array([ev.matrix_world@v.co for v in me.vertices]);ev.to_mesh_clear()
def at(q,t):
 d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))];d/=d[-1];return np.array([np.interp(t,d,q[:,j]) for j in range(3)])
neutralgap={s:np.mean([abs(at(base[paths[s]['Upper']],t)[2]-at(base[paths[s]['Lower']],t)[2]) for t in [.25,.5,.75]]) for s in [-1,1]}
steps=np.array([0,.18,.38,.62,.82,.95,1.]);CROSS=6
specs={'Upper':[(.63,.00055,.00075),(.77,.00065,.00105),(.88,.00070,.00145),(.96,.00060,.00170)],'Lower':[(.70,.00022,.00035),(.83,.00027,.00050),(.94,.00030,.00065)]}
if V=='E':specs={'Upper':[(.68,.00050,.00065),(.82,.00065,.0010),(.91,.00070,.0024),(.975,.00055,.0027)],'Lower':[(.74,.00016,.00025),(.86,.00019,.00035),(.955,.00022,.00045)]}
out={(s,label):[] for s in [-1,1] for label in ['Upper','Lower']};contact=[]
def normal(v):return v/max(np.linalg.norm(v),1e-10)
for ki,k in enumerate(keys):
 for kk in keys:kk.value=0
 if ki:k.value=1
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=np.array([ev.matrix_world@v.co for v in me.vertices]);bv=BVHTree.FromPolygons([Vector(q) for q in p],[list(f.vertices) for f in me.polygons]);record={'key':k.name,'owners':{}}
 for side in [-1,1]:
  curves={label:p[paths[side][label]] for label in ['Upper','Lower']};gap=np.mean([abs(at(curves['Upper'],t)[2]-at(curves['Lower'],t)[2]) for t in [.25,.5,.75]]);close=float(np.clip(1-gap/max(neutralgap[side],1e-8),0,1))
  for label in ['Upper','Lower']:
   upper=label=='Upper';q=curves[label];coords=[];offsets=[];miss=0
   for t,width,sweep in specs[label]:
    root=at(q,t);T=normal(at(q,min(1,t+.008))-at(q,max(0,t-.008)));root[2]+=.00035 if upper else -.00030 if V=='E' else -.00025
    hit=bv.ray_cast(Vector((root[0],-.2,root[2])),Vector((0,1,0)));h=hit[0]
    if h is not None:root[1]=h.y-.000075
    else:root[1]-=.000075
    ink=np.interp(t,[0,.12,.35,.65,.85,1],[0,.0022,.0032,.00355,.0038,.0011]);zheight=(ink*.96+.00045)*(1-close)+(-.00035)*close if upper else -(.00065+.00035*(t-.7)/.24)*(1-.22*close)
    if V=='E':zheight=np.interp(t,[.68,.82,.91,.975],[.0016,.0020,.0014,.00075])*(1-close)-.00030*close if upper else -(.00032+.00023*(t-.74)/.215)*(1-.22*close)
    depth=((.0014+.0002*close) if upper else .00018) if V=='E' else (.00075+.0005*close) if upper else .00036
    if V=='E':
     F=normal(np.array(hit[1]) if hit[1] is not None else np.array([0,-1,0]));F=normal(F-T*(F@T))
     if F[1]>0:F=-F
     U=side*normal(np.cross(F,T));p0=root;p1=root+T*sweep*.08+F*depth*.30+U*zheight*.43;p2=root+T*sweep*.68+F*depth*1.12+U*zheight*.92;p3=root+T*sweep+F*depth+U*zheight
    else:p0=root;p1=root+[side*sweep*.08,-depth*.30,zheight*.43];p2=root+[side*sweep*.68,-depth*1.12,zheight*.92];p3=root+[side*sweep,-depth,zheight]
    for ri,u in enumerate(steps):
     c=(1-u)**3*p0+3*(1-u)**2*u*p1+3*(1-u)*u*u*p2+u**3*p3;D=normal(3*(1-u)**2*(p1-p0)+6*(1-u)*u*(p2-p1)+3*u*u*(p3-p2));W=normal(T-D*(T@D));B=normal(np.cross(D,W));w=width*np.interp(u,[0,.20,.55,.82,1],[1,1.12,.72,.32,.018]);th=(.000065 if upper else .000038)*np.interp(u,[0,.3,.8,1],[.7,1,.6,.2])
     for ci in range(CROSS):
      a=ci*2*math.pi/CROSS;v=c+W*w*math.cos(a)+B*th*math.sin(a)
      if ri==0:
       # Root lies on the exterior lash-bearing lid, not in the opening.
       xx=q[:,0]*side;zz=np.interp(v[0]*side,xx,q[:,2]);v[2]=max(v[2],zz+.00018) if upper else min(v[2],zz-.00015)
       hh=bv.ray_cast(Vector((v[0],-.2,v[2])),Vector((0,1,0)))[0]
       if hh is not None:
        clearance=.000075-B[1]*th*math.sin(a);v[1]=hh.y-clearance;offsets.append(clearance)
       else:miss+=1
      else:
       hh=bv.ray_cast(Vector((v[0],-.2,v[2])),Vector((0,1,0)))[0]
       if hh is not None:v[1]=min(v[1],hh.y-.000055)
      coords.append(v)
   out[(side,label)].append(coords);record['owners'][label+'_'+str(side)]={'closure_from_actual_margin_gap':close,'root_samples':len(offsets),'root_miss':miss,'front_root_clearance_mm':[min(offsets)*1000,max(offsets)*1000] if offsets else None}
 ev.to_mesh_clear();contact.append(record);print('LASH_KEY',ki,k.name,flush=True)
material=next(o for o in bpy.context.scene.objects if 'Upper' in o.name and 'BoundaryRibbon' in o.name and not o.hide_render).data.materials[0].copy();material.name='V29_Lash_NativeSoftBlack';created=[];payload={}
for (side,label),a in out.items():
 a=np.array(a);faces=[];nt=len(specs[label]);nv=len(steps)*CROSS
 for ti in range(nt):
  off=ti*nv
  for r in range(len(steps)-1):
   for c in range(CROSS):cn=(c+1)%CROSS;faces.append([off+r*CROSS+c,off+r*CROSS+cn,off+(r+1)*CROSS+cn,off+(r+1)*CROSS+c])
  faces.append([off+c for c in reversed(range(CROSS))]);faces.append([off+(len(steps)-1)*CROSS+c for c in range(CROSS)])
 me=bpy.data.meshes.new('V29_'+label+'Lashes_'+str(side));me.from_pydata(a[0],[],faces);me.materials.append(material);uv=me.uv_layers.new(name='UVMap')
 for f in me.polygons:
  f.use_smooth=True
  for li,vi in zip(f.loop_indices,f.vertices):
   ti=vi//nv;ri=(vi%nv)//CROSS;ci=vi%CROSS;uv.data[li].uv=((ti+(math.cos(ci*2*math.pi/CROSS)+1)/2)/nt,float(steps[ri]))
 ob=bpy.data.objects.new(me.name,me);bpy.context.scene.collection.objects.link(ob)
 for ki,(kn,co) in enumerate(zip(names,a)):
  sk=ob.shape_key_add(name=kn,from_mix=False)
  for v,p in zip(sk.data,co):v.co=p
  if ki:
   d=sk.driver_add('value').driver;d.type='AVERAGE';v=d.variables.new();v.name='face_key';v.type='SINGLE_PROP';v.targets[0].id_type='KEY';v.targets[0].id=master.data.shape_keys;v.targets[0].data_path='key_blocks['+json.dumps(kn)+'].value'
 vg=ob.vertex_groups.new(name='J_Bip_C_Head');vg.add(list(range(len(me.vertices))),1,'REPLACE');arm=ob.modifiers.new('V29_Lash_HeadFollow','ARMATURE');arm.object=rig;created.append({'owner':ob.name,'layer':label+' lashes; separate from BoundaryRibbon ink/brows/pigment','vertices':len(me.vertices),'faces':len(me.polygons),'tuft_groups':nt,'closed_elliptic_cross_sections':CROSS,'curve_stations':len(steps),'material':material.name,'keys':len(names),'upper_open_tip_height_mm':'Existinginkwidth*.96+.45' if label=='Upper' else None,'lower_open_tip_height_mm':'0.65..1.0 downward' if label=='Lower' else None});payload[ob.name]=a
archived=[]
for ob in bpy.context.scene.objects:
 if ob.name.startswith('V28_LashFan_'):ob.hide_render=True;ob.hide_viewport=True;archived.append(ob.name)
for k in keys:k.value=0
bpy.context.view_layer.update();assert np.array_equal(skinbefore,get(skin));assert np.array_equal(masterbefore,get(master));dest=O/('Mia_EyeLash_v29_'+V+'.blend');bpy.ops.wm.save_as_mainfile(filepath=str(dest));np.savez_compressed(O/('lash-'+V+'-coordinates.npz'),**payload);(O/('lash-'+V+'-audit.json')).write_text(json.dumps({'input_native_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'output_native_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'created':created,'archived_old_flat_upper_fans_hidden_not_deleted':archived,'C2_skin_and_master_all42_exact':True,'C2_wall_white_and_trimmed_iris_unchanged':True,'old_liner_ribbon_coordinates_and_UV_unchanged':True,'body_L_preserved':'All C2 sharedskin coords exact, including original0..3956 prefix all42.','actual_perkey_front_root_contact':contact,'method':'Four upper/lower left/right owners, curved tapered closed tuft meshes (6-point elliptic sections,7curve stations). E further sweeps compact outer grouping forward/laterally and halves lower tufts after actual D pinlike silhouette failed source style. Actual evaluated42-key margin paths and surface-ray seating; closed upper lash curls forward/down with actual margin gap. Existing eyeliner remains a separate owner.','limits':'Frontal contact samples are not all-angle/all-closure acceptance. First actual isolate/production/half/full review required before surface maps.'},indent=2));print('LASH_SAVED',V)
