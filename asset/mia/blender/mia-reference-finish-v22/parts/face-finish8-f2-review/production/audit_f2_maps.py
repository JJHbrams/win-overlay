"""Read-only D/F2 actual consumed material and packed map equality."""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(data):return hashlib.sha256(data).hexdigest()
def simple(value):
 if isinstance(value,(bool,int,float,str)):return value
 try:return list(value)
 except:return str(value)
def material_state():
 skin=bpy.data.objects['MIA_V14_SculptedSkin'];mat=skin.data.materials[7];nodes=[];images={}
 for node in mat.node_tree.nodes:
  item={'name':node.name,'type':node.bl_idname,'inputs':{s.identifier:simple(s.default_value) for s in node.inputs if hasattr(s,'default_value')}}
  for prop in ['operation','blend_type','interpolation','extension','uv_map','attribute_name','clamp_factor','clamp_result']:
   if hasattr(node,prop):item[prop]=simple(getattr(node,prop))
  if hasattr(node,'color_ramp'):item['ramp']={'interpolation':node.color_ramp.interpolation,'elements':[(e.position,list(e.color)) for e in node.color_ramp.elements]}
  if node.type=='TEX_IMAGE' and node.image:
   im=node.image;item['image']=im.name
   images[node.name]={'name':im.name,'filepath':im.filepath,'size':list(im.size),'colorspace':im.colorspace_settings.name,'packed':bool(im.packed_file),'packed_sha256':digest(im.packed_file.data) if im.packed_file else None}
  nodes.append(item)
 return {'material':mat.name,'skin_slot':7,'uv_layer':skin.data.uv_layers.active.name,'nodes':sorted(nodes,key=lambda n:n['name']),'links':sorted((l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in mat.node_tree.links),'images':images}
states={}
for label,path in [('D',ROOT/'look-d/Mia_FaceFinish8_AuthoredLookD.blend'),('F2',ROOT/'shape-f2/Mia_FaceFinish8_ConnectedBuccalF2.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));states[label]=material_state()
assert states['D']==states['F2']
(ROOT/'shape-f2/handoff/material-map-audit.json').write_text(json.dumps({'actual_material_graph_and_packed_maps_equal_D':True,'state':states['F2'],'limits':'UV exactness separately verified in replay. No new paint or map detail authored for F2.'},indent=2));print('F2_MAPS_EXACT_D')
