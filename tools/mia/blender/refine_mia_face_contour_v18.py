"""Bounded v18 orbital/cheek correction; all keys share offsets, source immutable."""
import bpy,sys,math,json,hashlib,argparse
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import refine_mia_head_v06 as h
ap=argparse.ArgumentParser()
ap.add_argument('--source',default=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/uv-refined/Mia_HeadHair_v17d.blend')
ap.add_argument('--output-dir',required=True)
ap.add_argument('--trial',type=int,choices=[1,2,3,4],default=4)
ap.add_argument('--quick',action='store_true')
ap.add_argument('--resolution',type=int,default=1000)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);SOURCE=Path(a.source).resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrhash(seq):return hashlib.sha256(np.asarray(seq).tobytes()).hexdigest()
def snapshot(o):
 d=o.data
 return {'co':arrhash([tuple(v.co) for v in d.vertices]),'topology':arrhash([v for p in d.polygons for v in (len(p.vertices),*p.vertices)]),'uv':{l.name:arrhash([tuple(v.uv) for v in l.data]) for l in d.uv_layers},'weights':arrhash([(v.index,g.group,g.weight) for v in d.vertices for g in v.groups]),'keys':{k.name:arrhash([tuple(v.co) for v in k.data]) for k in d.shape_keys.key_blocks} if d.shape_keys else {},'materials':[s.material.name if s.material else None for s in o.material_slots],'matrix':str(o.matrix_world),'modifiers':[(m.name,m.type,m.show_render) for m in o.modifiers]}
def surface_metrics(skin):
 bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();bvh=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear();grid=[]
 for x in [-.055,-.045,.045,.055]:
  for z in [1.542,1.537,1.532,1.527,1.522,1.512,1.502]:
   hit=bvh.ray_cast(Vector((x,-.30,z)),Vector((0,1,0)))
   if hit[0] is not None:grid.append({'x':x,'z':z,'point':list(hit[0]),'normal':list(hit[1])})
 return grid
source_sha=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;skin=bpy.data.objects['MIA_V14_SculptedSkin'];body=bpy.data.objects[h.BODY_NAME]
assert not skin.get('v18_contour_applied'), 'Recipe must run exactly once on the original input.'
before={o.name:snapshot(o) for o in scene.objects if o.type=='MESH'};before_metrics=surface_metrics(skin)
coords=np.array([tuple(v.co) for v in skin.data.vertices]);keys={k.name:np.array([tuple(v.co) for v in k.data]) for k in skin.data.shape_keys.key_blocks}
# Locate the actual open eye boundary, rather than protecting a guessed rectangular socket.
edgeuses={tuple(sorted(e.vertices)):0 for e in skin.data.edges}
for p in skin.data.polygons:
 for i,j in zip(p.vertices,list(p.vertices)[1:]+[p.vertices[0]]):edgeuses[tuple(sorted((i,j)))]+=1
rimids={i for edge,n in edgeuses.items() if n==1 for i in edge if 1.525<coords[i,2]<1.558 and .012<abs(coords[i,0])<.066 and coords[i,1]>.025}
rim=coords[sorted(rimids)]
adj=[set() for p in coords]
for e in skin.data.edges:
 i,j=e.vertices;adj[i].add(j);adj[j].add(i)
