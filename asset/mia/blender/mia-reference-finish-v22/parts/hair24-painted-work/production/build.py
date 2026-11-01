import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).parent
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/parts/hair-ink-paint/native/0d7874821981-Mia_HairInkPaint_v22.blend')
SHA='0d787482198137c37a5fd80067f7f6ce74678c1a99df783b0ece7cb59c5fb319'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE)==SHA
bpy.ops.wm.open_mainfile(filepath=str(SOURCE),use_scripts=False)
scene=bpy.context.scene
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=scene.render.resolution_y=760
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.world=bpy.data.worlds.new('V24 Review');scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs[0].default_value=(.19,.19,.19,1)
bg.inputs[1].default_value=.3
for o in scene.objects:
 if o.type=='LIGHT':o.hide_render=True
for name,pos,power,size in [('Key',(-.6,.8,2),55,.8),('Fill',(.7,-.7,1.9),40,1.0)]:
 d=bpy.data.lights.new('V24 '+name,'AREA');d.energy=power;d.shape='DISK';d.size=size
 o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.55))-o.location).to_track_quat('-Z','Y').to_euler()
cameras={}
for name,yaw in [('front',0),('profile',82),('back',180),('left_oblique',35),('right_oblique',-35),('rear_oblique',135)]:
 d=bpy.data.cameras.new('V24 '+name);d.type='ORTHO';d.ortho_scale=.48
 o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);a=math.radians(yaw);o.location=(2*math.sin(a),-2*math.cos(a),1.55);o.rotation_euler=(Vector((0,0,1.55))-o.location).to_track_quat('-Z','Y').to_euler();cameras[name]=o
def render(prefix,views):
 for name in views:
  scene.camera=cameras[name];scene.render.filepath=str(P/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
views=['back','profile','rear_oblique']
render('baseline',views)
oldnames=['MIA_V20_HalfUp_Fold_Left','MIA_V20_HalfUp_Fold_Right','MIA_V20_HalfUp_Binder']
for name in oldnames:bpy.data.objects[name].hide_render=True;bpy.data.objects[name].hide_viewport=True
mat=bpy.data.materials['MIA_V20_AuthoredFold_AshStrata_V22_LightToon']
def sample(controls,n=81):
 ps=[Vector(p) for p in controls];out=[]
 for i in range(n):
  t=i/(n-1)*(len(ps)-1);k=min(int(t),len(ps)-2);t-=k
  a,b,c,d=ps[max(0,k-1)],ps[k],ps[k+1],ps[min(len(ps)-1,k+2)]
  out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return out
def lock(name,controls,w,dep):
 path=sample(controls);N=len(path);S=48;vs=[];fs=[]
 for i,p in enumerate(path):
  t=i/(N-1);taper=math.sin(math.pi*t)**.70
  tangent=(path[min(N-1,i+1)]-path[max(0,i-1)]).normalized();a=Vector((tangent.z,0,-tangent.x)).normalized();b=tangent.cross(a).normalized()
  for j in range(S):
   angle=math.tau*j/S
   # Broad flattened lock, four softly separated strand banks; not rope bevel.
   # Deliberate broad hair banks with three recessed divisions, swept with
   # the same curl: real 3D valleys, not a painted stripe or circular bevel.
   across=math.cos(angle)
   shifts=[-.52+.12*math.sin(t*math.pi),.03-.16*math.sin(t*math.pi),.58-.10*math.sin(t*math.pi)]
   valleys=sum(math.exp(-((across-q)/.075)**2) for q in shifts)
   depthscale=1-.20*valleys*max(0,math.sin(angle))
   widthscale=1+.14*math.sin(t*math.tau+.5)
   vs.append(tuple(p+a*across*(w*taper*widthscale+.00045)+b*math.sin(angle)*(dep*taper+.0003)*depthscale))
 for i in range(N-1):
  for j in range(S):fs.append((i*S+j,i*S+(j+1)%S,(i+1)*S+(j+1)%S,(i+1)*S+j))
 vs.extend([tuple(path[0]),tuple(path[-1])]);c0=len(vs)-2;c1=len(vs)-1
 for j in range(S):fs.append((c0,(j+1)%S,j));fs.append((c1,(N-1)*S+j,(N-1)*S+(j+1)%S))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(vs,[],fs);mesh.materials.append(mat);uv=mesh.uv_layers.new(name='MIA_V20_LongitudinalUV')
 for face in mesh.polygons:
  face.use_smooth=True
  inds=list(face.vertices);js=[v%S for v in inds if v<N*S];seam=0 in js and S-1 in js
  for li,vi in zip(face.loop_indices,inds):
   if vi<N*S:r,j=divmod(vi,S);uv.data[li].uv=(r/(N-1),1 if seam and j==0 else j/S)
   else:uv.data[li].uv=(-.005 if vi==c0 else 1.005,(sum(1 if seam and j==0 else j/S for j in js)/len(js)))
 obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj);obj['role']='closed flattened gathered-hair lobe; static; back +Y; endpoints tucked into measured posterior shell';return obj
new=[]
new.append(lock('MIA_V24_Gather_Main',[(-.020,.116,1.595),(-.024,.132,1.580),(-.017,.140,1.560),(.002,.142,1.554),(.016,.144,1.571),(.007,.150,1.584),(-.006,.122,1.577)],.017,.021))
new.append(lock('MIA_V24_Gather_Upper',[(.030,.116,1.588),(.017,.129,1.601),(-.003,.136,1.599),(-.011,.141,1.586),(-.004,.139,1.574),(.003,.118,1.572)],.012,.018))
new.append(lock('MIA_V24_Gather_Tuck',[(.014,.118,1.576),(.018,.135,1.562),(.007,.134,1.548),(-.011,.133,1.550),(-.016,.117,1.566)],.008,.012))
native=P/'Mia_HairStructure_v24.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(native))
render('candidate',views)
# Matte with the entire actual visible hair surface overridden, for form review.
matte=bpy.data.materials.new('V24 Neutral matte');matte.diffuse_color=(.32,.32,.32,1);matte.use_nodes=True;bsdf=next(n for n in matte.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bsdf.inputs['Base Color'].default_value=(.32,.32,.32,1);bsdf.inputs['Roughness'].default_value=.9
slots={}
for o in scene.objects:
 if o.type=='LIGHT' and o.name.startswith('V24 '):o.data.energy*=.24
for o in scene.objects:
 if o.type=='MESH' and not o.hide_render:
  slots[o.name]=list(o.data.materials)
  for i in range(len(o.data.materials)):o.data.materials[i]=matte
render('matte',views)
for name,mats in slots.items():
 for i,m in enumerate(mats):bpy.data.objects[name].data.materials[i]=m
report={'source':{'path':str(SOURCE),'sha256':SHA},'native':{'path':str(native),'sha256':sha(native)},'new_owners':[o.name for o in new],'hidden_retained_owners':oldnames,'replace_mesh_owners':[],'geometry_note':'Centrally overlapping closed lenticular clumps; no BVH nearest projection; +/-Y direction measured from original hair bounds. Shape is a WIP hypothesis until back/profile review.','dimensions':{o.name:[[min(v.co[k] for v in o.data.vertices),max(v.co[k] for v in o.data.vertices)] for k in range(3)] for o in new}}
(P/'manifest.json').write_text(json.dumps(report,indent=2))
print('DONE',report['native'])
