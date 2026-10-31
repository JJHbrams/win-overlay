"""Supplied flat imagegen art -> actual fixed UV albedo; shared scene-light contract.
No pixel artwork drawing, geometry edits, old beauty division, or camera-dependent runtime projection.
"""
import bpy,sys,math,json,hashlib,struct,argparse,shutil,ast
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent));import review_setup as r
sys.path.insert(0,str(r.CANON/'asset/mia/blender/mia-reference-finish-v22'));import skin_light_contract as contract
ap=argparse.ArgumentParser();ap.add_argument('--source',required=True);ap.add_argument('--plate',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();PLATE=Path(a.plate).resolve();OUT=Path(a.output_dir).resolve();OUT.mkdir(parents=True,exist_ok=True)
BASE=np.array(contract.BASE_LINEAR[:3],np.float32);SIZE=2048
def gh(o):
 h=hashlib.sha256();m=o.data;h.update(np.array([tuple(v.co) for v in m.vertices],np.float32).tobytes())
 for p in m.polygons:h.update(np.array(p.vertices,np.int32).tobytes())
 for l in m.uv_layers:h.update(np.array([tuple(v.uv) for v in l.data],np.float32).tobytes())
 for v in m.vertices:
  for g in v.groups:h.update(struct.pack('<IIf',v.index,g.group,g.weight))
 if m.shape_keys:
  for k in m.shape_keys.key_blocks:h.update(k.name.encode());h.update(np.array([tuple(v.co) for v in k.data],np.float32).tobytes())
 return h.hexdigest()
def flat(name,color):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*color,1);o=n.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],o.inputs[0]);return m
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def sample(img,u,v):
 xx=np.clip(u*(img.shape[1]-1),0,img.shape[1]-1);yy=np.clip(v*(img.shape[0]-1),0,img.shape[0]-1);x0=xx.astype(int);y0=yy.astype(int);x1=np.minimum(x0+1,img.shape[1]-1);y1=np.minimum(y0+1,img.shape[0]-1);fx=(xx-x0)[...,None];fy=(yy-y0)[...,None];return (img[y0,x0]*(1-fx)+img[y0,x1]*fx)*(1-fy)+(img[y1,x0]*(1-fx)+img[y1,x1]*fx)*fy
def load_raw(path,name):
 im=bpy.data.images.load(str(path),check_existing=False);im.name=name;im.colorspace_settings.name='Non-Color';px=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4);return im,px
def decode(px):return np.where(px<=.04045,px/12.92,((px+.055)/1.055)**2.4)
def encode(px):return np.where(px<=.0031308,px*12.92,1.055*np.maximum(px,0)**(1/2.4)-.055)
def save(name,px,filename,float_buffer=False):
 im=bpy.data.images.new(name,width=SIZE,height=SIZE,alpha=True,float_buffer=float_buffer);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(px.astype(np.float32).ravel());im.filepath_raw=str(OUT/filename);im.file_format='OPEN_EXR' if float_buffer else 'PNG';im.save();im.pack();im.use_fake_user=True;im.filepath='//'+filename;return im
