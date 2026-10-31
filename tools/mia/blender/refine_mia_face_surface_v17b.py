"""v17b bounded nose/profile and chin refinement atop v17 recipe; original inputs immutable."""
import bpy,sys,math,json,hashlib,struct,argparse
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(Path(__file__).resolve().parent));import refine_mia_head_v06 as h
ap=argparse.ArgumentParser();ap.add_argument('--source',default=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-static-complete-v12/head-hair-eye-v16/Mia_ScleraCulling_v16.blend');ap.add_argument('--output-dir',default=str(ROOT/'asset/mia/blender/mia-face-surface-v17/geometry-b'));ap.add_argument('--resolution',type=int,default=1000);ap.add_argument('--quick',action='store_true');a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(o):
 d=o.data;out={'vertices':len(d.vertices),'polygons':len(d.polygons),'uv':hashlib.sha256(b''.join(struct.pack('<2f',*v.uv) for l in d.uv_layers for v in l.data)).hexdigest(),'co':hashlib.sha256(b''.join(struct.pack('<3f',*v.co) for v in d.vertices)).hexdigest(),'topology':hashlib.sha256(b''.join(struct.pack('<I',i) for p in d.polygons for i in p.vertices)).hexdigest(),'weights':hashlib.sha256(b''.join(struct.pack('<IIf',v.index,g.group,g.weight) for v in d.vertices for g in v.groups)).hexdigest()}
 if d.shape_keys:out['key_deltas']={k.name:hashlib.sha256(b''.join(struct.pack('<3f',*(v.co-k.relative_key.data[i].co)) for i,v in enumerate(k.data))).hexdigest() for k in list(d.shape_keys.key_blocks)[1:]}
 return out
source_sha=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;cam=scene.camera;skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=bpy.data.objects['MIA_V14_EyeSurface'];before={o.name:snapshot(o) for o in scene.objects if o.type=='MESH'}
scene.render.resolution_x=scene.render.resolution_y=a.resolution;scene.render.resolution_percentage=100
views=[('front',(0,-2,1.55)),('left',(1.4,-1.4,1.55)),('right',(-1.4,-1.4,1.55)),('profile',(2,0,1.55))]
hair_collection_names={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
hair=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and (o.name in hair_collection_names or 'Hair' in o.name or 'HAIR' in o.name or 'PIXAL' in o.name)]
def render(name,loc=(0,-2,1.55),scale=.29,target=(0,0,1.55)):
 cam.data.ortho_scale=scale;h._aim(cam,loc,target);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def series(prefix):
 for name,loc in views[:1] if a.quick else views:render(prefix+'_'+name,loc)
series('before_hair')
for o in hair:o.hide_render=True
series('before_bare');render('before_eyes',scale=.165,target=(0,0,1.542),loc=(0,-2,1.542))
# Same displacement on every key preserves all expression deltas, relative relationships and weights.
deltas=[]
for v in skin.data.vertices:
 p=v.co;x=abs(p.x);front=h._smooth((p.y-.028)/.025);d=Vector((0,0,0))
 if p.z<1.535:
  chin=math.exp(-((p.z-1.468)/.013)**2)*math.exp(-(x/.028)**4)*front
  d.z+=.00115*chin
  jaw=math.exp(-((p.z-1.496)/.018)**2)*h._smooth((x-.018)/.025)*front
  d.x=-p.x*.014*jaw
  nose=math.exp(-(p.x/.009)**4-((p.z-1.519)/.007)**2)*front
  d.y-=.00200*nose
 deltas.append(d)
# v17b local surface relaxation softens chin turning, with a strict additional0.8mm cap.
coords=[v.co+d for v,d in zip(skin.data.vertices,deltas)];adj=[set() for _ in coords]
for edge in skin.data.edges:
 i,j=edge.vertices;adj[i].add(j);adj[j].add(i)
relaxed=[p.copy() for p in coords]
for _ in range(2):
 nxt=[p.copy() for p in relaxed]
 for i,p in enumerate(coords):
  if not adj[i]:continue
  w=math.exp(-((p.z-1.474)/.012)**4)*math.exp(-(p.x/.040)**4)*h._smooth((p.y-.025)/.025)
  mean=sum((relaxed[j] for j in adj[i]),Vector())/len(adj[i]);nxt[i]+=(mean-relaxed[i])*(.24*w)
 relaxed=nxt
chin_offsets=[]
for i,(p,q) in enumerate(zip(coords,relaxed)):
 d=q-p
 if d.length>.0008:d*=.0008/d.length
 chin_offsets.append(d.copy());deltas[i]+=d
for k in skin.data.shape_keys.key_blocks:
 for i,d in enumerate(deltas):k.data[i].co+=d
for v,d in zip(skin.data.vertices,deltas):v.co+=d
skin.data.update();skin['v17_change']='Lower-face local offsets applied identically to every shape key; UV, topology, expression deltas, weights retained. No forehead/cap movement.'
# Clean editable calibration surface; no inherited blurry pigment participates in the active graph.
oldmat=skin.material_slots[7].material;mat=oldmat.copy();mat.name='MIA_V17_CleanSkin_ForRegisteredPaint';n=mat.node_tree.nodes;l=mat.node_tree.links;emit=next(n for n in n if n.type=='EMISSION');ramp=next(n for n in n if n.type=='VALTORGB');mix=n.new('ShaderNodeMixRGB');mix.name='MIA_V17_PAINT_BASE_INPUT';mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(.94118,.87843,.85098,1);l.new(ramp.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],emit.inputs[0]);skin.material_slots[7].material=mat
# Fixed UV radial iris shader on the ORIGINAL curved carrier. No camera coordinates or new bitmap.
imat=bpy.data.materials.new('MIA_V17_FixedUV_GrayGreenIris');imat.use_nodes=True;n=imat.node_tree.nodes;n.clear();l=imat.node_tree.links
uv=n.new('ShaderNodeUVMap');uv.uv_map=eyes.data.uv_layers.active.name;sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs[0],sep.inputs[0])
def m(op,a,b=None):
 node=n.new('ShaderNodeMath');node.operation=op
 for i,x in enumerate([a,b]):
  if x is not None:
   if isinstance(x,(int,float)):node.inputs[i].default_value=x
   else:l.new(x,node.inputs[i])
 return node.outputs[0]
