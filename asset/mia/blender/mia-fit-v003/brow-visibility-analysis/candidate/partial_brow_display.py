"""One reversible evaluated 3D brow-on-fringe display candidate.

CURRENT scene only. No file open/save/render, original mesh/key/material mutation,
bitmap authoring, callback handlers or camera-specific projected PNG.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib
from mathutils import Matrix
P=Path(__file__).resolve().parent
PREFIX='MIA_v003_BrowInk_'
COMP='MIA_BrowInk_Component';SRC='MIA_BrowInk_SourceVertex';HIT='MIA_BrowInk_Hit';NORMAL='MIA_BrowInk_Normal';VALID='MIA_BrowInk_Valid';DEPTH='MIA_BrowInk_ForegroundDepth';SOURCEPOS='MIA_BrowInk_SourcePosition'
def checksum(a):return hashlib.sha256(np.asarray(a).tobytes()).hexdigest()
def make_group(name):
 g=bpy.data.node_groups.new(name,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');return g
def apply_to_current_scene(strength=.60):
 assert 0<=strength<=1
 meta=json.loads((P/'fringe-target-A.json').read_text(encoding='utf-8'));file=P/meta['payload'];assert hashlib.sha256(file.read_bytes()).hexdigest()==meta['payload_sha256'];data=np.load(file)
 if PREFIX+'HeadFrame' in bpy.data.objects:
  frame=bpy.data.objects[PREFIX+'HeadFrame'];assert frame.get('payload_sha256')==meta['payload_sha256'];set_strength(strength);return dict(already_applied=True,payload_sha256=meta['payload_sha256'])
 main=bpy.data.objects[meta['main_owner']];co=np.empty(len(main.data.vertices)*3,np.float32);main.data.vertices.foreach_get('co',co);faces=np.array([p.vertices[:] for p in main.data.polygons],np.int32)
 assert checksum(co)==meta['main_raw_co_sha256'] and checksum(faces)==meta['main_topology_sha256'],'Main topology/geometry changed; re-evaluate Fringe ownership'
 assert len(co)//3==meta['main_vertices'] and len(faces)==meta['main_faces']
 master=bpy.data.objects['MIA_V27_Foundation_Face'];rig=next(m.object for m in master.modifiers if m.type=='ARMATURE');head=rig.pose.bones['J_Bip_C_Head'];assert np.max(np.abs(np.array(head.matrix_basis)-np.eye(4)))<1e-6,'Install in neutral head pose; no pose reset is performed'
 collection=bpy.data.collections.new(PREFIX+'CandidateA');bpy.context.scene.collection.children.link(collection)
 frame=bpy.data.objects.new(PREFIX+'HeadFrame',None);collection.objects.link(frame);frame.parent=rig;frame.parent_type='BONE';frame.parent_bone=head.name;frame.matrix_world=Matrix.Identity(4);frame.empty_display_size=.004;frame['Strength']=strength;frame.id_properties_ui('Strength').update(min=0.,max=1.,description='Partial source-supported brow display on actual foreground Fringe;0 restores original appearance.');frame['payload_sha256']=meta['payload_sha256'];frame['mia_component']='brow_display_control'
 bpy.context.view_layer.update();assert np.allclose(np.array(frame.matrix_world),np.eye(4),rtol=0,atol=1e-6)
 points=data['main_point_ids'];coords=co.reshape(-1,3)[points];world=coords@np.array(main.matrix_world.to_3x3()).T+np.array(main.matrix_world.translation)
 mesh=bpy.data.meshes.new(PREFIX+'FringeTargetData');mesh.from_pydata(world,[],data['faces']);mesh.update();at=mesh.attributes.new(SRC,'INT','POINT');at.data.foreach_set('value',points);at=mesh.attributes.new(COMP,'INT','FACE');at.data.foreach_set('value',data['component_ids'])
 target=bpy.data.objects.new(PREFIX+'FringeTarget',mesh);collection.objects.link(target);target.parent=frame;target.matrix_parent_inverse=Matrix.Identity(4);target.matrix_basis=Matrix.Identity(4);target.hide_render=True;target.hide_set(True);target['mia_component']='brow_display_target';target['scope']='Unrendered proxy of only inherited Fringe-weight1 triangles, live-sampled from original Main evaluated vertex positions. No original hair data changed.'
 g=make_group(PREFIX+'TargetCurrentEvaluatedMain');n=g.nodes;l=g.links
 inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
 source=n.new('GeometryNodeObjectInfo');source.transform_space='RELATIVE';source.inputs['Object'].default_value=main;source.inputs['As Instance'].default_value=False
 index=n.new('GeometryNodeInputNamedAttribute');index.data_type='INT';index.inputs['Name'].default_value=SRC
 position=n.new('GeometryNodeInputPosition');sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;l.new(source.outputs['Geometry'],sample.inputs['Geometry']);l.new(position.outputs[0],sample.inputs['Value']);l.new(index.outputs['Attribute'],sample.inputs['Index'])
 setpos=n.new('GeometryNodeSetPosition');l.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);l.new(sample.outputs['Value'],setpos.inputs['Position']);l.new(setpos.outputs['Geometry'],out.inputs['Geometry']);mod=target.modifiers.new(PREFIX+'FollowActualMainVertices','NODES');mod.node_group=g
 # Small new unlit material; no original material graph is copied or replaced.
 mat=bpy.data.materials.new(PREFIX+'PartialCharcoal');mat.use_nodes=True;mat.node_tree.nodes.clear();n=mat.node_tree.nodes;l=mat.node_tree.links
 def smath(op,a,b=None):
  z=n.new('ShaderNodeMath');z.operation=op
  for i,v in enumerate([a,b]):
   if v is None:continue
   if hasattr(v,'node'):l.new(v,z.inputs[i])
   else:z.inputs[i].default_value=v
  return z.outputs[0]
 def ramp(value,lo,hi):
  z=n.new('ShaderNodeMapRange');z.clamp=True;z.interpolation_type='SMOOTHSTEP';z.inputs['From Min'].default_value=lo;z.inputs['From Max'].default_value=hi;z.inputs['To Min'].default_value=0.;z.inputs['To Max'].default_value=1.;l.new(value,z.inputs['Value']);return z.outputs['Result']
 uv=n.new('ShaderNodeUVMap');uv.uv_map='BrowParamUV';sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0]);edge=smath('MINIMUM',sep.outputs['Y'],smath('SUBTRACT',1.,sep.outputs['Y']));width=ramp(edge,0.,.15)
 # Each output object has its own material parameter window, installed below.
 low=n.new('ShaderNodeValue');low.name=PREFIX+'ObservedUMin';high=n.new('ShaderNodeValue');high.name=PREFIX+'ObservedUMax';feather=.04
 loend=smath('ADD',low.outputs[0],feather);histart=smath('SUBTRACT',high.outputs[0],feather)
 rise=n.new('ShaderNodeMapRange');rise.clamp=True;rise.interpolation_type='SMOOTHSTEP';l.new(sep.outputs['X'],rise.inputs['Value']);l.new(low.outputs[0],rise.inputs['From Min']);l.new(loend,rise.inputs['From Max'])
 fall=n.new('ShaderNodeMapRange');fall.clamp=True;fall.interpolation_type='SMOOTHSTEP';l.new(sep.outputs['X'],fall.inputs['Value']);l.new(histart,fall.inputs['From Min']);l.new(high.outputs[0],fall.inputs['From Max']);uweight=smath('MULTIPLY',rise.outputs['Result'],smath('SUBTRACT',1.,fall.outputs['Result']))
 geo=n.new('ShaderNodeNewGeometry');transform=n.new('ShaderNodeVectorTransform');transform.vector_type='VECTOR';transform.convert_from='WORLD';transform.convert_to='OBJECT';l.new(geo.outputs['Incoming'],transform.inputs[0]);dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';l.new(transform.outputs[0],dot.inputs[0]);dot.inputs[1].default_value=(0,-1,0);angle=ramp(dot.outputs['Value'],.40,.85)
 gain=n.new('ShaderNodeValue');gain.name=PREFIX+'Strength';gain.outputs[0].default_value=strength;d=gain.outputs[0].driver_add('default_value').driver;d.type='AVERAGE';v=d.variables.new();v.name='display_strength';v.type='SINGLE_PROP';v.targets[0].id=frame;v.targets[0].data_path='["Strength"]'
 alpha=smath('MULTIPLY',smath('MULTIPLY',width,uweight),smath('MULTIPLY',gain.outputs[0],angle));em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.031,.027,.030,1);em.inputs['Strength'].default_value=1.;tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(alpha,mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=n.new('ShaderNodeOutputMaterial');out.target='ALL';out.is_active_output=True;l.new(mix.outputs[0],out.inputs['Surface']);mat.surface_render_method='BLENDED';mat.use_backface_culling=False
 if hasattr(mat,'use_transparent_shadow'):mat.use_transparent_shadow=True
 if hasattr(mat,'use_transparency_overlap'):mat.use_transparency_overlap=False
 mat['scope']='Only current projected brow geometry on foreground Fringe. Source-supported U windows; original UV-width fade. View-angle fade in head-local incoming direction. Not global hair transparency.'
 overlay=[];groups=[];materials=[]
 for side in [-1,1]:
  source_brow=bpy.data.objects['V31_SourceBrow_'+str(side)];assert 'BrowParamUV' in source_brow.data.uv_layers
  data_mesh=bpy.data.meshes.new(PREFIX+'EmptySource_'+str(side));ob=bpy.data.objects.new('MiaHair_BrowInkProjection_'+str(side),data_mesh);collection.objects.link(ob);ob.parent=frame;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ob['mia_component']='hair';ob['mia_role']='brow_display';ob['source_brow']=source_brow.name
  material=mat.copy();material.name=PREFIX+'PartialCharcoal_'+str(side);window=meta['source_supported_windows'][str(side)];material.node_tree.nodes[PREFIX+'ObservedUMin'].outputs[0].default_value=window['u_min'];material.node_tree.nodes[PREFIX+'ObservedUMax'].outputs[0].default_value=window['u_max'];materials.append(material.name)
  ng=make_group(PREFIX+'Project_'+str(side));n=ng.nodes;l=ng.links;out=n.new('NodeGroupOutput');groups.append(ng.name)
  def node(t):return n.new(t)
  def math(op,a,b=None):
   z=node('ShaderNodeMath');z.operation=op
   for i,vv in enumerate([a,b]):
    if vv is None:continue
    if hasattr(vv,'node'):l.new(vv,z.inputs[i])
    else:z.inputs[i].default_value=vv
   return z.outputs[0]
  def vec(op,a,b):
   z=node('ShaderNodeVectorMath');z.operation=op
   for i,vv in enumerate([a,b]):
    if hasattr(vv,'node'):l.new(vv,z.inputs[i])
    else:z.inputs[i].default_value=vv
   return z.outputs['Value'] if op in ['DISTANCE','DOT_PRODUCT'] else z.outputs['Vector']
  def boolean(op,a,b=None):
   z=node('FunctionNodeBooleanMath');z.operation=op;l.new(a,z.inputs[0])
   if b is not None:l.new(b,z.inputs[1])
   return z.outputs[0]
  def named(name,kind):
   z=node('GeometryNodeInputNamedAttribute');z.data_type=kind;z.inputs['Name'].default_value=name;return z.outputs['Attribute']
  def store(geom,name,kind,value):
   z=node('GeometryNodeStoreNamedAttribute');z.data_type=kind;z.domain='POINT';z.inputs['Name'].default_value=name;l.new(geom,z.inputs['Geometry']);l.new(value,z.inputs['Value']);return z.outputs['Geometry']
  s=node('GeometryNodeObjectInfo');s.transform_space='RELATIVE';s.inputs['Object'].default_value=source_brow;s.inputs['As Instance'].default_value=False;sub=node('GeometryNodeSubdivideMesh');sub.inputs['Level'].default_value=2;l.new(s.outputs['Geometry'],sub.inputs['Mesh']);geometry=sub.outputs['Mesh']
  t=node('GeometryNodeObjectInfo');t.transform_space='RELATIVE';t.inputs['Object'].default_value=target;t.inputs['As Instance'].default_value=False;pos=node('GeometryNodeInputPosition');ray=node('GeometryNodeRaycast');ray.data_type='INT';l.new(t.outputs['Geometry'],ray.inputs['Target Geometry']);l.new(named(COMP,'INT'),ray.inputs['Attribute']);l.new(vec('ADD',pos.outputs[0],(0,-.04,0)),ray.inputs['Source Position']);ray.inputs['Ray Direction'].default_value=(0,1,0);ray.inputs['Ray Length'].default_value=.04
  normsep=node('ShaderNodeSeparateXYZ');l.new(ray.outputs['Hit Normal'],normsep.inputs[0]);ny=normsep.outputs['Y'];frontsign=math('SUBTRACT',math('MULTIPLY',math('LESS_THAN',ny,0.),2.),1.);frontnormal=node('ShaderNodeVectorMath');frontnormal.operation='SCALE';l.new(ray.outputs['Hit Normal'],frontnormal.inputs['Vector']);l.new(frontsign,frontnormal.inputs['Scale'])
  valid=boolean('AND',ray.outputs['Is Hit'],math('LESS_THAN',ray.outputs['Hit Distance'],.0395));valid=boolean('AND',valid,math('GREATER_THAN',ray.outputs['Hit Distance'],.0001));valid=boolean('AND',valid,math('GREATER_THAN',math('ABSOLUTE',ny),.08));valid=boolean('AND',valid,math('GREATER_THAN',ray.outputs['Attribute'],.5))
  uvsep=node('ShaderNodeSeparateXYZ');l.new(named('BrowParamUV','FLOAT_VECTOR'),uvsep.inputs[0]);valid=boolean('AND',valid,math('GREATER_THAN',uvsep.outputs['X'],window['u_min']));valid=boolean('AND',valid,math('LESS_THAN',uvsep.outputs['X'],window['u_max']))
  geometry=store(geometry,COMP,'INT',ray.outputs['Attribute']);geometry=store(geometry,HIT,'FLOAT_VECTOR',ray.outputs['Hit Position']);geometry=store(geometry,NORMAL,'FLOAT_VECTOR',frontnormal.outputs['Vector']);geometry=store(geometry,DEPTH,'FLOAT',math('SUBTRACT',.04,ray.outputs['Hit Distance']));geometry=store(geometry,SOURCEPOS,'FLOAT_VECTOR',pos.outputs[0]);geometry=store(geometry,VALID,'BOOLEAN',valid)
  delete=node('GeometryNodeDeleteGeometry');delete.domain='POINT';delete.mode='ALL';l.new(geometry,delete.inputs['Geometry']);l.new(boolean('NOT',named(VALID,'BOOLEAN')),delete.inputs['Selection']);geometry=delete.outputs['Geometry']
  edges=node('GeometryNodeInputMeshEdgeVertices')
  def sample_attr(kind,name,index):
   z=node('GeometryNodeSampleIndex');z.data_type=kind;z.domain='POINT';z.clamp=False;l.new(geometry,z.inputs['Geometry']);l.new(named(name,kind),z.inputs['Value']);l.new(index,z.inputs['Index']);return z.outputs['Value']
  owner1=sample_attr('INT',COMP,edges.outputs['Vertex Index 1']);owner2=sample_attr('INT',COMP,edges.outputs['Vertex Index 2']);bad=math('GREATER_THAN',math('ABSOLUTE',math('SUBTRACT',owner1,owner2)),.5)
  hit1=sample_attr('FLOAT_VECTOR',HIT,edges.outputs['Vertex Index 1']);hit2=sample_attr('FLOAT_VECTOR',HIT,edges.outputs['Vertex Index 2']);newdist=vec('DISTANCE',hit1,hit2);olddist=vec('DISTANCE',edges.outputs['Position 1'],edges.outputs['Position 2']);bad=boolean('OR',bad,math('GREATER_THAN',newdist,math('ADD',math('MULTIPLY',olddist,2.5),.0003)))
  dsep=node('ShaderNodeSeparateXYZ');l.new(vec('SUBTRACT',hit1,hit2),dsep.inputs[0]);bad=boolean('OR',bad,math('GREATER_THAN',math('ABSOLUTE',dsep.outputs['Y']),.003));cut=node('GeometryNodeDeleteGeometry');cut.domain='EDGE';cut.mode='EDGE_FACE';l.new(geometry,cut.inputs['Geometry']);l.new(bad,cut.inputs['Selection'])
  setpos=node('GeometryNodeSetPosition');l.new(cut.outputs['Geometry'],setpos.inputs['Geometry']);l.new(named(HIT,'FLOAT_VECTOR'),setpos.inputs['Position']);offset=node('ShaderNodeVectorMath');offset.operation='SCALE';l.new(named(NORMAL,'FLOAT_VECTOR'),offset.inputs['Vector']);offset.inputs['Scale'].default_value=.00015;l.new(offset.outputs[0],setpos.inputs['Offset'])
  assign=node('GeometryNodeSetMaterial');assign.inputs['Material'].default_value=material;l.new(setpos.outputs['Geometry'],assign.inputs['Geometry']);l.new(assign.outputs['Geometry'],out.inputs['Geometry']);modifier=ob.modifiers.new(PREFIX+'ActualBrowToFringe','NODES');modifier.node_group=ng;overlay.append(ob.name)
 # Unused template is retained only as new owned data; no original graph copied.
 mat.use_fake_user=True;bpy.context.view_layer.update()
 return dict(candidate='A',frame=frame.name,target=target.name,overlay_objects=overlay,materials=materials,projection_groups=groups,payload_sha256=meta['payload_sha256'],strength=strength,original_mesh_or_material_edited=False,source_supported_windows=meta['source_supported_windows'],scope='Actual deforming brow geometry projected to foreground Fringe proxy. Semantic family is only an inherited hint; bounded first-hit/component/depth tests enforce the local projection. No rear/head projection target.')
def set_strength(value):
 assert 0<=value<=1;frame=bpy.data.objects[PREFIX+'HeadFrame'];frame['Strength']=value;frame.update_tag();bpy.context.view_layer.update()