sh=r.sha(SOURCE);ph=r.sha(PLATE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;skin=bpy.data.objects['MIA_V14_SculptedSkin'];before={o.name:gh(o) for o in s.objects if o.type=='MESH'};oldpacked={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file};visibility={o.name:o.hide_render for o in s.objects}
for i in bpy.data.images:
 if i.packed_file:i.use_fake_user=True
r.hairhide();v=dict(id='front',yaw=0,elevation=0,roll=0);r.camera(s,v);s.render.resolution_x=s.render.resolution_y=SIZE;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
matstate={o.name:[x.material for x in o.material_slots] for o in s.objects if o.type=='MESH' and not o.hide_render};white=flat('V22_DIAG_VisibleSkin',(1,1,1));black=flat('V22_DIAG_Occluder',(0,0,0));bc=black.copy();bc.use_backface_culling=True
for name,mats in matstate.items():
 o=bpy.data.objects[name]
 for i,m in enumerate(mats):
  if o==skin:o.material_slots[i].material=white
  elif name=='MIA_V14_EyeSurface' and i in [6,8]:pass
  else:o.material_slots[i].material=bc if m and m.use_backface_culling else black
s.render.filepath=str(OUT/'actual_front_skin_visibility.png');bpy.ops.render.render(write_still=True)
for name,mats in matstate.items():
 for slot,mat in zip(bpy.data.objects[name].material_slots,mats):slot.material=mat
plateim,plate=load_raw(PLATE,'MIA_V22_SOURCE_ART_NOT_MODEL_RENDER');maskim,vis=load_raw(OUT/'actual_front_skin_visibility.png','MIA_V22_ProjectionVisibility');plate[:,:,:3]=decode(plate[:,:,:3]);h,w=plate.shape[:2]
# Global flat-base color calibration only: no old model beauty/shading division.
neutral=np.median(plate[int(h*.60):int(h*.70),int(w*.43):int(w*.57),:3],axis=(0,1));gain=BASE/neutral;plate[:,:,:3]=np.clip(plate[:,:,:3]*gain,0,1)
paint=np.ones((SIZE,SIZE,4),np.float32);paint[:,:,:3]=BASE;mask=np.ones_like(paint);mask[:,:,:3]=0;coverage=np.zeros((SIZE,SIZE),np.uint8)
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();uv=me.uv_layers.active.data;mw=ev.matrix_world;nm=mw.to_3x3().inverted().transposed();points=np.array([tuple(mw@v.co) for v in me.vertices]);normals=np.array([tuple((nm@v.normal).normalized()) for v in me.vertices]);count=0
for tri in me.loop_triangles:
 p=points[list(tri.vertices)];nn=normals[list(tri.vertices)];t=np.array([tuple(uv[i].uv) for i in tri.loops])*SIZE;lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),SIZE-1)
 if np.any(hi<lo):continue
 yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
 if abs(den)<1e-8:continue
 aa=((t[1,1]-t[2,1])*(xx+.5-t[2,0])+(t[2,0]-t[1,0])*(yy+.5-t[2,1]))/den;bb=((t[2,1]-t[0,1])*(xx+.5-t[2,0])+(t[0,0]-t[2,0])*(yy+.5-t[2,1]))/den;cc=1-aa-bb;inside=(aa>=0)&(bb>=0)&(cc>=0)
 xyz=aa[...,None]*p[0]+bb[...,None]*p[1]+cc[...,None]*p[2];norm=aa[...,None]*nn[0]+bb[...,None]*nn[1]+cc[...,None]*nn[2];x=np.abs(xyz[...,0]);z=xyz[...,2];pu=.5+xyz[...,0]/.29;pv=.5+(z-1.55)/.29
 # Measured source mouth center .706 vs actual closed seam .700: local6px/1000 registration, original PNG unchanged.
 offset=-.006*np.exp(-((z-1.492)/.008)**4)*smooth((.027-x)/.012)
 offset+=-.007*np.exp(-((z-1.538)/.013)**4)*smooth((x-.016)/.010)*smooth((.071-x)/.012)
 target=sample(plate,pu,pv+offset);visible=sample(vis,pu,pv)[...,0]
 weight=smooth((-norm[...,1]-.10)/.55)*smooth((.077-x)/.016)*smooth((z-1.468)/.012)*smooth((1.594-z)/.015)*smooth((-xyz[...,1]-.022)/.024)*smooth((visible-.12)/.75)*target[...,3]
 # Reject generated eye whites/gray carrier colors from cavity-adjacent skin; real eye geometry remains independent.
 eyezone=(x>.016)&(x<.071)&(z>1.533)&(z<1.553);neutral_eye=(target[:,:,:3].max(-1)-target[:,:,:3].min(-1)<.17)&(target[:,:,1]>=target[:,:,0]*.94)&(target[:,:,2]>=target[:,:,0]*.85)
 whitezone=(x>.016)&(x<.071)&(z>1.525)&(z<1.553);source_white=target[:,:,:3].min(-1)>.72
 weight=np.where((eyezone&neutral_eye)|(whitezone&source_white),0,weight)
 rgb=BASE*(1-weight[...,None])+target[...,:3]*weight[...,None];sl=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1];paint[sl][:,:,:3]=np.where(inside[...,None],rgb,paint[sl][:,:,:3]);mask[sl][:,:,:3]=np.where(inside[...,None],weight[...,None],mask[sl][:,:,:3]);coverage[sl][inside]=1;count+=int((inside&(weight>.01)).sum())
