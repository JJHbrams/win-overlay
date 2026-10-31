"""Read-only normal-route isolation on Face6 and R8; never saves a native."""
import bpy,sys,ast,json,hashlib,math,numpy as np
from pathlib import Path
H=Path(__file__).resolve().parent;D=H.parent/'surface-diagnosis/dependencies';sys.path.insert(0,str(D));import review_setup as r
tree=ast.parse((D/'shape_evidence.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rig','constant']],type_ignores=[]),'frozen-helper-functions','exec'))
P=Path(r'C:/Users/antio/.codex/worktrees/mia-final-face-v12/win-overlay/asset/mia/blender/mia-face-finish-v22')
sources={'face6':P/'finish-6/continuous-candidate/Mia_FaceFinish6_v22.blend','r8':P/'finish-7/candidate-r8/Mia_FaceFinish7_RadialGuideR8_v22.blend'}
report={'scope':'In-memory diagnostic only; no mesh coordinates or native files saved. Recomputed route reconstructs the already evaluated skin with identical coordinates/faces, all-smooth and no custom/sharp attributes. Body route remains unchanged.','sources':{}}
def summary(values):
 a=np.asarray(values);return {k:float(v) for k,v in zip(['min','p50','p95','max'],np.percentile(a,[0,50,95,100]))} if len(a) else None
def inspect(o):
 m=o.data;mods=[]
 for x in o.modifiers:
  props={}
  for prop in x.bl_rna.properties:
   key=prop.identifier
   if any(t in key.lower() for t in ['normal','smooth','sharp','weight','level','quality']):
    try:
     v=getattr(x,key)
     if isinstance(v,(bool,int,float,str)):props[key]=v
    except Exception:pass
  mods.append({'name':x.name,'type':x.type,'show_render':x.show_render,'show_viewport':x.show_viewport,'settings':props})
 materials=[]
 for slot in o.material_slots:
  mat=slot.material
  if mat and mat.use_nodes:
   links=[{'node':n.name,'type':n.type,'input':i.name,'from':[(l.from_node.name,l.from_socket.name) for l in i.links]} for n in mat.node_tree.nodes for i in n.inputs if i.name=='Normal' and i.is_linked]
   materials.append({'name':mat.name,'linked_normal_inputs':links})
 return {'vertices':len(m.vertices),'polygons':len(m.polygons),'smooth_polygons':sum(p.use_smooth for p in m.polygons),'sharp_edges':sum(e.use_edge_sharp for e in m.edges),'has_custom_normals':m.has_custom_normals,'attributes':[{'name':a.name,'domain':a.domain,'data_type':a.data_type} for a in m.attributes],'modifiers':mods,'materials':materials}
for label,path in sources.items():
 sh=r.sha(path);bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects['MIA_V14_SculptedSkin'];body=bpy.data.objects['MIA_V06_BODY_SKIN'];rec={'source':r.artifact(path),'skin':inspect(skin),'body':inspect(body),'active_skin_keys':{k.name:k.value for k in skin.data.shape_keys.key_blocks if k.name!='Basis' and k.value},'renders':[]}
 dep=bpy.context.evaluated_depsgraph_get();ev=skin.evaluated_get(dep);me=ev.to_mesh();co=[tuple(v.co) for v in me.vertices];faces=[list(p.vertices) for p in me.polygons];old=np.array([tuple(n.vector) for n in me.corner_normals]);rec['evaluated']={'vertices':len(co),'polygons':len(faces),'has_custom_normals':me.has_custom_normals,'sharp_edges':sum(e.use_edge_sharp for e in me.edges),'smooth_polygons':sum(p.use_smooth for p in me.polygons)}
 fresh=bpy.data.meshes.new('DIAG_SameEvaluatedGeometry_RecomputedNormals');fresh.from_pydata(co,[],faces)
 for p in fresh.polygons:p.use_smooth=True
 fresh.update();new=np.array([tuple(n.vector) for n in fresh.corner_normals]);angles=np.degrees(np.arccos(np.clip(np.einsum('ij,ij->i',old,new),-1,1)));diff=np.linalg.norm(old-new,axis=1)
 rec['old_vs_recomputed_corner_normals']={'euclidean_difference':summary(diff),'angle_degrees_float_precision_limited':summary(angles),'count_difference_gt_1e-5':int(sum(diff>1e-5))}
 geom=[];vertexloops={}
 for p in me.polygons:
  for li in p.loop_indices:
   geom.append(math.degrees(math.acos(max(-1,min(1,float(np.dot(old[li],np.array(p.normal))))))))
   vertexloops.setdefault(me.loops[li].vertex_index,[]).append(old[li])
 rec['corner_vs_polygon_normal_angle_degrees']=summary(geom)
 rec['max_shared_vertex_corner_normal_spread']=max(float(np.max(np.linalg.norm(np.array(v)-v[0],axis=1))) for v in vertexloops.values())
 rec['fresh_geometry_exact']=co==[tuple(v.co) for v in fresh.vertices] and faces==[list(p.vertices) for p in fresh.polygons]
 ev.to_mesh_clear();rig(s);r.hairhide();s.render.use_freestyle=False;clay=constant('DIAG_IdenticalDiffuse',(.18,.18,.18),True)
 for o in [skin,body]:
  for slot in o.material_slots:slot.material=clay
 for o in s.objects:
  if any(t in o.name for t in ['UpperLash','OuterWing','Brow','MouthSeam','SingleUnderEyeCrease']):o.hide_render=True
 fresh.materials.append(clay);clone=bpy.data.objects.new('DIAG_RecomputedSkin',fresh);s.collection.objects.link(clone);clone.matrix_world=skin.matrix_world.copy();clone.hide_render=True
 for route in ['original','recomputed']:
  if route=='recomputed':skin.hide_render=True;clone.hide_render=False
  for view,yaw,el in [('low30',30,-10),('level60',60,0)]:
   r.camera(s,{'yaw':yaw,'elevation':el,'roll':0});s.render.resolution_x=s.render.resolution_y=700;s.render.filepath=str(H/(label+'_'+route+'_'+view+'.png'));bpy.ops.render.render(write_still=True)
   rec['renders'].append({'route':route,'view':view,'artifact':r.artifact(Path(s.render.filepath)),'matrix':[list(row) for row in s.camera.matrix_world],'ortho_scale':.29,'resolution':[700,700]})
 assert r.sha(path)==sh;rec['source_unchanged']=True;report['sources'][label]=rec
 (H/'normal-report.json').write_text(json.dumps(report,indent=2))
 print('NORMAL_DONE',label,json.dumps(rec['old_vs_recomputed_corner_normals']),flush=True)
