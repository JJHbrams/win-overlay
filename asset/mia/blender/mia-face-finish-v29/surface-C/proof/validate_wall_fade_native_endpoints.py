"""CPU-native numeric endpoint bakes of the actual staged node graphs.

Each probe quad samples one actual wall-root UV; the separate active bake UV
places those samples into a tiny atlas. No native save, GPU or model assignment.
"""
import bpy,numpy as np,json,hashlib,ast,math
from pathlib import Path
P=Path(__file__).parent.resolve();S=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-orbit-thorax-review-v28/integrated-G2L/Mia_Foundation_v28_G2L.blend');EXPECTED='f0dead17dba4f492c47652dab62c48a93bcd0100bc2586ca3ac315d41a977ee2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(S)==EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(S),use_scripts=False);owner=bpy.data.objects['MIA_V27_SharedHeadBody'];images={}
for key,path,cs in [('art',P/'art-pigment-B/Mia_UVPigment_Art_B.png','sRGB'),('features',P/'native-control-maps-final/V29_FeatureControls_RGB.exr','Non-Color'),('response',P/'native-control-maps-final/V29_LightReflectControls_RGB.exr','Non-Color')]:
 im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name=cs;images[key]=im
builder=P/'apply_surface_after_eye_gate.py';tree=ast.parse(builder.read_text());wanted={'scalar','graph','digest','material'};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted],type_ignores=[]),'actual_surface_builder','exec'));newmaterials=[]
face=material(owner.material_slots[0].material,'V29_UNASSIGNED_FaceEndpoints');wall=material(bpy.data.objects['V28G_InnerLid_-1'].material_slots[0].material,'V29_UNASSIGNED_WallEndpoints',wall=True)
samples=[]
for sign in [-1,1]:
 o=bpy.data.objects['V28G_InnerLid_'+str(sign)];uv=o.data.uv_layers['UVMap'];values={i:[] for i in range(96)}
 for loop in o.data.loops:
  if loop.vertex_index<96:values[loop.vertex_index].append(np.array(uv.data[loop.index].uv,dtype=float))
 for station,pts in values.items():
  assert pts and max(float(np.max(abs(q-pts[0]))) for q in pts)<1e-6
  samples.append({'owner':o.name,'row':0,'station':station,'uv':pts[0].tolist()})
for uv in [[.345,.365],[.655,.365],[.345,.505],[.655,.505],[.255,.326],[.745,.326],[.5,.241],[.5,.85]]:samples.append({'owner':'additional diagnostic','uv':uv})
width=16;height=math.ceil(len(samples)/width);verts=[];faces=[]
for i in range(width*height):
 x=i%width;y=i//width;k=len(verts);verts.extend([(x,y,0),(x+1,y,0),(x+1,y+1,0),(x,y+1,0)]);faces.append([k,k+1,k+2,k+3])
mesh=bpy.data.meshes.new('V29_TemporaryNumericProbeGrid');mesh.from_pydata(verts,[],faces);mesh.update();source_uv=mesh.uv_layers.new(name='UVMap');bake_uv=mesh.uv_layers.new(name='ProbeBakeUV');mesh.uv_layers.active_index=1;source_uv.active_render=False;bake_uv.active_render=True
for i,poly in enumerate(mesh.polygons):
 source=samples[i]['uv'] if i<len(samples) else [.5,.85];x=i%width;y=i//width
 target=[(x/width,y/height),((x+1)/width,y/height),((x+1)/width,(y+1)/height),(x/width,(y+1)/height)]
 for li,t in zip(poly.loop_indices,target):source_uv.data[li].uv=source;bake_uv.data[li].uv=t
