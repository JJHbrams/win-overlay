"""Owned hair corrections: folded half-up bundle, true crown locks and local tip polish."""
import bpy,math,json,hashlib,struct,sys,argparse
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SRC=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();source_sha=sha(SRC)
bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;hair=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];coll=bpy.data.collections['MIA_V17_PIXAL_HAIR'];cam=s.camera

def signature(o):
 m=o.data;data=b''.join(struct.pack('<3f',*v.co) for v in m.vertices)+b''.join(struct.pack('<2f',*v.uv) for l in m.uv_layers for v in l.data)
 if m.shape_keys:data+=b''.join(struct.pack('<3f',*v.co) for k in m.shape_keys.key_blocks for v in k.data)
 return hashlib.sha256(data).hexdigest()
owned={o.name for o in coll.objects};nonhair={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in owned};packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};uvhash=lambda m:hashlib.sha256(b''.join(struct.pack('<2f',*v.uv) for l in m.uv_layers for v in l.data)).hexdigest();mainuv=uvhash(hair.data)
s.render.resolution_x=s.render.resolution_y=1000;s.render.resolution_percentage=100;cam.data.type='ORTHO';cam.data.ortho_scale=.52;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
views=[('front',0),('profile',90),('back',180),('three_quarter_l',45),('three_quarter_r',-45)]
def render(prefix,cases=views):
 for name,angle in cases:
  t=math.radians(angle);cam.location=(2*math.sin(t),-2*math.cos(t),1.475);cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(OUT/(prefix+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
render('before',[('profile',90),('back',180)])
# Archive the rejected knot owners, never alter their mesh or source data.
oldknot=[o for o in coll.objects if 'Knot' in o.name]
archive=bpy.data.collections.new('MIA_V20_REJECTED_KNOT_ARCHIVE');coll.children.link(archive);archive.hide_render=True;archive.hide_viewport=True
for o in oldknot:
 coll.objects.unlink(o);archive.objects.link(o);o.hide_render=True
# Longitudinal UV signal for NEW locks only. Source Pixal4096 atlas remains untouched.
mat=bpy.data.materials.new('MIA_V20_AuthoredFold_AshStrata');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links;out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0]);mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=94.2478;l.new(sep.outputs['Y'],mult.inputs[0]);wave=n.new('ShaderNodeMath');wave.operation='SINE';l.new(mult.outputs[0],wave.inputs[0]);ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=-1;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.91;ramp.inputs['To Max'].default_value=1.;l.new(wave.outputs[0],ramp.inputs[0]);geo=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(.3,-.65,.7);l.new(geo.outputs['Normal'],dot.inputs[0]);shade=n.new('ShaderNodeMapRange');shade.inputs['From Min'].default_value=-1;shade.inputs['From Max'].default_value=1;shade.inputs['To Min'].default_value=.60;shade.inputs['To Max'].default_value=1.;l.new(dot.outputs['Value'],shade.inputs[0]);mix=n.new('ShaderNodeMath');mix.operation='MULTIPLY';l.new(ramp.outputs[0],mix.inputs[0]);l.new(shade.outputs[0],mix.inputs[1]);col=n.new('ShaderNodeMixRGB');col.blend_type='MULTIPLY';col.inputs[0].default_value=1;col.inputs[1].default_value=(.205,.168,.160,1);l.new(mix.outputs[0],col.inputs[2]);l.new(col.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])

def catmull(points,n=100):
 pts=[Vector(q) for q in points];result=[]
 for j in range(n):
  tt=j/(n-1)*(len(pts)-1);i=min(int(tt),len(pts)-2);t=tt-i;p0=pts[max(i-1,0)];p1=pts[i];p2=pts[i+1];p3=pts[min(i+2,len(pts)-1)];result.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 return result

