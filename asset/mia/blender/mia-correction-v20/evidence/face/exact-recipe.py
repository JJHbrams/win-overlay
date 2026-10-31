"""V20 coordinated contour correction. Never overwrites its source; no hair/body edits."""
import bpy, sys, math, json, hashlib, argparse
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import refine_mia_head_v06 as h

ap=argparse.ArgumentParser()
ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True)
ap.add_argument('--render-only',action='store_true');ap.add_argument('--full',action='store_true')
ap.add_argument('--strength',type=float,default=.75);ap.add_argument('--resolution',type=int,default=900)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path(a.source).resolve();NATIVE=OUT/'Mia_FaceCorrection_v20.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ah(x):return hashlib.sha256(np.asarray(x).tobytes()).hexdigest()
def coords(o):return np.array([tuple(v.co) for v in o.data.vertices])
def snap(o):
 d=o.data
 return dict(co=ah(coords(o)),topology=ah([v for p in d.polygons for v in (len(p.vertices),*p.vertices)]),uv={l.name:ah([tuple(v.uv) for v in l.data]) for l in d.uv_layers},weights=ah([(v.index,g.group,g.weight) for v in d.vertices for g in v.groups]),keys={k.name:ah([tuple(v.co) for v in k.data]) for k in d.shape_keys.key_blocks} if d.shape_keys else {},materials=[s.material.name if s.material else None for s in o.material_slots],matrix=str(o.matrix_world),modifiers=[(m.name,m.type,m.show_render) for m in o.modifiers],visibility=o.hide_render)
def smooth(t):return h._smooth(t)
def add_offsets(o,ds):
 old=coords(o);keys={k.name:np.array([tuple(v.co) for v in k.data]) for k in o.data.shape_keys.key_blocks} if o.data.shape_keys else {}
 if keys:
  for k in o.data.shape_keys.key_blocks:
   for v,p,d in zip(k.data,keys[k.name],ds):v.co=p+d
 for v,p,d in zip(o.data.vertices,old,ds):v.co=p+d
 o.data.update()
 drift={}
 if keys:
  for k in o.data.shape_keys.key_blocks:
   now=np.array([tuple(v.co) for v in k.data])-np.array([tuple(v.co) for v in k.relative_key.data])
   drift[k.name]=float(np.max(np.abs(now-(keys[k.name]-keys[k.relative_key.name]))))
 return drift

def eye_field(p):
 x,y,z=map(float,p);xx=abs(x);cx=.0345
 # Broaden the aperture around its existing center. Carry depth curvature too.
 w=math.exp(-((xx-cx)/.025)**6-((z-1.540)/.012)**4)*smooth((y-.025)/.025)
 dx=(x-math.copysign(cx,x))*.10*w
 dy=(y-.057)*.10*w
 # Relax the pointed lower-outer corner into a softer arc, with no new eye opening.
 dz=.00055*math.exp(-((xx-.047)/.008)**2-((z-1.533)/.0045)**2)*w
 return np.array([dx,dy,dz])

def contour_field(p):
 x,y,z=map(float,p);xx=abs(x)
 # A continuous elliptical family replaces the abrupt orbital shelf / cheek wall.
 # Centerline and ear/cap boundaries fade to zero; no global head scale.
 zz=np.array([1.480,1.495,1.510,1.525,1.540,1.555,1.575,1.590])
 rx=np.interp(z,zz,[.048,.057,.065,.070,.076,.080,.083,.084])
 ry=np.interp(z,zz,[.065,.074,.075,.073,.071,.072,.076,.076])
 target=ry*math.sqrt(max(0,1-(xx/rx)**2))
 w=smooth((xx-.026)/.020)*(1-smooth((xx-.064)/.012))*smooth((y-.006)/.020)*smooth((z-1.494)/.018)*(1-smooth((z-1.562)/.022))
 dy=.006*math.tanh((target-y)/.006)*w*a.strength
 # Modest local cheek width relaxation. Central chin/nose/mouth remain fixed.
 dx=-math.copysign(.0008,x)*math.exp(-((xx-.057)/.014)**4-((z-1.517)/.020)**4)*smooth((y-.010)/.025)
 return np.array([dx,dy,0])