attribute=mesh.attributes.new('V29_CosmeticRootFade','FLOAT','POINT');scene=bpy.data.scenes.new('V29_EndpointValidation_CPU');bpy.context.window.scene=scene;obj=bpy.data.objects.new('V29_EndpointValidation_Only',mesh);scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True);mesh.materials.append(face);scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=1;scene.render.bake.margin=0;scene.render.bake.use_clear=True
def control_output(mat):
 n=mat.node_tree.nodes;l=mat.node_tree.links;combine=n.new('ShaderNodeCombineColor');combine.mode='RGB';l.new(n['V29_ActiveDiffuseShadowControl'].inputs[0].links[0].from_socket,combine.inputs['Red']);l.new(n['V29_WeightedActualSpecular'].inputs[2].links[0].from_socket,combine.inputs['Green'])
 if mat==face:l.new(n['V29_FaceRootFade'].outputs[0],combine.inputs['Blue'])
 else:l.new(next(q for q in n if q.type=='ATTRIBUTE' and q.attribute_name=='V29_CosmeticRootFade').outputs['Fac'],combine.inputs['Blue'])
 return combine.outputs['Color']
controls={m.name:control_output(m) for m in [face,wall]};baked={}
def bake(label,mat,socket,fade):
 for item in attribute.data:item.value=fade
 mesh.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;l.new(socket,n['방출'].inputs['Color']);target=n.get('V29_NumericBakeTarget') or n.new('ShaderNodeTexImage');target.name='V29_NumericBakeTarget';im=bpy.data.images.new(label,width=width,height=height,alpha=True,float_buffer=True);im.colorspace_settings.name='Non-Color';target.image=im;n.active=target;target.select=True;bpy.context.view_layer.update();bpy.ops.object.bake(type='EMIT',margin=0,use_clear=True);a=np.empty(len(im.pixels),dtype=np.float32);im.pixels.foreach_get(a);a=a.reshape(-1,4)[:len(samples),:3];baked[label]=a;return a
original=bake('original',wall,wall.node_tree.nodes['V27_ACTUAL_UV_PIGMENT'].outputs['Color'],0.)
wall0=bake('wall_fade0',wall,wall.node_tree.nodes['V29_OriginalVsSurfaceBypass'].outputs[0],0.)
wall1=bake('wall_fade1',wall,wall.node_tree.nodes['V29_OriginalVsSurfaceBypass'].outputs[0],1.)
wallhalf=bake('wall_fade_half',wall,wall.node_tree.nodes['V29_OriginalVsSurfaceBypass'].outputs[0],.5)
face1=bake('face_fade1',face,face.node_tree.nodes['V29_OriginalVsSurfaceBypass'].outputs[0],1.)
c0=bake('wall_controls0',wall,controls[wall.name],0.);c1=bake('wall_controls1',wall,controls[wall.name],1.);cf=bake('face_controls1',face,controls[face.name],1.)
errors={'deep_color_vs_original':float(abs(wall0-original).max()),'root_color_vs_face':float(abs(wall1-face1).max()),'half_color_vs_linear_complete_fade':float(abs(wallhalf-(original+face1)*.5).max()),'deep_diffuse_shadow_factor_vs1':float(abs(c0[:,0]-1).max()),'deep_specular_scale_vs0':float(abs(c0[:,1]).max()),'root_diffuse_spec_controls_vs_face':float(abs(c1-cf).max())}
assert max(errors.values())<2e-6,errors
assert float(abs(face1-original).max())>.001,'Probe must exercise nonzero cosmetics, not only a neutral region'
report={'method':'Actual Blender Cycles CPU EMIT bakes through newly built native material graph, sampling192 actual wall-root UV stations plus8 feature/outside controls. Explicit sourceUVMap and separate bakeUV; no manual shader evaluator or bitmap edit.','source_native_sha256':EXPECTED,'source_native_sha256_after':sha(S),'builder_sha256':sha(builder),'original_face_graph_sha256':digest(graph(owner.material_slots[0].material.node_tree)),'original_wall_graph_sha256':digest(graph(bpy.data.objects['V28G_InnerLid_-1'].material_slots[0].material.node_tree)),'sample_count':len(samples),'samples':samples,'errors_m_or_linear_RGB':errors,'nonzero_cosmetic_difference_max_linear_RGB':float(abs(face1-original).max()),'no_gpu':True,'native_saved':False,'model_owners_unassigned':True,'status':'Native graph endpoint numeric checks PASS. Actual final material/eye/lash/source/render acceptance remains unverified.'}
assert report['source_native_sha256_after']==EXPECTED;(P/'wall-fade-native-endpoint-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print('WALL_NATIVE_ENDPOINTS_PASS',json.dumps(errors),flush=True)
