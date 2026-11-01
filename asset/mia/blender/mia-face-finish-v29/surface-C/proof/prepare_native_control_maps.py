"""Stage deterministic UV control maps with Blender's CPU EMIT bake.

No AI numeric maps, image-pixel painting or saved model edits. These provisional
selectors are aligned to the audited UV chart, not a new anatomical source.
Their actual footprint must be reviewed on the accepted eye/lash native.
"""
import bpy,json,hashlib,numpy as np
from pathlib import Path
P=Path(__file__).parent;O=P/'native-control-maps-v02';O.mkdir(exist_ok=True)
S=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');SHA='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(S)==SHA
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);source=bpy.data.objects['MIA_V27_SharedHeadBody'];sm=source.data;polys=[p for p in sm.polygons if p.material_index==0];ids=sorted({v for p in polys for v in p.vertices});remap={v:i for i,v in enumerate(ids)}
mesh=bpy.data.meshes.new('V29_TemporaryFaceUVBake');mesh.from_pydata([list(sm.shape_keys.key_blocks[0].data[v].co) for v in ids],[],[[remap[v] for v in p.vertices] for p in polys]);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
for before,after in zip(polys,mesh.polygons):
 assert [ids[v] for v in after.vertices]==list(before.vertices)
 for a,b in zip(before.loop_indices,after.loop_indices):uv.data[b].uv=sm.uv_layers['UVMap'].data[a].uv
scene=bpy.data.scenes.new('V29_NativeControlBake_CPU');bpy.context.window.scene=scene;obj=bpy.data.objects.new('V29_TemporaryFaceUVBake',mesh);scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.margin=16;scene.render.bake.margin_type='EXTEND';scene.render.bake.use_clear=False;scene.render.bake.use_selected_to_active=False
mat=bpy.data.materials.new('V29_ControlMasks_NativeBakeOnly');mat.use_nodes=True;mesh.materials.append(mat);nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
def math(op,a,b=None):
 n=nodes.new('ShaderNodeMath');n.operation=op
 for i,x in enumerate([a,b] if b is not None else [a]):
  if hasattr(x,'node'):links.new(x,n.inputs[i])
  else:n.inputs[i].default_value=x
 return n.outputs[0]
def mr(value,lo,hi,outlo,outhi):
 n=nodes.new('ShaderNodeMapRange');n.clamp=True;n.interpolation_type='SMOOTHERSTEP';links.new(value,n.inputs['Value']);n.inputs['From Min'].default_value=lo;n.inputs['From Max'].default_value=hi;n.inputs['To Min'].default_value=outlo;n.inputs['To Max'].default_value=outhi;return n.outputs['Result']
t=nodes.new('ShaderNodeUVMap');t.uv_map='UVMap';sep=nodes.new('ShaderNodeSeparateXYZ');links.new(t.outputs['UV'],sep.inputs[0]);u,v=sep.outputs['X'],sep.outputs['Y']
def ellipse(cx,cy,rx,ry):
 x=math('DIVIDE',math('SUBTRACT',u,cx),rx);y=math('DIVIDE',math('SUBTRACT',v,cy),ry);r=math('ADD',math('MULTIPLY',x,x),math('MULTIPLY',y,y));return mr(r,.55,1.,1.,0.)
def union(*sockets):
 out=sockets[0]
 for s in sockets[1:]:out=math('MAXIMUM',out,s)
 return out
fatigue=union(*[ellipse(cx,.365,.094,.064) for cx in [.345,.655]])
folds=[]
for cx in [.345,.655]:
 q=math('DIVIDE',math('SUBTRACT',u,cx),.078);curve=math('SUBTRACT',.506,math('MULTIPLY',math('MULTIPLY',q,q),.029));distance=math('ABSOLUTE',math('SUBTRACT',v,curve));band=mr(distance,.008,.021,1.,0.);edge=mr(math('ABSOLUTE',q),.85,1.18,1.,0.);folds.append(math('MULTIPLY',band,edge))
