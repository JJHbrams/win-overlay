import bpy,numpy as np,json,hashlib
from pathlib import Path
P=Path(__file__).parent;paths={'baseline':P/'Mia_Q6b_BakeOnly_Control.blend','candidate':P/'Mia_ConnectedLoft_Q7_SurfaceFit.blend'};r={}
for label,path in paths.items():
 bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['MIA_V14_SculptedSkin'];me=o.data;sk=me.shape_keys
 r[label]={'keys':{k.name:np.array([v.co[:] for v in k.data]) for k in sk.key_blocks},'uv':np.array([v.uv[:] for v in me.uv_layers.active.data]),'faces':[list(p.vertices) for p in me.polygons],'other_meshes':{obj.name:hashlib.sha256(np.array([v.co[:] for v in obj.data.vertices],dtype=np.float32).tobytes()).hexdigest() for obj in bpy.data.objects if obj.type=='MESH' and obj!=o},'group_names':[g.name for g in o.vertex_groups]}
a,b=r['baseline'],r['candidate'];d=b['keys']['Basis']-a['keys']['Basis'];report={'key_names_equal':list(a['keys'])==list(b['keys']),'all_key_delta_residual_max_mm':max(float(np.max(np.abs((b['keys'][k]-a['keys'][k])-d))*1000) for k in a['keys']),'uv_max_error':float(np.max(np.abs(a['uv']-b['uv']))),'topology_equal':a['faces']==b['faces'],'other_mesh_coordinates_equal':a['other_meshes']==b['other_meshes'],'group_names_equal':a['group_names']==b['group_names'],'max_delta_mm':float(np.max(np.linalg.norm(d,axis=1))*1000),'unchanged_mesh_count':len(a['other_meshes'])}
(P/'q7-technical-audit.json').write_text(json.dumps(report,indent=2));print(report)