x=m('DIVIDE',m('SUBTRACT',m('FRACT',m('MULTIPLY',sep.outputs[0],2)),.5),.252)
y=m('DIVIDE',m('SUBTRACT',sep.outputs[1],.5),.222)
r=m('SQRT',m('ADD',m('MULTIPLY',x,x),m('MULTIPLY',y,y)))
def ramp_node(inp,stops):
 rr=n.new('ShaderNodeValToRGB');rr.color_ramp.interpolation='LINEAR';els=rr.color_ramp.elements
 while len(els)>2:els.remove(els[-1])
 for i,(pos,col) in enumerate(stops):
  e=els[i] if i<2 else els.new(pos);e.position=pos;e.color=col
 l.new(inp,rr.inputs[0]);return rr.outputs[0]
# Muted upper-to-lower iris planes, small pupil and fine outer limbal ring.
grad=ramp_node(sep.outputs[1],[(.28,(.30,.37,.37,1)),(.49,(.14,.19,.20,1)),(.66,(.035,.052,.060,1))])
ring=ramp_node(r,[(.0,(1,1,1,1)),(.86,(1,1,1,1)),(.94,(.27,.30,.31,1)),(1,(.20,.23,.24,1))])
col=n.new('ShaderNodeMixRGB');col.blend_type='MULTIPLY';col.inputs[0].default_value=1;l.new(grad,col.inputs[1]);l.new(ring,col.inputs[2])
py=m('ADD',y,.29);pr=m('SQRT',m('ADD',m('MULTIPLY',x,x),m('MULTIPLY',py,py)));pupil=m('LESS_THAN',pr,.285);pc=n.new('ShaderNodeMixRGB');l.new(pupil,pc.inputs[0]);l.new(col.outputs[0],pc.inputs[1]);pc.inputs[2].default_value=(.018,.026,.031,1)
gx=m('ADD',x,.30);gy=m('ADD',y,.26);gr=m('SQRT',m('ADD',m('MULTIPLY',gx,gx),m('MULTIPLY',gy,gy)));glint=m('LESS_THAN',gr,.075);gc=n.new('ShaderNodeMixRGB');l.new(glint,gc.inputs[0]);l.new(pc.outputs[0],gc.inputs[1]);gc.inputs[2].default_value=(.58,.65,.64,1);em=n.new('ShaderNodeEmission');l.new(gc.outputs[0],em.inputs[0]);tr=n.new('ShaderNodeBsdfTransparent');out=n.new('ShaderNodeOutputMaterial');mx=n.new('ShaderNodeMixShader');alpha=m('LESS_THAN',r,1);l.new(alpha,mx.inputs[0]);l.new(tr.outputs[0],mx.inputs[1]);l.new(em.outputs[0],mx.inputs[2]);l.new(mx.outputs[0],out.inputs[0]);imat.surface_render_method='DITHERED';eyes.material_slots[5].material=imat
trans=bpy.data.materials.new('MIA_V17_LegacyEyeGlintsHidden');trans.use_nodes=True;n=trans.node_tree.nodes;n.clear();t=n.new('ShaderNodeBsdfTransparent');o=n.new('ShaderNodeOutputMaterial');trans.node_tree.links.new(t.outputs[0],o.inputs[0])
for i in [6,8]:eyes.material_slots[i].material=trans
assert eyes.material_slots[1].material.use_backface_culling
# Ink is surface-conforming, static and separate editable geometry.
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());sm=ev.to_mesh();bvh=BVHTree.FromPolygons([v.co for v in sm.vertices],[list(p.vertices) for p in sm.polygons]);ev.to_mesh_clear()
def depth(x,z):
 p=bvh.ray_cast(Vector((x,.25,z)),Vector((0,-1,0)))[0];return p.y if p else None
