"""Allocated one-frame gate-only diagnostic, with actual render-DG capture."""
from pathlib import Path
import bpy,json,hashlib,ast,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;wrapper=P/'render_four.py';tree=ast.parse(wrapper.read_text(encoding='utf-8'));stop=next(i for i,n in enumerate(tree.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and getattr(n.value.func,'id',None)=='render');code=ast.unparse(ast.Module(body=tree.body[:stop],type_ignores=[])).replace("O = P / 'review/A-front-oblique4'","O = P / 'review/A-gate-corrected-front1'")
env={'__file__':str(wrapper),'__name__':'brow_gate_front_diagnostic'};exec(compile(code,str(wrapper),'exec'),env);runtime=env['delta'].apply_to_current_scene(.60);env['runtime']=runtime;scene=env['scene'];cam=env['cam'];captures=[]
def capture(scene,dg):
 if dg.mode!='RENDER' or len(captures)>=4:return
 actors=[]
 for name in runtime['overlay_objects']+[runtime['target']]:
  ob=bpy.data.objects[name];ev=ob.evaluated_get(dg);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);actors.append(dict(name=name,hide_render=ob.hide_render,visible_viewport=ob.visible_get(),evaluated_vertices=len(me.vertices),evaluated_faces=len(me.polygons),material_slots=[m.name for m in me.materials if m],material_index_counts={str(i):sum(p.material_index==i for p in me.polygons) for i in set(p.material_index for p in me.polygons)}));ev.to_mesh_clear()
 captures.append(dict(mode=dg.mode,camera=scene.camera.name,frame=scene.frame_current,actors=actors))
bpy.app.handlers.depsgraph_update_post.append(capture)
try:env['render']('candidate-front-gate-corrected','front')
finally:
 if capture in bpy.app.handlers.depsgraph_update_post:bpy.app.handlers.depsgraph_update_post.remove(capture)
record=env['records'][0];record['diagnostic_driver']=dict(path=str(Path(__file__)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest());record['actual_render_depsgraph_captures']=captures;record['actor_flags_after_setup']={name:dict(hide_render=bpy.data.objects[name].hide_render,hide_viewport=bpy.data.objects[name].hide_viewport,hide_get=bpy.data.objects[name].hide_get()) for name in runtime['overlay_objects']+[runtime['target']]};(env['O']/'render-records.json').write_text(json.dumps(env['records'],indent=2)+'\n',encoding='utf-8');print('BROW_GATE_FRONT_ONE_DONE',len(captures),str(env['O']/'render-records.json'),flush=True)
