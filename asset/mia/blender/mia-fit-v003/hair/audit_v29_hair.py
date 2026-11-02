"""Read retained v29 hair ancestry and actual recorded camera/light comparability."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
P=Path(__file__).resolve().parent;W=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay');V=W/'asset/mia/blender/mia-face-finish-v29';N=V/'surface-C/native/Mia_FaceFinish_v29_C.blend';sha=hashlib.sha256(N.read_bytes()).hexdigest();assert sha=='d7e2f7d7027e7ce65746e18af25562ec25a19c61bca847d5363080259b27d3be'
bpy.ops.wm.open_mainfile(filepath=str(N),use_scripts=False);main=bpy.data.objects['MIA_V17_PIXAL_DetailedHair'];m=main.data;coords=np.array([v.co[:] for v in m.vertices],np.float32);materials=[]
for ma in m.materials:
 if ma is None:continue
 materials.append(dict(name=ma.name,nodes=[dict(name=n.name,type=n.type,image=n.image.name if n.type=='TEX_IMAGE' and n.image else None,attribute=getattr(n,'attribute_name',None)) for n in ma.node_tree.nodes],links=[dict(source=l.from_node.name,output=l.from_socket.name,target=l.to_node.name,input=l.to_socket.name) for l in ma.node_tree.links]))
old=json.loads((V/'final-review/orbit/render-records.json').read_text());current=json.loads((W/'asset/mia/blender/mia-refinement-v002/review/integrated-R3b/orbit/render-records.json').read_text());comparisons=[]
for view in ['000','009','012','015','018']:
 a=next(x for x in old if x['id']==view);b=next(x for x in current if x['id']==view+'-production');ka=a['camera'];kb=b['camera'];comparisons.append(dict(view=view,old_path=a['path'],current_path=b['path'],camera_matrix_exact=ka['matrix']==kb['matrix'],ortho_scale_exact=ka['ortho_scale']==kb['ortho_scale'],lighting_record_exact=ka.get('lighting')==kb.get('lighting'),color_management_exact=ka.get('color_management')==kb.get('color_management'),old_material_mode=a['material_mode'],current_material_mode=b['material_mode']))
report=dict(v29_native=str(N),sha256=sha,vertices=len(m.vertices),polygons=len(m.polygons),coordinates_sha256=hashlib.sha256(coords.tobytes()).hexdigest(),uv_layers=[u.name for u in m.uv_layers],materials=materials,recorded_comparisons=comparisons,native_saved=False,limits='Read-only retained native/actual records. Matching camera/light metadata enables a stronger historical comparison but does not isolate every material/geometry change. Current pigment-only/gray diagnostic is the causal texture-vs-light ablation; no v29 pigment ablation rendered.')
(P/'v29-hair-ancestry.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('V29_HAIR_AUDIT_OK',len(m.vertices),len(m.polygons),flush=True)
