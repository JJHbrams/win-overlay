"""Transfer supplied v17 IMAGEGEN paint source to fixed skin UV. No geometry/art drawing."""
import bpy,sys,json,hashlib,struct,argparse,shutil
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(Path(__file__).resolve().parent));import refine_mia_head_v06 as h
ap=argparse.ArgumentParser();ap.add_argument('--source',default=str(ROOT/'asset/mia/blender/mia-face-surface-v17/Mia_FaceSurface_v17.blend'));ap.add_argument('--output-dir',default=str(ROOT/'asset/mia/blender/mia-face-surface-v17/painted'));ap.add_argument('--plate',default=r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/front-paint-source-not-model-render.png');ap.add_argument('--resolution',type=int,default=1000);a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);SOURCE=Path(a.source).resolve();OUT=Path(a.output_dir).resolve();PLATE=Path(a.plate).resolve();OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def gh(o):
 hh=hashlib.sha256();d=o.data;hh.update(np.array([tuple(v.co) for v in d.vertices],np.float32).tobytes())
 for p in d.polygons:hh.update(np.array(p.vertices,np.int32).tobytes())
 for layer in d.uv_layers:hh.update(np.array([tuple(v.uv) for v in layer.data],np.float32).tobytes())
 for v in d.vertices:
  for g in v.groups:hh.update(struct.pack('<IIf',v.index,g.group,g.weight))
 if d.shape_keys:
  for k in d.shape_keys.key_blocks:hh.update(k.name.encode());hh.update(struct.pack('<f',k.value));hh.update(np.array([tuple(v.co) for v in k.data],np.float32).tobytes())
 return hh.hexdigest()
source_sha=sha(SOURCE);plate_sha=sha(PLATE);copied=OUT/'front-paint-source-not-model-render.png'
if copied!=PLATE:shutil.copyfile(PLATE,copied)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;cam=scene.camera;skin=bpy.data.objects['MIA_V14_SculptedSkin'];before={o.name:gh(o) for o in scene.objects if o.type=='MESH'};base=np.array([.94118,.87843,.85098],np.float32)
scene.render.resolution_x=scene.render.resolution_y=a.resolution;scene.render.resolution_percentage=100
views=[('front',(0,-2,1.55)),('left',(1.4,-1.4,1.55)),('right',(-1.4,-1.4,1.55)),('profile',(2,0,1.55))]
def render(name,loc=(0,-2,1.55)):
 cam.data.ortho_scale=.29;h._aim(cam,loc,(0,0,1.55));scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
def series(prefix):
 for name,loc in views:render(prefix+'_'+name,loc)
hair_collection_names={o.name for c in bpy.data.collections if 'HAIR' in c.name.upper() for o in c.all_objects}
hair=[o for o in scene.objects if o.type=='MESH' and not o.hide_render and (o.name in hair_collection_names or any(t in o.name for t in ['Hair','HAIR','PIXAL']))];hairnames=[o.name for o in hair];ink=[o for o in scene.objects if o.type=='MESH' and any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease'])];inkstate={o.name:o.hide_render for o in ink}
series('before_hair')
for o in hair:o.hide_render=True
series('before_bare')
for o in ink:o.hide_render=True
render('fresh_calibration_noink')
# Actual visibility mask: visible skin white, other real occluders black, original hidden cards remain transparent.
matstate={o.name:[s.material for s in o.material_slots] for o in scene.objects if o.type=='MESH' and not o.hide_render};white=h._flat_paper_material('DIAG_V17_VisibleSkinWhite',(1,1,1,1));black=h._flat_paper_material('DIAG_V17_OccluderBlack',(0,0,0,1));blackcull=black.copy();blackcull.use_backface_culling=True
for name,mats in matstate.items():
 o=bpy.data.objects[name]
 for i,m in enumerate(mats):
  if o==skin:o.material_slots[i].material=white
  elif o.name=='MIA_V14_EyeSurface' and i in [6,8]:pass
  else:o.material_slots[i].material=blackcull if m and m.use_backface_culling else black
world=scene.world;scene.world=world.copy();scene.world.use_nodes=True
for n in scene.world.node_tree.nodes:
 if n.type=='BACKGROUND':n.inputs['Color'].default_value=(0,0,0,1);n.inputs['Strength'].default_value=0
vs=scene.view_settings;settings=(vs.view_transform,vs.look,vs.exposure,vs.gamma);vs.view_transform='Standard';vs.look='None';vs.exposure=0;vs.gamma=1;scene.render.resolution_x=scene.render.resolution_y=2048;render('visible_skin_mask_2048')
vs.view_transform,vs.look,vs.exposure,vs.gamma=settings;scene.world=world;scene.render.resolution_x=scene.render.resolution_y=a.resolution
for name,mats in matstate.items():
 for slot,mat in zip(bpy.data.objects[name].material_slots,mats):slot.material=mat
for o in ink:o.hide_render=inkstate[o.name]
def load(path,name,space='sRGB'):
 im=bpy.data.images.load(str(path),check_existing=False);im.name=name;im.colorspace_settings.name=space;px=np.array(im.pixels[:],np.float32).reshape(im.size[1],im.size[0],4)
 if space=='sRGB':px[:,:,:3]=np.where(px[:,:,:3]<=.04045,px[:,:,:3]/12.92,((px[:,:,:3]+.055)/1.055)**2.4)
 return im,px
plateim,plate=load(copied,'MIA_V17_IMAGEGEN_SOURCE_NOT_MODEL_RENDER');calim,cal=load(OUT/'fresh_calibration_noink.png','MIA_V17_FreshGeometryCalibration');maskim,vis=load(OUT/'visible_skin_mask_2048.png','MIA_V17_ActualFrontVisibility','Non-Color')
# Keep actual high-resolution visibility; extra erosion creates a pale waterline gap.
mask=vis[:,:,0].copy()
# No erosion: geometric visibility already excludes the eye cavity.
vis[:,:,:3]=mask[:,:,None]
SIZE=2048;paint=np.ones((SIZE,SIZE,4),np.float32);paint[:,:,:3]=base;coverage=np.zeros((SIZE,SIZE),np.uint8);preview=np.ones_like(paint);preview[:,:,:3]=0
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());sm=ev.to_mesh();sm.calc_loop_triangles();uv=sm.uv_layers.active.data;mw=ev.matrix_world;nm=mw.to_3x3().inverted().transposed();worldco=np.array([tuple(mw@v.co) for v in sm.vertices]);normal=np.array([tuple((nm@v.normal).normalized()) for v in sm.vertices])
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
def sample(img,u,v):
 xx=np.clip(u*(img.shape[1]-1),0,img.shape[1]-1);yy=np.clip(v*(img.shape[0]-1),0,img.shape[0]-1);x0=xx.astype(int);y0=yy.astype(int);x1=np.minimum(x0+1,img.shape[1]-1);y1=np.minimum(y0+1,img.shape[0]-1);fx=(xx-x0)[...,None];fy=(yy-y0)[...,None];return (img[y0,x0]*(1-fx)+img[y0,x1]*fx)*(1-fy)+(img[y1,x0]*(1-fx)+img[y1,x1]*fx)*fy
count=0
for tri in sm.loop_triangles:
 p=worldco[list(tri.vertices)];nn=normal[list(tri.vertices)];t=np.array([tuple(uv[i].uv) for i in tri.loops])*SIZE;lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),SIZE-1)
 if np.any(hi<lo):continue
 yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];den=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
 if abs(den)<1e-8:continue
 aa=((t[1,1]-t[2,1])*(xx+.5-t[2,0])+(t[2,0]-t[1,0])*(yy+.5-t[2,1]))/den;bb=((t[2,1]-t[0,1])*(xx+.5-t[2,0])+(t[0,0]-t[2,0])*(yy+.5-t[2,1]))/den;cc=1-aa-bb;inside=(aa>=0)&(bb>=0)&(cc>=0)
 xyz=aa[...,None]*p[0]+bb[...,None]*p[1]+cc[...,None]*p[2];norm=aa[...,None]*nn[0]+bb[...,None]*nn[1]+cc[...,None]*nn[2];pu=.5+xyz[...,0]/.29;pv=.5+(xyz[...,2]-1.55)/.29;x=np.abs(xyz[...,0]);z=xyz[...,2]
 # Observed source mouth seam y~.701 vs geometry.6974: local max4px correction at1000px only.
 shift=-.004*np.exp(-((z-1.493)/.010)**4)*smooth((.028-x)/.012);target=sample(plate,pu,pv+shift)[...,:3];ref=sample(cal,pu,pv)[...,:3];visible=sample(vis,pu,pv)[...,0]
 weight=smooth((-norm[...,1]-.12)/.60)*smooth((.079-x)/.016)*smooth((z-1.469)/.012)*smooth((1.594-z)/.014)*smooth((-xyz[...,1]-.022)/.022)*smooth((visible-.15)/.70)
 # Source-eye neutral whites/gray iris cannot become skin pigment if tiny artwork/aperture mismatch remains.
 eyezone=(x>.017)&(x<.064)&(z>1.532)&(z<1.548);neutral=(target.max(-1)-target.min(-1)<.115)&(target.mean(-1)>.12);weight=np.where(eyezone&neutral,0,weight)
 ratio=np.clip((target+.006)/(ref+.006),.015,1.35);color=np.clip(base*ratio,0,1);rgb=base*(1-weight[...,None])+color*weight[...,None];sl=np.s_[lo[1]:hi[1]+1,lo[0]:hi[0]+1];paint[sl][:,:,:3]=np.where(inside[...,None],rgb,paint[sl][:,:,:3]);preview[sl][:,:,:3]=np.where(inside[...,None],weight[...,None],preview[sl][:,:,:3]);coverage[sl][inside]=1;count+=int((inside&(weight>.01)).sum())