deltas=np.zeros_like(coords);protection=[]
# Coordinated guide field: C1 cubic horizontal curves, smoothly lofted vertically.
# Negative Y retreats the excessively frontal outer-orbit shelf; the mid-cheek is
# not inflated. The inner canthus and central nose/mouth/chin remain anchored.
guide_x=np.array([.020,.035,.050,.065,.082])
guide_z=np.array([1.480,1.490,1.505,1.520,1.535,1.550,1.565,1.580])
guide_dy=np.array([[0,0,0,0,0],[0,0,0,0,0],[0,-.0005,-.001,0,0],[0,-.0007,-.002,-.003,0],[0,-.0015,-.006,-.009,0],[0,-.001,-.004,-.007,0],[0,-.0005,-.0015,-.003,0],[0,0,0,0,0]])
def cubic(t,knots,values):
 if t<=knots[0]:return float(values[0])
 if t>=knots[-1]:return float(values[-1])
 k=int(np.searchsorted(knots,t)-1);span=knots[k+1]-knots[k];u=(t-knots[k])/span
 slopes=np.zeros_like(values);slopes[1:-1]=(values[2:]-values[:-2])/(knots[2:]-knots[:-2])
 return float((2*u**3-3*u*u+1)*values[k]+(u**3-2*u*u+u)*span*slopes[k]+(-2*u**3+3*u*u)*values[k+1]+(u**3-u*u)*span*slopes[k+1])
def coordinated_offset(p):
 x,y,z=map(float,p);xx=abs(x)
 front=h._smooth((y-.004)/.020)
 center=h._smooth((xx-.020)/.012)
 lateral=1-h._smooth((xx-.063)/.017)
 vertical=h._smooth((z-1.482)/.026)*(1-h._smooth((z-1.552)/.028))
 amplitude=.0060 if a.trial==3 else .0045+.0015*(1-h._smooth((z-1.518)/.020))
 dx=-math.copysign(amplitude,x)*h._smooth((xx-.020)/.040)*lateral*vertical*front
 dy=cubic(z,guide_z,np.array([cubic(xx,guide_x,row) for row in guide_dy]))*center*front
 return np.array([dx,dy*(1 if a.trial==3 else .40),0.0])
for i,p in enumerate(coords):
 if a.trial>=3:
  deltas[i]=coordinated_offset(p);continue
 x,y,z=p;xx=abs(x);front=h._smooth((y-.022)/.020)
 distance=float(np.linalg.norm(rim-p,axis=1).min()) if len(rim) else 1
 protect=h._smooth((distance-(.002 if a.trial==1 else .00075))/(.006 if a.trial==1 else .0035));protection.append(protect)
 # Broad width taper follows the cheek, does not scale the eye opening or skull.
 width=math.exp(-((xx-.055)/.020)**4-((z-1.515)/.026)**4)*front*protect
 deltas[i,0]=-math.copysign(.0025 if a.trial==1 else .0015,x)*width
 # Fill the recessed upper cheek below the orbital shelf, not a uniform face flattening.
 fill=math.exp(-((xx-.052)/.016)**4-((z-(1.526 if a.trial==1 else 1.530))/.014)**2)*front*protect
 deltas[i,1]+=(.0015 if a.trial==1 else .0040)*fill
 # Local depth-only relaxation attenuates coarse triangular turning, with strict cap.
 if adj[i]:
  mean=np.mean(coords[list(adj[i])],axis=0)
  weight=math.exp(-((xx-.053)/.016)**4-((z-1.532)/.016)**4)*front*protect
  deltas[i,1]+=np.clip((mean[1]-y)*.40,-.00065,.00065)*weight
 # Completely freeze upper head, nose/lips and the far lateral ear/cap seam.
 if z>=1.558 or xx<.027 or xx>.077:deltas[i]=0
for k in skin.data.shape_keys.key_blocks:
 for i,v in enumerate(k.data):v.co=keys[k.name][i]+deltas[i]