for o in bpy.data.collections['MIA_V14_FACE_IDENTITY'].objects:
 if 'Brow' in o.name or 'MouthSeam' in o.name:o.hide_render=False;o.hide_viewport=False
 if 'UpperLash' in o.name:
  for i in range(0,len(o.data.vertices),2):
   va,vb=o.data.vertices[i:i+2];center=(va.co.z+vb.co.z)/2
   for v in [va,vb]:v.co.z=center+(v.co.z-center)*1.20;v.co.y=(depth(v.co.x,v.co.z) or v.co.y)+.00045
 if 'MouthSeam' in o.name:
  for v in o.data.vertices:v.co.x*=.94;v.co.y=(depth(v.co.x,v.co.z) or v.co.y)+.0004
col=bpy.data.collections.new('MIA_V17_FACE_SURFACE');scene.collection.children.link(col);ink=h._flat_paper_material('MIA_V17_SingleLowerCrease',(.14,.085,.08,1))
for sign in [-1,1]:
 boundary=[]
 for j in range(100):
  x=.012+j*.00055;zs=[1.528+k*.00015 for k in range(180) if depth(sign*x,1.528+k*.00015) is None]
  if len(zs)>5:boundary.append((x,min(zs)))
 # Use only inner 80 percent, a single narrow lower crescent, tapered ends.
 boundary=boundary[5:-8]
 for _ in range(4):boundary=[boundary[0]]+[(boundary[j][0],(boundary[j-1][1]+2*boundary[j][1]+boundary[j+1][1])/4) for j in range(1,len(boundary)-1)]+[boundary[-1]]
 verts=[]
 for j,(x,z) in enumerate(boundary):
  t=j/max(1,len(boundary)-1);w=.00030*math.sin(math.pi*t)**.7;z-=.00135
  for zz in [z-w/2,z+w/2]:verts.append((sign*x,(depth(sign*x,zz) or .06)+.00025,zz))
 mesh=bpy.data.meshes.new('MIA_V17_CreaseMesh');mesh.from_pydata(verts,[],[(i,i+1,i+3,i+2) for i in range(0,len(verts)-2,2)]);mesh.materials.append(ink);ob=bpy.data.objects.new('MIA_V17_SingleUnderEyeCrease_'+str(sign),mesh);col.objects.link(ob);ob.matrix_world=skin.matrix_world.copy();ob['scope']='Static projected surface ink; not final blink rig'
