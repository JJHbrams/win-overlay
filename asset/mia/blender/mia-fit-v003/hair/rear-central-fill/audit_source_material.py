from pathlib import Path
import bpy,json,sys
P=Path(__file__).resolve().parent;W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');N=W/'asset/mia/blender/mia-refinement-v002/integrated/Mia_v0.0.2_Review_R3b.blend';bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);m=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'].data;ma=m.materials[0];tree=ma.node_tree;out=tree.get_output_node('EEVEE');stack=[out];seen=set()
while stack:
 n=stack.pop()
 if n in seen:continue
 seen.add(n)
 for p in n.inputs:
  for l in p.links:stack.append(l.from_node)
report=dict(material=ma.name,actual_eevee_output=out.name,active_nodes=[dict(name=n.name,type=n.type,attribute=getattr(n,'attribute_name',None),uv=getattr(n,'uv_map',None),image=n.image.name if n.type=='TEX_IMAGE' and n.image else None) for n in seen],all_POINT_attributes=[dict(name=a.name,type=a.data_type) for a in m.attributes if a.domain=='POINT'],all_UVs=[u.name for u in m.uv_layers],geometry_normal_links=[dict(from_node=l.from_node.name,from_socket=l.from_socket.name,to_node=l.to_node.name,to_socket=l.to_socket.name) for l in tree.links if l.from_node in seen and (l.from_node.type in ['NEW_GEOMETRY','NORMAL_MAP','ATTRIBUTE'] or l.to_node.type in ['NORMAL_MAP'])]);(P/'source-material-active-route.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('SOURCE_ROUTE',[(n.name,n.type,getattr(n,'attribute_name',None),getattr(n,'uv_map',None)) for n in seen if n.type in ['ATTRIBUTE','NORMAL_MAP','UVMAP','NEW_GEOMETRY']],flush=True)
