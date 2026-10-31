import bpy,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;F=H/'finish-4';p=F/'Mia_FaceFinish_v22.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(p)
bpy.ops.wm.open_mainfile(filepath=str(p));d={}
for name,slot in [('MIA_V14_SculptedSkin',7),('MIA_V06_BODY_SKIN',0),('MIA_V14_EyeSurface',5)]:
 o=bpy.data.objects[name];m=o.material_slots[slot].material;d[name]={'slot':slot,'material':m.name,'images':[{'node':n.name,'image':n.image.name,'colorspace':n.image.colorspace_settings.name,'packed':bool(n.image.packed_file),'fake_user':n.image.use_fake_user} for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image],'uv_nodes':{n.name:n.uv_map for n in m.node_tree.nodes if n.type=='UVMAP'},'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links]}
d['sclera_backface_culling']=bpy.data.objects['MIA_V14_EyeSurface'].material_slots[1].material.use_backface_culling
d['native_unchanged']=before==sha(p);(F/'actual-material-route.json').write_text(json.dumps(d,indent=2));print({n:v['material'] for n,v in d.items() if isinstance(v,dict)})
