import bpy,numpy as np,json,hashlib
from pathlib import Path
O=Path(__file__).parent;OUT=O/'face-final-r3';bpy.ops.wm.open_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'));skin=bpy.data.objects['MIA_V27_ContinuousSkin'];master=bpy.data.objects['MIA_V27_Foundation_Face'];p=np.array([v.co[:] for v in master.data.shape_keys.key_blocks[0].data]);audit=json.loads((OUT/'eye-controls-audit.json').read_text());paths=[]
for side in [-1,1]:
 up=next(r['indices'] for r in audit['actual_arc_targets'] if r['side']==side and r['arc']=='upper');lo=next(r['indices'] for r in audit['actual_arc_targets'] if r['side']==side and r['arc']=='lower');ui=np.argsort(p[up,0]);li=np.argsort(p[lo,0]);paths.append((p[np.array(up)[ui]],p[np.array(lo)[li]]))
W=2048;base=np.array([.82,.63,.55]);pixels=np.ones((W,W,4),np.float32);pixels[:,:,:3]=base;mask=np.zeros((W,W),np.float32);crease_mask=np.zeros((W,W),np.float32)
raw=np.load(O/'skin-boundaries.npz',allow_pickle=True);mouth=np.array(next(v for v in raw['loops'] if len(v)==50),int);mouthcx=p[mouth,0].mean();mouthrad=max(abs(p[mouth,0]-mouthcx));mouthcoef=np.polyfit((p[mouth,0]-mouthcx)/mouthrad,p[mouth,2],2);nosepoints=p[(np.abs(p[:,0])<.008)&(p[:,2]>1.505)&(p[:,2]<1.53)];nosetip=nosepoints[np.argmin(nosepoints[:,1])];nostril_z=float(nosetip[2]-.0011)
def pigment(q):
 col=np.broadcast_to(base,(len(q),3)).copy();fat=np.zeros(len(q));fold=np.zeros(len(q));front=np.clip((-q[:,1]-.025)/.02,0,1)
 for up,lo in paths:
  xmin=max(up[0,0],lo[0,0]);xmax=min(up[-1,0],lo[-1,0]);u=(q[:,0]-xmin)/(xmax-xmin);gate=np.where((u>0)&(u<1),np.sin(np.pi*np.clip(u,0,1))**.6,0);lz=np.interp(q[:,0],lo[:,0],lo[:,2]);uz=np.interp(q[:,0],up[:,0],up[:,2]);below=lz-q[:,2]
  band=np.exp(-.5*((below-.0033)/.0042)**2)*np.clip((below+.0004)/.0013,0,1)*gate*front
  fat=np.maximum(fat,band)
  f=np.exp(-.5*((q[:,2]-uz-.0064)/.00055)**2)*gate*front
  fold=np.maximum(fold,f)
 col=col*(1-.64*fat[:,None])+np.array([.35,.205,.19])*(.64*fat[:,None]);col=col*(1-.48*fold[:,None])+np.array([.27,.17,.16])*(.48*fold[:,None])
 u=(q[:,0]-mouthcx)/mouthrad;seam=np.polyval(mouthcoef,u);lip=np.exp(-.5*((q[:,2]-seam)/.00030)**2)*np.where(abs(u)<1,np.maximum(1-u*u,0)**.3,0)*front;col=col*(1-.65*lip[:,None])+np.array([.22,.12,.11])*(.65*lip[:,None])
 nostril=np.zeros(len(q))
 for sign in [-1,1]:nostril=np.maximum(nostril,np.exp(-.5*((q[:,0]-sign*.0022)/.00048)**2-.5*((q[:,2]-nostril_z)/.00028)**2)*front)
 col=col*(1-.42*nostril[:,None])+np.array([.22,.12,.105])*(.42*nostril[:,None])
 return col,fat,fold
