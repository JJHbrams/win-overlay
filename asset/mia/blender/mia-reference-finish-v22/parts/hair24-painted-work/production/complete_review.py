import bpy,json,hashlib
from pathlib import Path
P=Path(__file__).parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(P/'Mia_HairStructure_v24.blend'),use_scripts=False)
s=bpy.context.scene
new=[o for o in bpy.data.objects if o.name.startswith('MIA_V24_Gather_')]
old=[bpy.data.objects[n] for n in ['MIA_V20_HalfUp_Fold_Left','MIA_V20_HalfUp_Fold_Right','MIA_V20_HalfUp_Binder']]
views=['front','profile','back','left_oblique','right_oblique']
records={}
for baseline in [True,False]:
 for o in new:o.hide_render=baseline
 for o in old:o.hide_render=not baseline
 for name in views:
  c=bpy.data.objects['V24 '+name];s.camera=c
  s.render.filepath=str(P/(('baseline' if baseline else 'candidate')+'_'+name+'.png'));bpy.ops.render.render(write_still=True)
  records[name]={'projection':'ORTHO','ortho_scale':c.data.ortho_scale,'matrix':[list(r) for r in c.matrix_world],'frame':s.frame_current,'active_shape_keys':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks if k.value} for o in bpy.data.objects if o.type=='MESH' and o.data.shape_keys and not o.hide_render},'lighting':[{'name':o.name,'position':list(o.location),'energy':o.data.energy,'size':o.data.size} for o in s.objects if o.type=='LIGHT' and not o.hide_render],'color_management':{'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'resolution':[s.render.resolution_x,s.render.resolution_y],'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'lens_shift':[c.data.shift_x,c.data.shift_y]}
(P/'review-cameras.json').write_text(json.dumps(records,indent=2))
