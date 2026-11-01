import bpy,json
from pathlib import Path
P=Path(__file__).parent
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
rows=[]
for name in ['MIA_V20_AuthoredFold_AshStrata_V22_LightToon','MIA_V17_ReferenceAshGray_PaintUV.001_V22_LightToon_GeneratedInk']:
 m=bpy.data.materials[name]
 rows.append({'name':name,'nodes':[{'name':n.name,'type':n.type,'uv_map':getattr(n,'uv_map',None),'image':n.image.name if n.type=='TEX_IMAGE' and n.image else None,'inputs':{s.name:str(s.default_value) for s in n.inputs if hasattr(s,'default_value') and not s.is_linked}} for n in m.node_tree.nodes],'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in m.node_tree.links]})
(P/'material-audit.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