def lock(name,points,width,depth,outward,phase=0):
 # Bury root/tip centers beneath actual neighboring source hair, not guessed bbox.
 pts=[Vector(q) for q in points]
 bv=BVHTree.FromPolygons([hair.matrix_world@v.co for v in hair.data.vertices],[list(p.vertices) for p in hair.data.polygons])
 for j in [0,len(pts)-1]:
  q=pts[j]
  if outward[0]:
   hit,_,_,_=bv.ray_cast(Vector((2,q.y,q.z)),Vector((-1,0,0)))
   if hit and hit.x>.02:q.x=hit.x-.003
  else:
   hit,_,_,_=bv.ray_cast(Vector((q.x,2,q.z)),Vector((0,-1,0)))
   if hit:q.y=hit.y-.004
 path=catmull(pts);verts=[];faces=[];uvcoords=[];N=32
 for i,c in enumerate(path):
  t=i/(len(path)-1);tangent=(path[min(i+1,len(path)-1)]-path[max(i-1,0)]).normalized();axis=Vector(outward);side=tangent.cross(axis).normalized();normal=side.cross(tangent).normalized();env=.20+.80*math.sin(math.pi*t)**.55;variation=.78+.30*math.sin(t*8+phase);twist=.33*math.sin(t*math.pi*1.5+phase);oldside=side.copy();side=side*math.cos(twist)+normal*math.sin(twist);normal=normal*math.cos(twist)-oldside*math.sin(twist)
  for j in range(N):
   angle=2*math.pi*j/N;ridge=1+.035*math.cos(12*angle+phase);q=c+side*(math.cos(angle)*width*env*variation)+normal*(math.sin(angle)*depth*env*ridge);verts.append(q);uvcoords.append((t,j/N))
 for i in range(len(path)-1):
  for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
 faces.extend([tuple(reversed(range(N))),tuple((len(path)-1)*N+j for j in range(N))]);m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.materials.append(mat);o=bpy.data.objects.new(name,m);coll.objects.link(o);uv=m.uv_layers.new(name='MIA_V20_LongitudinalUV')
 for poly in m.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:uv.data[li].uv=uvcoords[m.loops[li].vertex_index]
 o['MIA_owner']='half_up_fold' if 'Fold' in name or 'Binder' in name else 'crown_hole_repair';o['MIA_new_geometry']='Authored tapered flattened lock, independent editable owner; longitudinal UV; no deformation claim.'
 root=o.vertex_groups.new(name='Roots_Locked');root.add([i for i in range(len(verts)) if i//N<8 or i//N>91],1,'REPLACE');return o
new=[]
new.append(lock('MIA_V20_HalfUp_Fold_Left',[(.018,.105,1.609),(-.009,.126,1.605),(-.028,.143,1.582),(-.022,.150,1.556),(-.002,.145,1.551),(.013,.128,1.571),(.005,.108,1.591)],.012,.0032,(0,1,0),.4))
new.append(lock('MIA_V20_HalfUp_Fold_Right',[(.020,.104,1.610),(.010,.137,1.595),(-.005,.150,1.577),(.009,.146,1.562),(.017,.125,1.543),(-.004,.105,1.535)],.010,.003,(0,1,0),1.2))
new.append(lock('MIA_V20_HalfUp_Binder',[(-.017,.119,1.587),(-.010,.148,1.580),(.004,.151,1.570),(.015,.127,1.566)],.0055,.0032,(0,1,0),2.0))
# Near-side hole is bounded by actual source lock samples. Two overlapping curved locks
# restore a raised surface, with both ends buried under surrounding crown/back strands.
# Reconstruct the true raw-source hole using adjacent actual Pixal strand surface.
# This is a donor transplant, not a claim that missing original polygons were recovered.
donor=[]
for po in hair.data.polygons:
 q=po.center
 if .04<q.x<.12 and .071<q.y<.094 and 1.607<q.z<1.655:donor.append(po)
verts=[];faces=[];loopuv=[];srcids=[];mp={};source_attr=hair.data.attributes.get('MIA_SOURCE_POLYGON')
for po in donor:
 ids=[]
 for li in po.loop_indices:
  vi=hair.data.loops[li].vertex_index
  if vi not in mp:
   q=hair.data.vertices[vi].co.copy();q.y-=.014
   edge=min(max(0,(q.z-1.607)/.009),max(0,(1.655-q.z)/.009),max(0,(q.y-.057)/.006),max(0,(.080-q.y)/.006),1)
   q.x+=.003*edge-.004*(1-edge);mp[vi]=len(verts);verts.append(q)
  ids.append(mp[vi])
 faces.append(ids);loopuv.append({layer.name:[list(layer.data[li].uv) for li in po.loop_indices] for layer in hair.data.uv_layers});srcids.append(source_attr.data[po.index].value if source_attr else po.index)
m=bpy.data.meshes.new('V20_CrownDonor_Surface');m.from_pydata(verts,[],faces)
for ma in hair.data.materials:m.materials.append(ma)
for layer in hair.data.uv_layers:
 uv=m.uv_layers.new(name=layer.name)
 for po,values in zip(m.polygons,loopuv):
  for li,q in zip(po.loop_indices,values[layer.name]):uv.data[li].uv=q
attr=m.attributes.new('MIA_DONOR_SOURCE_POLYGON','INT','FACE')
for po,i in zip(m.polygons,srcids):po.use_smooth=True;attr.data[po.index].value=i
patch=bpy.data.objects.new('MIA_V20_Crown_PixalDonorLock',m);coll.objects.link(patch);patch['MIA_owner']='crown_hole_reconstruction';patch['provenance']='Adjacent Pixal surface relocated14mm alongY, retained exact sourceUV/paintUV. True rawsourcehole remains absent; not original polygon recovery.';new.append(patch)
# Smaller depth-varied folded bundle, roots buried under the existing crown.
for ob in new:
 if 'HalfUp' in ob.name:
  for v in ob.data.vertices:
   q=v.co;v.co=Vector((q.x*.90,.104+(q.y-.104)*.65,1.575+(q.z-1.575)*.85))
  ob.data.update()
# Subtle non-uniform longitudinal strata, avoiding parallel decorative cord lines.
noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=2;scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(3,105,1);l.new(uv.outputs['UV'],scale.inputs[0]) if hasattr(uv,'outputs') else None
texcoord=next(nn for nn in n if nn.type=='TEX_COORD');l.new(texcoord.outputs['UV'],scale.inputs[0]);l.new(scale.outputs[0],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs[0]);ramp.inputs['From Min'].default_value=0;ramp.inputs['From Max'].default_value=1;ramp.inputs['To Min'].default_value=.76;ramp.inputs['To Max'].default_value=1.03
# Local rear-tip tangential polishing only: all source loops/UV/source polygon IDs retained.
m=hair.data;adj=[set() for _ in m.vertices]
for e in m.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
original=[v.co.copy() for v in m.vertices];changed=[]
for iteration in range(3):
 coords=[v.co.copy() for v in m.vertices];updates={}
 for i,q in enumerate(coords):
  if q.z<1.39 and q.y>.025 and adj[i]:
   fade=max(0,min(1,(1.39-q.z)/.045))*max(0,min(1,(q.y-.025)/.025));avg=sum((coords[j] for j in adj[i]),Vector())/len(adj[i]);d=avg-q
   # Limit smoothing to submillimeter spatial noise, preserving broad waves/taper.
   if d.length>.001:d*=.001/d.length
   updates[i]=q+d*(.20*fade)
 for i,q in updates.items():m.vertices[i].co=q
m.update();changed=[i for i,v in enumerate(m.vertices) if (v.co-original[i]).length>1e-9];assert uvhash(m)==mainuv
# Face-based authored owner tags are real only for newly constructed locks; main Pixal stays intact.
assert all(signature(bpy.data.objects[k])==v for k,v in nonhair.items())
for im in bpy.data.images:
 if im.packed_file:im.use_fake_user=True
cam.location=(0,-2,1.475);cam.rotation_euler=(Vector((0,0,1.475))-cam.location).to_track_quat('-Z','Y').to_euler();DST=OUT/'Mia_HairCorrection_v20.blend';bpy.ops.wm.save_as_mainfile(filepath=str(DST));bpy.ops.wm.open_mainfile(filepath=str(DST));s=bpy.context.scene;cam=s.camera
assert all(signature(bpy.data.objects[k])==v for k,v in nonhair.items());assert packed=={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file};render('after',[('profile',90),('back',180)])
# True near-side surface occlusion evidence at diagnosed hole positions.
ray=[]
for y,z in [(.060,1.628),(.060,1.634),(.063,1.628)]:
 r=s.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((2,y,z)),Vector((-1,0,0)));ray.append({'y':y,'z':z,'first_object':r[4].name if r[0] else None,'world_x':r[1].x if r[0] else None})
assert sha(SRC)==source_sha
r={'source':str(SRC),'source_sha256':source_sha,'native_sha256':sha(DST),'nonhair_mesh_uv_keys_exact':len(nonhair),'packed_images_exact':len(packed),'main_hair_faces':len(bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].data.polygons),'main_uv_exact':mainuv,'tip_vertices_smoothed':len(changed),'new_owners':[o.name for o in bpy.data.collections['MIA_V17_PIXAL_HAIR'].objects if o.name.startswith('MIA_V20')],'old_knot_archived_hidden':len(oldknot),'hole_rays':ray,'art_status':'Await image review; not automatic PASS'};(OUT/'manifest.json').write_text(json.dumps(r,indent=2));print('NATIVE',r['native_sha256'])
