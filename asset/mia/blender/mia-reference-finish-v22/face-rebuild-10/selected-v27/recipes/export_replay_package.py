import bpy,json,hashlib,sys
from pathlib import Path
O=Path(__file__).parent;P=O/'replay-package';sys.path.insert(0,str(P));from state import fingerprint
SOURCE=Path('C:/Users/antio/.codex/worktrees/mia-body-head-v06/win-overlay/asset/mia/blender/mia-reference-finish-v22/integration-wip-9-review/Mia_FaceReview_v22_WIP9_M5.blend');FINAL=O/'face-shared-final/Mia_Foundation_v27.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));original_objects=set(bpy.data.objects.keys());original_materials=set(bpy.data.materials.keys());bpy.ops.wm.open_mainfile(filepath=str(FINAL));owners=[o for o in bpy.context.scene.objects if not o.hide_render and o.type=='MESH' and (o.name.startswith('V27_') or o.name.startswith('MIA_V27_'))];assert len(owners)==6
def val(x):
 if isinstance(x,bpy.types.ID):return {'id':x.bl_rna.identifier,'name':x.name}
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 if isinstance(x,set):return {'set':sorted(x)}
 try:return list(x)
 except TypeError:raise ValueError
def modifier(m):
 props={}
 for p in m.bl_rna.properties:
  if p.is_readonly or p.identifier in {'rna_type','name','type'}:continue
  try:props[p.identifier]=val(getattr(m,p.identifier))
  except (ValueError,TypeError,AttributeError):pass
 try:custom={k:val(v) for k,v in m.items()}
 except TypeError:custom={}
 return {'name':m.name,'type':m.type,'properties':props,'custom':custom}
meta={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'final_sha256':hashlib.sha256(FINAL.read_bytes()).hexdigest(),'objects':{},'original_visibility':{o.name:[o.hide_render,o.hide_viewport,o.hide_get()] for o in bpy.data.objects if o.name in original_objects}}
for o in owners:
 record={'fingerprint':fingerprint(o),'parent':o.parent.name if o.parent else None,'matrix_basis':[list(v) for v in o.matrix_basis],'matrix_parent_inverse':[list(v) for v in o.matrix_parent_inverse],'modifiers':[modifier(m) for m in o.modifiers],'original_material_slots':{str(i):s.material.name for i,s in enumerate(o.material_slots) if s.material and s.material.name in original_materials}}
 meta['objects'][o.name]=record
 for m in list(o.modifiers):o.modifiers.remove(m)
 o.parent=None
 for i in record['original_material_slots']:o.material_slots[int(i)].material=None
bpy.data.libraries.write(str(P/'face-owners.blend'),set(owners),path_remap='RELATIVE',fake_user=True,compress=True);meta['library_sha256']=hashlib.sha256((P/'face-owners.blend').read_bytes()).hexdigest();(P/'manifest.json').write_text(json.dumps(meta,indent=2));print('REPLAY_PACKAGE_EXPORTED', (P/'face-owners.blend').stat().st_size)