if not a.render_only:
 source_hash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene
 skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=bpy.data.objects['MIA_V14_EyeSurface']
 assert not skin.get('v20_correction_applied'),'Run on frozen v18, exactly once.'
 before={o.name:snap(o) for o in s.objects if o.type=='MESH'}
 # Use actual Basis coordinates: source mesh.data.vertices has a stale crown cache.
 old=np.array([tuple(v.co) for v in skin.data.shape_keys.key_blocks[0].data]);delta=np.array([contour_field(p)+eye_field(p) for p in old])
 # Fair the remaining lateral supraorbital ridge along its surface normal.
 # Area-weighted triangle normals retain a true geometric test; no custom normal edit.
 work=old+delta;start=work.copy();adj=[set() for v in work]
 for edge in skin.data.edges:
  i,j=edge.vertices;adj[i].add(j);adj[j].add(i)
 fw=[]
 for x,y,z in old:
  fw.append(smooth((abs(x)-.039)/.015)*(1-smooth((abs(x)-.068)/.010))*smooth((y-.005)/.022)*smooth((z-1.525)/.018)*(1-smooth((z-1.576)/.020)))
 for iteration in range(12):
  normals=np.zeros_like(work)
  for poly in skin.data.polygons:
   ids=list(poly.vertices);normal=np.cross(work[ids[1]]-work[ids[0]],work[ids[2]]-work[ids[0]])
   for i in ids:normals[i]+=normal
  norms=np.linalg.norm(normals,axis=1);normals/=np.maximum(norms,1e-12)[:,None]
  steps=np.zeros_like(work)
  for i,nei in enumerate(adj):
   if fw[i]<1e-5 or not nei:continue
   nei=list(nei);dist=np.linalg.norm(work[nei]-work[i],axis=1);weights=1/np.maximum(dist,.0005)
   lap=np.average(work[nei],axis=0,weights=weights)-work[i]
   steps[i]=normals[i]*np.clip(np.dot(lap,normals[i]),-.001,.001)*.32*fw[i]
  work+=steps
 fair_delta=work-start
 delta+=fair_delta
 drift=add_offsets(skin,delta);skin['v20_correction_applied']=True
 changed={skin.name};deltas={skin.name:[{'vertex':i,'local_delta_m':d.tolist()} for i,d in enumerate(delta) if np.linalg.norm(d)>1e-9]}
 # Transform complete eye surface around each carrier center, retaining X/Y curvature.
 toskin=skin.matrix_world.inverted()@eyes.matrix_world;back=toskin.inverted().to_3x3();ed=[]
 iris_vertices={i for p in eyes.data.polygons if p.material_index==5 for i in p.vertices}
 for v in eyes.data.vertices:
  q=toskin@v.co;center=Vector((math.copysign(.0345,q.x),.057,1.540))
  rel=q-center;rel.x*=1.10;rel.y*=1.10
  if v.index in iris_vertices:d=center+rel-q+Vector(contour_field(q))
  else:
   d=Vector(eye_field(q)+contour_field(q))
   # Keep the widened sclera inside the softer outer skin rim, eliminating white tips.
   d.y-=.00065*smooth((abs(q.x)-.047)/.009)
  ed.append(back@d)
 add_offsets(eyes,np.array([tuple(v) for v in ed]));changed.add(eyes.name)
 # Upper ink follows the same field and is seated on the actual evaluated skin.
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 bvh=BVHTree.FromPolygons([v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
 for o in s.objects:
  if o.type!='MESH' or o.hide_render or not any(t in o.name for t in ['UpperLash','OuterWing']):continue
  toskin=skin.matrix_world.inverted()@o.matrix_world;back=toskin.inverted();ds=[]
  for v in o.data.vertices:
   q=toskin@v.co;q+=Vector(eye_field(q)+contour_field(q));hit=bvh.ray_cast(Vector((q.x,.30,q.z)),Vector((0,-1,0)))[0]
   if hit is not None:q.y=hit.y+.00045
   ds.append(back@q-v.co)
  add_offsets(o,np.array([tuple(v) for v in ds]));changed.add(o.name)
 # A single blink follower is transferred from the evaluated skin to owned ink.
 # This is not a final facial rig; the fixed paint and original eye carrier remain.
 blink=next(k for k in skin.data.shape_keys.key_blocks if k.name.endswith('Fcl_EYE_Close'))
 def evalskin():
  bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();vv=np.array([tuple(v.co) for v in me.vertices]);tt=[tuple(t.vertices) for t in me.loop_triangles];ev.to_mesh_clear();return vv,tt
 nv,nt=evalskin();nb=BVHTree.FromPolygons([Vector(p) for p in nv],nt,all_triangles=True)
 blink.value=1;bv,_=evalskin();blink.value=0;bpy.context.view_layer.update();blink_followers=[]
 for name in sorted(changed):
  if not any(t in name for t in ['UpperLash','OuterWing']):continue
  o=bpy.data.objects[name];assert o.data.shape_keys is None
  o.shape_key_add(name='Basis');key=o.shape_key_add(name='MIA_V20_BlinkFollower')
  toskin=skin.matrix_world.inverted()@o.matrix_world;back=toskin.inverted().to_3x3()
  for v,kv in zip(o.data.vertices,key.data):
   q=toskin@v.co;hit,normal,ti,dist=nb.find_nearest(q)
   if ti is None:continue
   ids=nt[ti];aa,bb,cc=nv[list(ids)];M=np.column_stack((bb-aa,cc-aa));uv=np.linalg.lstsq(M,np.asarray(hit)-aa,rcond=None)[0];ww=np.array([1-uv.sum(),uv[0],uv[1]])
   kd=np.sum((bv[list(ids)]-nv[list(ids)])*ww[:,None],axis=0);kv.co=v.co+back@Vector(kd)
  fc=key.driver_add('value');driver=fc.driver;driver.type='AVERAGE';var=driver.variables.new();var.name='skin_blink';var.type='SINGLE_PROP';var.targets[0].id_type='KEY';var.targets[0].id=skin.data.shape_keys;var.targets[0].data_path=blink.path_from_id('value');blink_followers.append(name)
 assert eyes.material_slots[1].material.use_backface_culling
 after={o.name:snap(o) for o in s.objects if o.type=='MESH'}
 unrelated=[n for n in before if n not in changed and before[n]!=after[n]];assert not unrelated,unrelated
 for n in changed:
  for f in ['topology','uv','weights','materials','matrix','modifiers','visibility']:assert before[n][f]==after[n][f],(n,f)
 assert max(drift.values())<2e-7
 manifest=dict(source=str(SOURCE),source_sha256=source_hash,script_sha256=sha(__file__),before=before,after=after,changed_owners=sorted(changed),unrelated_changes=unrelated,body_headcap_changed=False,entire_body_unchanged=True,relative_key_error_m=drift,skin_max_delta_m=float(np.linalg.norm(delta,axis=1).max()),parameters=dict(strength=a.strength,aperture_curvature_scale=1.10,normal_fairing_iterations=12,fairing_max_delta_m=float(np.linalg.norm(fair_delta,axis=1).max()),cap_join='Unchanged. Rejected seam trials confused stale mesh.data.vertices with evaluated Basis; no lift or cap reversal retained'),blink_followers=blink_followers,limits=['Static contour candidate, not art approved','Uneven original triangular control topology retained','Single Close driver is not a complete expression rig','Unchanged fixed UV paint may stretch with the edited geometry'])
 (OUT/'vertex-deltas.json').write_text(json.dumps(deltas,indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE));manifest['native_sha256']=sha(NATIVE)
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes())

views=[('front',0,0,0),('left45',45,0,0),('right45',-45,0,0),('profile90',90,0,0),('expression04',-20,5,-9),('portrait',-5,3,-7.5)]
def load(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100;s.render.pixel_aspect_x=s.render.pixel_aspect_y=1;s.camera.data.type='ORTHO';s.camera.data.ortho_scale=.29;s.camera.data.shift_x=s.camera.data.shift_y=0
 return s
def hide_hair(s):
 members={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
 for o in s.objects:
  if o.type=='MESH' and (o.name in members or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):o.hide_render=True
def clay(s):
 for o in s.objects:
  if o.type=='MESH' and any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
 mat=h._paper_material('V20_NEUTRAL_CLAY',(.22,.24,.27,1));bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
 for name in ['MIA_V14_SculptedSkin',h.BODY_NAME]:
  for slot in bpy.data.objects[name].material_slots:slot.material=mat
 s.view_settings.exposure-=2.5
def render(s,prefix,vs):
 target=Vector((0,0,1.55));metadata=[]
 for name,yaw,elev,roll in vs:
  y,e=math.radians(yaw),math.radians(elev);h._aim(s.camera,target+Vector((2*math.sin(y)*math.cos(e),-2*math.cos(y)*math.cos(e),2*math.sin(e))),target)
  if roll:s.camera.rotation_euler=(s.camera.rotation_euler.to_quaternion()@Quaternion((0,0,1),math.radians(roll))).to_euler()
  s.render.filepath=str(OUT/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
  metadata.append(dict(name=name,yaw=yaw,elevation=elev,roll_image=roll,matrix=[list(r) for r in s.camera.matrix_world],target=list(target),ortho=.29,resolution=a.resolution,frame=s.frame_current))
 (OUT/(prefix+'-cameras.json')).write_text(json.dumps(metadata,indent=2))
for prefix,path in [('before',SOURCE),('after',NATIVE)]:
 s=load(path);render(s,prefix+'_hair',views if a.full else [views[0],views[1]])
 hide_hair(s);render(s,prefix+'_bare',views if a.full else [views[0],views[1]])
 clay(s);render(s,prefix+'_clay',views[:4] if a.full else [views[1]])
print('V20_DONE',str(NATIVE),sha(NATIVE),flush=True)