for i,v in enumerate(skin.data.vertices):v.co=coords[i]+deltas[i]
skin.data.update();skin['v18_contour_applied']=a.trial
allowed_changes={skin.name}
if a.trial>=3:
 # Carry the actual curved eye carrier and silhouette lash meshes with the rim.
 followers=[bpy.data.objects['MIA_V14_EyeSurface']]+[o for o in scene.objects if o.type=='MESH' and not o.hide_render and any(t in o.name for t in ['UpperLash','OuterWing'])]
 for o in followers:
  into_skin=skin.matrix_world.inverted()@o.matrix_world;back=o.matrix_world.inverted().to_3x3()@skin.matrix_world.to_3x3();old=[v.co.copy() for v in o.data.vertices]
  if a.trial==4 and o.name=='MIA_V14_EyeSurface':
   ds=[]
   for p in old:
    q=into_skin@p;center=Vector((math.copysign(.037,q.x),.060,1.541));move=Vector(coordinated_offset(center));relative=q-center;relative.x*=.92;relative.y*=.92;ds.append(back@(center+move+relative-q))
  else:ds=[back@Vector(coordinated_offset(into_skin@p)) for p in old]
  if o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks:
    for v,d in zip(k.data,ds):v.co+=d
  for v,p,d in zip(o.data.vertices,old,ds):v.co=p+d
  o.data.update();allowed_changes.add(o.name)
 if a.trial==4:
  bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();surface=BVHTree.FromPolygons([v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
  for o in followers:
   if o.name=='MIA_V14_EyeSurface':continue
   into_skin=skin.matrix_world.inverted()@o.matrix_world;back=into_skin.inverted()
   for v in o.data.vertices:
    q=into_skin@v.co;hit=surface.ray_cast(Vector((q.x,.30,q.z)),Vector((0,-1,0)))[0]
    if hit is not None:q.y=hit.y+.00045;v.co=back@q
   o.data.update()
 eyes=bpy.data.objects['MIA_V14_EyeSurface'];oldmat=eyes.material_slots[5].material;iris=oldmat.copy();iris.name='MIA_V18_Coordinated_GrayIris';divs=[n for n in iris.node_tree.nodes if n.type=='MATH' and n.operation=='DIVIDE' and not n.inputs[1].is_linked and abs(n.inputs[1].default_value-.252)<.00001];assert len(divs)==1
 divs[0].inputs[1].default_value=.252*1.12;eyes.material_slots[5].material=iris
 assert eyes.material_slots[1].material.use_backface_culling
after={o.name:snapshot(o) for o in scene.objects if o.type=='MESH'}
unrelated=[name for name in before if name not in allowed_changes and before[name]!=after[name]]
assert not unrelated,unrelated
for field in ['topology','uv','weights','materials','matrix','modifiers']:assert before[skin.name][field]==after[skin.name][field],field
for name in allowed_changes:
 for field in ['topology','uv','weights','matrix','modifiers']:assert before[name][field]==after[name][field],(name,field)
drift={}
for k in skin.data.shape_keys.key_blocks:
 rel=k.relative_key.name;now=np.array([tuple(v.co) for v in k.data])-np.array([tuple(v.co) for v in k.relative_key.data]);drift[k.name]=float(np.abs(now-(keys[k.name]-keys[rel])).max())
assert max(drift.values())<2e-7
manifest={'source':str(SOURCE),'source_sha':source_sha,'trial':a.trial,'before':before,'after':after,'allowed_changes':sorted(allowed_changes),'unrelated_changes':unrelated,'key_relative_delta_max_error_m':drift,'eye_boundary_vertices':sorted(rimids),'eye_boundary_max_displacement_m':float(np.linalg.norm(deltas[sorted(rimids)],axis=1).max()) if rimids else None,'moved_vertices':int(np.count_nonzero(np.linalg.norm(deltas,axis=1)>1e-7)),'max_displacement_m':float(np.linalg.norm(deltas,axis=1).max()),'before_surface_samples':before_metrics,'after_surface_samples':surface_metrics(skin),'cap_decision':'No body/cap or global cranial change. Coordinated trial3 field smoothly vanishes at z1.580 and x.082; temple seam must be visually checked. Earlier rejected trials froze z1.558+.','shape_key_names':list(keys),'coordinated_guide':{'x':guide_x.tolist(),'z':guide_z.tolist(),'depth_offsets_m':guide_dy.tolist(),'iris_uv_width_factor':1.12} if a.trial==3 else None}
native=OUT/'Mia_FaceContour_v18.blend';bpy.ops.wm.save_as_mainfile(filepath=str(native));manifest['native_sha']=sha(native)
# Every preview starts from the saved actual native or original source, never an unsaved candidate.
views=[('front',0,0),('left45',45,0),('right45',-45,0),('profile90',90,0),('upper20_left45',45,20),('upper20_right45',-45,20),('upper35_left45',45,35),('upper35_right45',-45,35)]
def setup(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100;s.camera.data.ortho_scale=.29;return s
def render(s,prefix,vs):
 target=Vector((0,0,1.55))
 for name,yaw,elev in vs:
  y=math.radians(yaw);e=math.radians(elev);h._aim(s.camera,target+Vector((2*math.sin(y)*math.cos(e),-2*math.cos(y)*math.cos(e),2*math.sin(e))),target);s.render.filepath=str(OUT/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
def hide_hair(s):
 members={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
 for o in s.objects:
  if o.type=='MESH' and (o.name in members or any(t in o.name for t in ['Hair','HAIR','PIXAL'])):o.hide_render=True
def clay(s):
 for o in s.objects:
  if o.type=='MESH' and any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
 m=h._paper_material('V18_DIAGNOSTIC_CLAY',(.22,.24,.27,1));bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
 for name in ['MIA_V14_SculptedSkin',h.BODY_NAME]:
  for slot in bpy.data.objects[name].material_slots:slot.material=m
 s.view_settings.exposure-=2.5
for prefix,path in [('before',SOURCE),('after',native)]:
 s=setup(path)
 if not a.quick:render(s,prefix+'_hair',views)
 elif a.trial>=3:render(s,prefix+'_hair',[views[0],views[1]])
 hide_hair(s);render(s,prefix+'_bare',views if not a.quick else [views[0],views[1],views[4]])
 clay(s);render(s,prefix+'_clay',views if not a.quick else [views[0],views[1],views[4]])
if not a.quick:
 s=setup(native);hide_hair(s);ob=bpy.data.objects['MIA_V14_SculptedSkin'];ks=ob.data.shape_keys.key_blocks
 for label,needle,val in [('mild_smile','Fcl_ALL_Fun',.25),('blink','Fcl_EYE_Close',.5)]:
  matches=[k for k in ks if needle.lower()==k.name.lower() or k.name.lower().endswith('_'+needle.lower())]
  if matches:
   matches[0].value=val;render(s,'smoke_'+label,[views[0],views[1]]);matches[0].value=0;manifest[label+'_probe']={'key':matches[0].name,'value':val,'limitation':'Skin-only static probe; inherited eye carrier has no matching keys, not a finished expression rig.'}
  else:manifest[label+'_probe']={'skipped':'No unambiguous matching key'}
 # Actual unchanged UVs displayed on the visible skin.
 s=setup(native);hide_hair(s);ob=bpy.data.objects['MIA_V14_SculptedSkin'];m=bpy.data.materials.new('V18_UV_CHECK_ONLY');m.use_nodes=True;n=m.node_tree.nodes;n.clear();uv=n.new('ShaderNodeUVMap');uv.uv_map=ob.data.uv_layers.active.name;ch=n.new('ShaderNodeTexChecker');ch.inputs['Scale'].default_value=48;em=n.new('ShaderNodeEmission');out=n.new('ShaderNodeOutputMaterial');l=m.node_tree.links;l.new(uv.outputs[0],ch.inputs['Vector']);l.new(ch.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])
 for slot in ob.material_slots:slot.material=m
 render(s,'uv_checker',[views[0],views[1],views[4]])
manifest['source_sha_after']=sha(SOURCE);manifest['native_sha_after_readonly_renders']=sha(native);manifest['script_sha']=sha(__file__)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print('V18_DONE',manifest['native_sha'],flush=True)