bpy.context.view_layer.update();ev=skin.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();uv=me.uv_layers['UVMap'];positions=np.array([ev.matrix_world@v.co for v in me.vertices]);written=0
for tri in me.loop_triangles:
 U=np.array([uv.data[li].uv[:] for li in tri.loops]);Q=positions[list(tri.vertices)];v0=U[1]-U[0];v1=U[2]-U[0];det=v0[0]*v1[1]-v1[0]*v0[1]
 if abs(det)<1e-12:continue
 lo=np.maximum(np.floor(U.min(0)*W-.5).astype(int),0);hi=np.minimum(np.ceil(U.max(0)*W-.5).astype(int),W-1)
 if np.any(hi<lo):continue
 yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];delta=np.stack([(xx+.5)/W-U[0,0],(yy+.5)/W-U[0,1]],axis=-1);b=(delta[:,:,0]*v1[1]-v1[0]*delta[:,:,1])/det;c=(v0[0]*delta[:,:,1]-delta[:,:,0]*v0[1])/det;inside=(b>=-1e-6)&(c>=-1e-6)&(b+c<=1+1e-6)
 if not inside.any():continue
 bb=b[inside];cc=c[inside];q=Q[0]+bb[:,None]*(Q[1]-Q[0])+cc[:,None]*(Q[2]-Q[0]);rgb,fat,fold=pigment(q);ys=yy[inside];xs=xx[inside];pixels[ys,xs,:3]=rgb;mask[ys,xs]=fat;crease_mask[ys,xs]=fold;written+=len(xs)
ev.to_mesh_clear();image=bpy.data.images.new('MIA_V27_ActualUV_Pigment_R3_2048',width=W,height=W,alpha=True,float_buffer=True);image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(OUT/'MIA_V27_ActualUV_Pigment_R3_2048.exr');image.file_format='OPEN_EXR';image.save();image.pack()
mat=skin.material_slots[0].material.copy();mat.name='MIA_V27_NewSurface_ActualUVIdentity';skin.material_slots[0].material=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;oldtex=n.get('V27_ACTUAL_UV_PIGMENT');n.remove(oldtex) if oldtex else None;tex=n.new('ShaderNodeTexImage');tex.name='V27_ACTUAL_UV_PIGMENT';tex.image=image;uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='UVMap';l.new(uvnode.outputs['UV'],tex.inputs['Vector']);l.new(tex.outputs['Color'],n['PigmentTimesControlledLight'].inputs[1]);out=next(x for x in n if x.type=='OUTPUT_MATERIAL' and x.is_active_output);keep=set()
def visit(x):
 if x in keep:return
 keep.add(x)
 for socket in x.inputs:
  for link in socket.links:visit(link.from_node)
visit(out)
for x in list(n):
 if x not in keep:n.remove(x)
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Mia_Foundation_v27.blend'))
np.savez_compressed(OUT/'actual-uv-paint-masks.npz',fatigue=mask,upper_fold=crease_mask)
(OUT/'actual-uv-pigment-audit.json').write_text(json.dumps({'image':image.name,'path':image.filepath_raw,'sha256':hashlib.sha256(Path(image.filepath_raw).read_bytes()).hexdigest(),'size':[W,W],'color_space':'Non-Color, scene-linear RGB','rasterized_samples':written,'uv_layer':'UVMap','method':'Rasterize actual evaluated new skin triangles to original preserved UV; under-eye warm fatigue and thin upper-fold follow new actual upper/lower lid curves in world space. Not old M5 coordinates/maps.','connected_route':'UVMap -> V27_ACTUAL_UV_PIGMENT -> PigmentTimesControlledLight -> existing controlled-light Emission output','base_linear':base.tolist(),'limits':'First painted draft, no art acceptance. Body and hair materials unchanged. Parametric bridge UV at0 samples unpainted base.'},indent=2));(OUT/'fine-feature-paint-audit.json').write_text(json.dumps({'mouth_curve_coefficients':mouthcoef.tolist(),'mouth_center_x':mouthcx,'mouth_half_width':mouthrad,'lip_sigma_mm':.30,'nostril_z':nostril_z,'nostril_x':[-.0022,.0022],'nostril_sigma_mm':[.48,.28],'method':'Actual current mouth boundary and nasal tip; two tiny nostril marks and thin lip seam only. No large shadow bake.'},indent=2));print('ACTUAL_UV_PAINT_SAVED')


