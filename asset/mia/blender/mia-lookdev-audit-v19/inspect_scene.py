import bpy,json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent;SRC=Path(r'C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v17/integrated-v18/Mia_HeadHair_v18.blend');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene

def val(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def graph(tree):
 if not tree:return None
 outputs=[n for n in tree.nodes if n.type in {'OUTPUT_MATERIAL','OUTPUT_WORLD','GROUP_OUTPUT'} and getattr(n,'is_active_output',True)];active=set();todo=list(outputs)
 while todo:
  n=todo.pop()
  if n.name in active:continue
  active.add(n.name)
  for inp in n.inputs:
   todo.extend(l.from_node for l in inp.links)
 r=[]
 for n in tree.nodes:
  if n.name not in active:continue
  item={'name':n.name,'type':n.type,'inputs':{str(j)+':'+i.name:val(i.default_value) for j,i in enumerate(n.inputs) if hasattr(i,'default_value') and not i.is_linked},'links':[{'input':i.name,'from_node':l.from_node.name,'from_socket':l.from_socket.name} for i in n.inputs for l in i.links]}
  for attr in ['operation','blend_type','uv_map','attribute_name','interpolation','projection','extension']:
   if hasattr(n,attr):item[attr]=getattr(n,attr)
  if n.type=='TEX_IMAGE' and n.image:item['image']={'name':n.image.name,'path':n.image.filepath,'colorspace':n.image.colorspace_settings.name,'size':list(n.image.size),'packed':bool(n.image.packed_file)}
  if n.type=='VALTORGB':item['ramp']=[{'position':e.position,'color':list(e.color)} for e in n.color_ramp.elements]
  if n.type=='GROUP':item['group']=graph(n.node_tree)
  r.append(item)
 return r
objects=[];materials={}
for o in s.objects:
 if o.type!='MESH' or o.hide_render or not o.visible_get():continue
 slots=[];usage={i:sum(p.material_index==i for p in o.data.polygons) for i in range(len(o.material_slots))}
 for slot in o.material_slots:
  m=slot.material
  if m:materials[m.name]={'nodes':graph(m.node_tree),'diffuse_color':list(m.diffuse_color),'use_nodes':m.use_nodes,'backface_culling':m.use_backface_culling};slots.append(m.name)
 objects.append({'name':o.name,'polygon_slot_usage':usage,'materials':slots,'uv_layers':[{'name':u.name,'active_render':u.active_render} for u in o.data.uv_layers],'active_uv':o.data.uv_layers.active.name if o.data.uv_layers.active else None})
c=s.camera;lights=[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'color':list(o.data.color),'location':list(o.matrix_world.translation),'rotation':list(o.matrix_world.to_euler()),'size':getattr(o.data,'size',None),'hide_render':o.hide_render,'visible':o.visible_get()} for o in s.objects if o.type=='LIGHT']
r={'source_sha256':before,'camera':{'name':c.name,'type':c.data.type,'ortho_scale':c.data.ortho_scale,'lens':c.data.lens,'matrix_world':[list(row) for row in c.matrix_world],'location':list(c.matrix_world.translation),'rotation':list(c.matrix_world.to_euler()),'shift_x':c.data.shift_x,'shift_y':c.data.shift_y,'clip_start':c.data.clip_start,'clip_end':c.data.clip_end},'render':{'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'film_transparent':s.render.film_transparent},'color_management':{k:val(getattr(s.view_settings,k)) for k in ['view_transform','look','exposure','gamma','use_curve_mapping']},'display_device':s.display_settings.display_device,'world':{'name':s.world.name,'color':list(s.world.color),'nodes':graph(s.world.node_tree)},'lights':lights,'objects':objects,'materials':materials};assert sha(SRC)==before;(OUT/'scene-material-audit.json').write_text(json.dumps(r,indent=2));print('SOURCE',before);print('CAMERA',r['camera']);print('COLOR',r['color_management']);print('LIGHTS',lights);print('VISIBLE_MESHES',len(objects),'MATERIALS',len(materials))