fold=union(*folds)
makeup=union(*[ellipse(cx,.490,.105,.052) for cx in [.345,.655]],*[ellipse(cx,.326,.091,.052) for cx in [.255,.745]],ellipse(.5,.241,.061,.026))
# Disjoint ownership: makeup cannot redraw the fold/fatigue when its own gain is enabled.
makeup=math('MULTIPLY',makeup,math('SUBTRACT',1.,union(fatigue,fold)))
central=ellipse(.5,.46,.39,.40);nose=ellipse(.5,.392,.040,.095);lip=ellipse(.5,.242,.062,.023)
shadow=math('SUBTRACT',1.,math('MULTIPLY',central,.12));spec=math('ADD',math('MULTIPLY',central,.02),math('ADD',math('MULTIPLY',nose,.10),math('MULTIPLY',lip,.045)));roughness=math('SUBTRACT',.74,math('ADD',math('MULTIPLY',nose,.15),math('MULTIPLY',lip,.11)))
emit=nodes.new('ShaderNodeEmission');out=nodes.new('ShaderNodeOutputMaterial');out.is_active_output=True;links.new(emit.outputs[0],out.inputs['Surface']);target=nodes.new('ShaderNodeTexImage');nodes.active=target;target.select=True
reports=[]
for name,channels,bg,meaning in [('V29_FeatureControls_RGB',[fatigue,fold,makeup],(0,0,0,1),{'R':'new fatigue cosmetic selection/gain','G':'new upper-fold cosmetic selection/gain','B':'new makeup/cheek/lip selection/gain'}),('V29_LightReflectControls_RGB',[shadow,spec,roughness],(1,0,.74,1),{'R':'actual diffuse-ramp shadow influence,1=baseline','G':'active specular weight selection','B':'active specular closure roughness'})]:
 combine=nodes.new('ShaderNodeCombineColor');combine.mode='RGB'
 for c,s in zip(['Red','Green','Blue'],channels):links.new(s,combine.inputs[c])
 links.new(combine.outputs['Color'],emit.inputs['Color']);image=bpy.data.images.new(name,width=2048,height=2048,alpha=True,float_buffer=True);image.generated_color=bg;image.colorspace_settings.name='Non-Color';target.image=image;nodes.active=target
 bpy.ops.object.bake(type='EMIT',use_clear=False,margin=16,margin_type='EXTEND');path=O/(name+'.exr');image.filepath_raw=str(path);image.file_format='OPEN_EXR';image.save();pixels=np.empty(len(image.pixels),dtype=np.float32);image.pixels.foreach_get(pixels);pixels=pixels.reshape(2048,2048,4)
 reports.append({'name':name,'path':str(path.resolve()),'sha256':sha(path),'size':[2048,2048],'float_buffer':True,'colorspace':image.colorspace_settings.name,'channels':meaning,'alpha':'coverage, not an authored control','per_channel_min':pixels.min((0,1)).tolist(),'per_channel_max':pixels.max((0,1)).tolist(),'pixel_hash':hashlib.sha256(pixels.tobytes()).hexdigest(),'method':'Blender Cycles CPU one-sample EMIT bake of native UV shader math; island-aware16px EXTEND margin; no bitmap editing or AI numeric data.'})
 assert nodes.active==target and out.is_active_output
report={'source_native':str(S),'source_sha256':SHA,'source_sha256_after':sha(S),'art_source':'B generated art remains separate sRGB1254-square, not used to paint these numeric controls.','native_saved':False,'gpu_used':False,'bake_engine':'CYCLES_CPU','temporary_mesh':'Only slot0 FaceUV polygons copied for native bake, no original mesh edits or topology transfer.','uv_layout_sha256':hashlib.sha256(np.array([list(x.uv) for x in sm.uv_layers['UVMap'].data],dtype='<f8').tobytes()).hexdigest(),'status':'PROVISIONAL CONTROLS ONLY. Not a current active native delivery. Bind/review only after accepted-eye/lash gate; clear all layer claims until actual socket/probe evidence.','maps':reports}
assert report['source_sha256_after']==SHA;(O/'native-control-bake-manifest.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('NATIVE_CPU_CONTROLS_STAGED',len(reports),flush=True)