for o in hair:o.hide_render=False
cam.data.ortho_scale=.29;h._aim(cam,(0,-2,1.55),(0,0,1.55));native=OUT/'Mia_FaceSurface_v17b.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native),relative_remap=False)
hairnames=[o.name for o in hair];bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera;skin=bpy.data.objects['MIA_V14_SculptedSkin'];eyes=bpy.data.objects['MIA_V14_EyeSurface'];hair=[bpy.data.objects[name] for name in hairnames];series('after_hair')
for o in hair:o.hide_render=True
series('after_bare')
for name,loc in views[:1] if a.quick else views:render('after_eyes_'+name,loc=(loc[0],loc[1],1.542),scale=.165,target=(0,0,1.542))
# Clean neutral front for fresh raster creation; this image is an actual saved-native render.
render('calibration_front',scale=.29)
# Actual visible UV checker. Shader checker, not a newly painted bitmap.
checker=bpy.data.materials.new('DIAG_V17_UVChecker');checker.use_nodes=True;n=checker.node_tree.nodes;n.clear();l=checker.node_tree.links;u=n.new('ShaderNodeTexCoord');c=n.new('ShaderNodeTexChecker');c.inputs['Scale'].default_value=32;c.inputs['Color1'].default_value=(.06,.12,.20,1);c.inputs['Color2'].default_value=(.75,.65,.45,1);l.new(u.outputs['UV'],c.inputs[0]);e=n.new('ShaderNodeEmission');l.new(c.outputs[0],e.inputs[0]);o=n.new('ShaderNodeOutputMaterial');l.new(e.outputs[0],o.inputs[0]);saved=skin.material_slots[7].material;ei=eyes.material_slots[5].material;skin.material_slots[7].material=checker;eyes.material_slots[5].material=checker;render('uvchecker_front');render('uvchecker_left',(1.4,-1.4,1.55));skin.material_slots[7].material=saved;eyes.material_slots[5].material=ei
# Isolated eyes preserve true depth in the same material; no skin/ink/hair occlusion.
vis={o.name:o.hide_render for o in scene.objects if o.type=='MESH'}
for o in scene.objects:
 if o.type=='MESH':o.hide_render=o!=eyes
for name,loc in views[:1] if a.quick else views:render('isolated_eyes_'+name,loc=(loc[0],loc[1],1.542),scale=.165,target=(0,0,1.542))
for name,v in vis.items():bpy.data.objects[name].hide_render=v
after={o.name:snapshot(o) for o in scene.objects if o.type=='MESH'};changed=[k for k in before if before[k]!=after[k]]
report={'source':str(SOURCE),'source_sha_before':source_sha,'source_sha_after':sha(SOURCE),'native':str(native),'native_sha':sha(native),'script_sha':sha(Path(__file__)),'changed_existing_meshes':changed,'before':before,'after':after,'all_uv_topology_weights_preserved':all(all(before[k][f]==after[k][f] for f in ['uv','topology','weights']) for k in before),'eye_carrier_geometry_unchanged':before[eyes.name]['co']==after[eyes.name]['co'],'sclera_backface_culling':eyes.material_slots[1].material.use_backface_culling,'max_skin_offset_m':max(d.length for d in deltas),'v17b_additional_nose_max_m':.00135,'v17b_chin_relax_max_m':max(d.length for d in chin_offsets),'v17b_scope':'Original v17 eyes/materials/lashes unchanged; only bounded nose and chin offsets added consistently to every skin key','face_base':'Clean normal-response skin pending root registered fixed-UV paint; inherited v15 textures packed as archive, disconnected.','iris':'Original UV and curved carrier. Periodic UV ellipse radii .126U/.222V versus source ~.115U/.26V; smaller pupil radius .285; muted gray-green gradient and fine limbal ring. Shader nodes, no raster fabrication.','calibration':{'file':'calibration_front.png','camera':[0,-2,1.55],'target':[0,0,1.55],'orthographic_scale':.29,'resolution':a.resolution,'hair_hidden':True},'limits':['Neutral/static only; no blink/rig claim','Clean skin calibration awaits new fixed-UV paint','No hair/body/headcap edits','Single under-eye crease is static geometry','Source archived oral parts remain hidden; expression corner-fit work outstanding']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('V17_DONE',json.dumps({k:v for k,v in report.items() if k not in ['before','after']}))