ev.to_mesh_clear()
# Technical UV island padding, not source-art retouching.
for _ in range(8):
 cnt=np.zeros_like(coverage,dtype=np.float32);summ=np.zeros((SIZE,SIZE,3),np.float32)
 for axis,shift in [(0,-1),(0,1),(1,-1),(1,1)]:mm=np.roll(coverage,shift,axis);summ+=np.roll(paint[:,:,:3],shift,axis)*mm[...,None];cnt+=mm
 take=(coverage==0)&(cnt>0);paint[:,:,:3][take]=summ[take]/cnt[take,None];coverage[take]=1
atlas=save('MIA_V22_Face_BaseColor_LINEAR_2048',paint,'Face_BaseColor_LINEAR_2048.exr',True);encoded=paint.copy();encoded[:,:,:3]=encode(encoded[:,:,:3]);save('MIA_V22_Face_BaseColor_sRGB_EXPORT',encoded,'Face_BaseColor_sRGB_2048.png');save('MIA_V22_Face_PaintRegion_MASK',mask,'Face_PaintRegion_MASK_2048.png')
fm=contract.build_skin_material('MIA_V22_Face_ActualLight_NewUV');nodes=fm.node_tree.nodes;links=fm.node_tree.links;u=nodes.new('ShaderNodeUVMap');u.uv_map=skin.data.uv_layers.active.name;tex=nodes.new('ShaderNodeTexImage');tex.name='MIA_V22_FULL_LINEAR_ALBEDO';tex.image=atlas;links.new(u.outputs[0],tex.inputs['Vector']);links.new(tex.outputs['Color'],nodes['PigmentTimesControlledLight'].inputs[1]);skin.material_slots[7].material=fm
body=bpy.data.objects['MIA_V06_BODY_SKIN'];bodyim=bpy.data.images['MIA_V13_BodySkin_UV_2048'];body.material_slots[0].material=contract.build_skin_material('MIA_V22_Body_CommonLight_Preview',bodyim)
for name,hidden in visibility.items():bpy.data.objects[name].hide_render=hidden
for o in s.objects:
 if o.type=='MESH' and any(t in o.name for t in ['Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
plateim.pack();plateim.use_fake_user=True;plateim.filepath=str(PLATE)
# Shared rig implementation reused from read-only evidence helper, without executing its script body.
tree=ast.parse((r.OUT/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rig'],type_ignores=[]),'common-rig','exec'));rig(s)
r.camera(s,v)
if hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):s.eevee.taa_render_samples=128
# Bounded UV shader refinement: clearer limbal rim and a reflected lower arc.
eyes=bpy.data.objects['MIA_V14_EyeSurface'];imat=eyes.material_slots[5].material.copy();imat.name='MIA_V22_Iris_LowerArc_Rim';n=imat.node_tree.nodes;l=imat.node_tree.links
ring=next(x for x in n if x.type=='VALTORGB' and len(x.color_ramp.elements)==4);radius=ring.inputs[0].links[0].from_socket
for e,(pos,col) in zip(ring.color_ramp.elements,[(0,(1,1,1,1)),(.84,(1,1,1,1)),(.92,(.18,.23,.25,1)),(1,(.13,.18,.20,1))]):e.position=pos;e.color=col
def ramp(inp,stops,name):
 node=n.new('ShaderNodeValToRGB');node.name=name;node.color_ramp.interpolation='EASE';els=node.color_ramp.elements
 while len(els)>1:els.remove(els[-1])
 for i,(p,c) in enumerate(stops):e=els[0] if i==0 else els.new(p);e.position=p;e.color=(c,c,c,1)
 l.new(inp,node.inputs[0]);return node.outputs[0]
arc=ramp(radius,[(0,0),(.62,0),(.73,.65),(.80,.85),(.87,0),(1,0)],'MIA_V22_LowerArc_RadialBand')
sep=next(x for x in n if x.type=='SEPXYZ');lower=ramp(sep.outputs[1],[(0,1),(.34,1),(.41,0),(1,0)],'MIA_V22_LowerArc_VMask')
mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(arc,mul.inputs[0]);l.new(lower,mul.inputs[1])
col=next(x for x in n if x.type=='MIX_RGB' and x.blend_type=='MULTIPLY');dest=[x.to_socket for x in list(l) if x.from_node==col]
mix=n.new('ShaderNodeMixRGB');mix.name='MIA_V22_ReflectedLowerArc';l.new(mul.outputs[0],mix.inputs[0]);l.new(col.outputs[0],mix.inputs[1]);mix.inputs[2].default_value=(.65,.74,.74,1)
for socket in dest:l.new(mix.outputs[0],socket)
eyes.material_slots[5].material=imat

after={o.name:gh(o) for o in s.objects if o.type=='MESH'};assert before==after
native=OUT/'Mia_FaceFinish_v22.blend';assert not native.exists();bpy.ops.wm.save_as_mainfile(filepath=str(native));nh=r.sha(native);bpy.ops.wm.open_mainfile(filepath=str(native));assert {o.name:gh(o) for o in bpy.context.scene.objects if o.type=='MESH'}==before
for name,digest in oldpacked.items():assert hashlib.sha256(bpy.data.images[name].packed_file.data).hexdigest()==digest,name
source_manifest=json.loads((SOURCE.parent/'manifest.json').read_text());report={'source':source_manifest['source'],'geometry_source':r.artifact(SOURCE),'native':r.artifact(native),'plate':r.artifact(PLATE),'plate_role':'IMAGEGEN source artwork, not a model render','recipe_sha256':r.sha(__file__),'shared_shader_helper':r.artifact(contract.__file__),'geometry_uv_keys_weights_unchanged_during_paint':before==after,'geometry_hashes':before,'original_packed_count':len(oldpacked),'original_packed_exact':True,'base_linear':BASE.tolist(),'sampled_flat_plate_neutral_linear':neutral.tolist(),'flat_base_calibration_gain':gain.tolist(),'atlas':'Face_BaseColor_LINEAR_2048.exr Non-Color, full linear albedo/graphic makeup. PNG is explicitly sRGB encoded export, not active numeric multiplier.','route':'Explicit skin UV -> new full linear albedo -> shared actual-scene diffuse luminance light ramp -> Emission. Body slot0 common root helper with legacy Body pigment; Body geometry unchanged in this phase.','no_old_beauty_ratio':True,'mouth_registration':'Source y=.706 to actual seam y=.700 via local6px/1000 UV sampling offset; original PNG unchanged','eye_registration':'Local source sampling -0.007V around z1.538, matching inherited registered plate; original PNG unchanged','finish4_scope':'Surface-only new controlled under-eye pigment plus UV iris lower reflected arc/stronger limbal rim. All geometry frozen from finish3.','neutral_eye_filter':'Blue-gray source iris colors rejected, warm brown/mauve pigment retained; actual visibility and white rejection retained','painted_uv_samples':count,'remaining_issues':['Generated pigment is graphic artwork, not physical reflectance measurement','Source outline/yaw/gaze correspondence uncertain; full art review required','Fixed under-eye/nose marks do not animate independently','Inherited uneven triangular skin topology/close expression limitations remain']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2));(OUT/'exact-recipe.py').write_bytes(Path(__file__).read_bytes());shutil.copyfile(SOURCE.parent/'source-view-definitions.json',OUT/'source-view-definitions.json');assert r.sha(SOURCE)==sh and r.sha(PLATE)==ph;print('PAINT_DONE',nh)