ev.to_mesh_clear()
# Technical atlas island padding only.
for _ in range(8):
 cnt=np.zeros_like(coverage,dtype=np.float32);summ=np.zeros((SIZE,SIZE,3),np.float32)
 for axis,shift in [(0,-1),(0,1),(1,-1),(1,1)]:mm=np.roll(coverage,shift,axis);summ+=np.roll(paint[:,:,:3],shift,axis)*mm[...,None];cnt+=mm
 take=(coverage==0)&(cnt>0);paint[:,:,:3][take]=summ[take]/cnt[take,None];coverage[take]=1
def save(name,px,filename):
 im=bpy.data.images.new(name,width=SIZE,height=SIZE,alpha=True);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(px.ravel());im.filepath_raw=str(OUT/filename);im.file_format='PNG';im.save();im.pack();im.filepath='//'+filename;return im
atlas=save('MIA_V17_FixedUV_FacePigment',paint,'Mia_FacePaint_v17_2048.png');save('MIA_V17_TransferMask',preview,'transfer_mask_2048.png');mat=skin.material_slots[7].material.copy();mat.name='MIA_V17_FixedUV_PaintedSkin';tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.name='MIA_V17_FIXED_UV_PAINT';tex.image=atlas;uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map=skin.data.uv_layers.active.name;mat.node_tree.links.new(uvnode.outputs[0],tex.inputs['Vector']);mat.node_tree.links.new(tex.outputs[0],mat.node_tree.nodes['MIA_V17_PAINT_BASE_INPUT'].inputs[1]);skin.material_slots[7].material=mat
hidden=[]
for o in ink:
 if any(s in o.name for s in ['Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True;o.hide_viewport=True;hidden.append(o.name)
for o in hair:o.hide_render=False
plateim.pack();plateim.filepath='//front-paint-source-not-model-render.png';cam.data.ortho_scale=.29;h._aim(cam,(0,-2,1.55),(0,0,1.55));native=OUT/'Mia_FacePainted_v17.blend';bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(native),relative_remap=False)
bpy.ops.wm.open_mainfile(filepath=str(native));scene=bpy.context.scene;cam=scene.camera;series('after_hair')
for name in hairnames:bpy.data.objects[name].hide_render=True
series('after_bare');after={o.name:gh(o) for o in scene.objects if o.type=='MESH'}
report={'source':str(SOURCE),'source_sha_before':source_sha,'source_sha_after':sha(SOURCE),'plate':str(PLATE),'plate_sha':plate_sha,'plate_label':'IMAGEGEN source artwork, NOT a model render. Original pixels copied unchanged.','native':str(native),'native_sha':sha(native),'script_sha':sha(Path(__file__)),'all_mesh_coords_uv_keys_weights_match':before==after,'geometry_hashes_before':before,'geometry_hashes_after':after,'atlas':{'image':'MIA_V17_FixedUV_FacePigment','size':[SIZE,SIZE],'packed':True,'color_space':'Non-Color','runtime':'Explicit skin UVMap -> image -> MIA_V17_PAINT_BASE_INPUT.inputs[1] -> multiply normal ramp -> Emission'},'hidden_replaced_ink':hidden,'bake':'Evaluated actual skin UV triangle raster, linear base*(target+.006)/(fresh noink calibration+.006), ratio bounded .015..1.35. PNG byte pixels experimentally confirmed encoded despite sRGB image metadata; explicit standard sRGB decoding once before ratio; output linear atlas Non-Color. Approximate under inherited display transform, not physical albedo recovery.','mask':'Fresh2048 visible skin white emission mask, actual occluders black, black world; antialiased coverage plus front normal/anatomical fade and bright-neutral eye rejection; dark lash ink is retained.','registration':'Only mouth localized -0.004 image V max at worldz1.493, x<.028; no global or inherited v15 offset. Source raster unchanged.','written_uv_samples':count,'limitations':['Fixed painted marks remain attached to UV, not dynamically lit intrinsic albedo.','Original silhouette/ear/headcap/neck/body remain base; hair is temporary context.','No geometry, topology, UV, keys, weights or rig changes.','Art review remains required; no automatic identity/fullcharacter PASS.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('V17_PAINT_DONE',json.dumps({k:v for k,v in report.items() if 'geometry_hashes' not in k}))


