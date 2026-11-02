"""Add bounded v003 eye and stylized dental-display controls to CURRENT scene.

No native open, save, render, raster creation or preset JSON mutation.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent
S='Face.M_F00_000_00_Fcl_EYE_Surprised';G='Face.M_F00_000_00_Fcl_MIA_ToothyGrin'
def sha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def arr(c,field='co',width=3):
 a=np.empty(len(c)*width,np.float32);c.foreach_get(field,a);return a.reshape(-1,width)
def bind(d,name,owner,path,id_type=None):
 v=d.variables.new();v.name=name;v.type='SINGLE_PROP'
 if id_type:v.targets[0].id_type=id_type
 v.targets[0].id=owner;v.targets[0].data_path=path
def apply_eyes_to_current_scene():
 meta=json.loads((P/'payload/surprise-A.json').read_text());file=P/'payload'/meta['payload'];assert hashlib.sha256(file.read_bytes()).hexdigest()==meta['payload_sha256'];data=np.load(file)
 master=bpy.data.objects['MIA_V27_Foundation_Face'];ctrl=bpy.data.objects['Mia_FacialControls_v002'];masterkeys=master.data.shape_keys
 if ctrl.get('V003_eye_payload'):
  assert ctrl['V003_eye_payload']==meta['payload_sha256'];return dict(already_applied=True,payload_sha256=meta['payload_sha256'])
 for name,guard in meta['owners'].items():
  ob=bpy.data.objects[name];assert len(ob.data.vertices)==len(ob.data.shape_keys.key_blocks[0].data);keys=ob.data.shape_keys.key_blocks
  assert all(n in keys for n in guard['key_names']),('Required original eye key missing',name)
  assert sha(arr(ob.data.vertices))==guard['raw_sha256'],('Eye raw array changed',name)
  for kn,digest in guard['original_key_sha256'].items():assert sha(arr(keys[kn].data))==digest,('Eye key precondition changed',name,kn)
  assert {u.name:sha(arr(u.data,'uv',2)) for u in ob.data.uv_layers}==guard['UV'],('Eye UV changed',name)
 created=[]
 for row in meta['entries']:
  ob=bpy.data.objects[row['owner']];basis=arr(ob.data.shape_keys.key_blocks[0].data);ids=data[row['prefix']+'_ids'];delta=data[row['prefix']+'_delta'];key=ob.shape_key_add(name=row['name'],from_mix=False);basis[ids]+=delta;key.data.foreach_set('co',basis.ravel());key.value=0.;key.slider_min=0.;key.slider_max=1.
  d=key.driver_add('value').driver;d.type='SCRIPTED';bind(d,'s',masterkeys,'key_blocks["'+S+'"].value','KEY')
  side='R' if row['side']==-1 else 'L'
  for var,suffix in [('c','EYE_Close'),('j','EYE_Joy'),('r','EYE_Close_'+side),('q','EYE_Joy_'+side)]:bind(d,var,masterkeys,'key_blocks["Face.M_F00_000_00_Fcl_'+suffix+'"].value','KEY')
  close='min(1,max(0,c,j,r,q))'
  d.expression=('max(0,min(1,(s-0.15)/0.65))*(1-'+close+')') if row['role']=='aperture' else 'max(0,min(1,s))*'+close
  created.append(dict(owner=ob.name,key=key.name,role=row['role'],side=row['side'],driver=d.expression,changed_vertices=len(ids)))
 ctrl['V003_eye_payload']=meta['payload_sha256'];bpy.context.view_layer.update()
 return dict(payload_sha256=meta['payload_sha256'],created=created,scope='Additive local skin/wall/lash opening; side-aware inherited Surprise cancellation under Close/Joy. Original arrays, iris radius, UV, weights, materials and all poses untouched.')
def _copy_clean_ancestry(old):
 assert old.use_nodes;nt=old.node_tree;out=nt.get_output_node('EEVEE');assert out and out.inputs['Surface'].is_linked
 ancestry=set()
 def visit(n):
  if n in ancestry:return
  assert n.type!='GROUP','Dental enamel must have a clean stock-node route'
  ancestry.add(n)
  for inp in n.inputs:
   for link in inp.links:visit(link.from_node)
 visit(out)
 mat=bpy.data.materials.new('MIA_v003_Enamel_DentalDisplay');mat.use_nodes=True;mat.node_tree.nodes.clear();nodes={}
 for n in ancestry:
  new=mat.node_tree.nodes.new(n.bl_idname);new.name=n.name;new.label=n.label;nodes[n]=new
  for attr in ['operation','blend_type','clamp','use_clamp','interpolation_type','data_type','uv_map','extension','projection','interpolation']:
   if hasattr(n,attr) and hasattr(new,attr):
    try:setattr(new,attr,getattr(n,attr))
    except (TypeError,ValueError,AttributeError):pass
  if n.type=='TEX_IMAGE':new.image=n.image
  for a,b in zip(n.inputs,new.inputs):
   if hasattr(a,'default_value') and hasattr(b,'default_value'):
    try:b.default_value=a.default_value
    except (TypeError,ValueError):pass
  if n.type=='VALTORGB':
   new.color_ramp.interpolation=n.color_ramp.interpolation
   while len(new.color_ramp.elements)>2:new.color_ramp.elements.remove(new.color_ramp.elements[-1])
   for i,e in enumerate(n.color_ramp.elements):
    ne=new.color_ramp.elements[i] if i<2 else new.color_ramp.elements.new(e.position);ne.position=e.position;ne.color=e.color
 for link in nt.links:
  if link.from_node in ancestry and link.to_node in ancestry:
   ni=list(link.from_node.outputs).index(link.from_socket);nj=list(link.to_node.inputs).index(link.to_socket);mat.node_tree.links.new(nodes[link.from_node].outputs[ni],nodes[link.to_node].inputs[nj])
 target=nodes[out];target.target='ALL';target.is_active_output=True;mat.diffuse_color=old.diffuse_color;mat.use_backface_culling=old.use_backface_culling
 if hasattr(mat,'surface_render_method'):mat.surface_render_method='DITHERED'
 if hasattr(mat,'use_transparent_shadow'):mat.use_transparent_shadow=True
 if hasattr(mat,'use_transparency_overlap'):mat.use_transparency_overlap=False
 mat['V003_scope']='Explicit stylized dental visibility only. Transparent endpoint exposes existing cavity. Original enamel graph archived; crown anatomy/UV and clean oral-depth palette stay intact.'
 return mat,target
def apply_small_mouth_display_to_current_scene():
 ctrl=bpy.data.objects['Mia_FacialControls_v002'];master=bpy.data.objects['MIA_V27_Foundation_Face'];rows=[bpy.data.objects['MIA_v002_'+side+'DentalCrowns'] for side in ['Upper','Lower']]
 if ctrl.get('V003_dental_display'):
  assert all(o.material_slots[0].material.get('V003_scope') for o in rows);return dict(already_applied=True)
 assert all(o.material_slots[0].material==rows[0].material_slots[0].material for o in rows);old=rows[0].material_slots[0].material;assert old.name=='MIA_v002_Enamel_ActualToon'
 ctrl['ManualSmallMouthDentalHide']=0.;ctrl.id_properties_ui('ManualSmallMouthDentalHide').update(min=0.,max=1.,description='Stylized dental display:0 keeps enamel,1 exposes existing dark cavity. Source03/06/12 contribute automatically; MIA grin overrides hide. Manual phoneme I/E stays independent.')
 ctrl['_EffectiveSmallMouthDentalHide']=0.;d=ctrl.driver_add('["_EffectiveSmallMouthDentalHide"]').driver;d.type='SCRIPTED'
 for var,path in [('m','ManualSmallMouthDentalHide'),('t','PresetTotal'),('strength','Strength'),('p3','P03_skeptical_question'),('p6','P06_upward_uncertain'),('p12','P12_surprised')]:bind(d,var,ctrl,'["'+path+'"]')
 bind(d,'grin',master.data.shape_keys,'key_blocks["'+G+'"].value','KEY');d.expression='min(1,max(0,m+strength*(p3+p6+p12)/max(1,t)))*(1-min(1,max(0,grin)))'
 mat,out=_copy_clean_ancestry(old);old.use_fake_user=True;n=mat.node_tree.nodes;l=mat.node_tree.links;signal=out.inputs['Surface'].links[0].from_socket;transparent=n.new('ShaderNodeBsdfTransparent');transparent.name='V003_ExplicitDentalHidden';transparent.inputs['Color'].default_value=(1,1,1,1);mix=n.new('ShaderNodeMixShader');mix.name='V003_DentalDisplay';l.new(signal,mix.inputs[1]);l.new(transparent.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);mix.inputs[0].default_value=0.
 d=mix.inputs[0].driver_add('default_value').driver;d.type='AVERAGE';bind(d,'hide',ctrl,'["_EffectiveSmallMouthDentalHide"]')
 for ob in rows:ob.material_slots[0].material=mat
 ctrl['V003_dental_display']=mat.name;bpy.context.view_layer.update()
 settings={name:getattr(mat,name) for name in ['surface_render_method','use_transparent_shadow','use_transparency_overlap','use_backface_culling','use_backface_culling_shadow'] if hasattr(mat,name)}
 return dict(material=mat.name,archived=old.name,settings=settings,automatic_source_panels=[3,6,12],manual_default=ctrl['ManualSmallMouthDentalHide'],geometry_changed=False,scope='Stylized visibility, not anatomical tooth retraction. Actual EEVEE endpoints/shadow fringe require matched rendering.')
def apply_to_current_scene():
 return dict(eyes=apply_eyes_to_current_scene(),dental_display=apply_small_mouth_display_to_current_scene(),native_opened=False,native_saved=False)
