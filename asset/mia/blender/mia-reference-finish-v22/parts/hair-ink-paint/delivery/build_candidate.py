"""Owned generated pigment projected into unchanged UVs; frozen baseline remains immutable."""
import bpy,hashlib,json,struct
from pathlib import Path
O=Path(__file__).resolve().parent
S=O.parents[1]/'Mia_HairLookdev_v22.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(S)
bpy.ops.wm.open_mainfile(filepath=str(S))
def sig(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in o.data.uv_layers:
  h.update(uv.name.encode())
  for d in uv.data:h.update(struct.pack('<2f',*d.uv))
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:
   h.update(k.name.encode());h.update(struct.pack('<f',k.value))
   for v in k.data:h.update(struct.pack('<3f',*v.co))
 h.update(str([list(row) for row in o.matrix_world]).encode())
 return h.hexdigest()
protected={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
packed={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
slots={o.name:[m.name if m else None for m in o.data.materials] for o in bpy.data.objects if o.type=='MESH'}
im=bpy.data.images.load(str(O/'Mia_GeneratedInkPaint_4096.png'),check_existing=False);im.name='MIA_V22_GeneratedSelectiveLockPigment';im.colorspace_settings.name='sRGB';im.alpha_mode='STRAIGHT';im.pack();im.filepath='//Mia_GeneratedInkPaint_4096.png';im.use_fake_user=True
cache={};changed=[]
for name in ['MIA_V17_PIXAL_DetailedHair','MIA_V20_Crown_PixalDonorLock']:
 o=bpy.data.objects.get(name)
 if not o:continue
 for index,old in enumerate(o.data.materials):
  if not old or 'V22_FINAL_COLOR_TIMES_ACTUAL_LIGHT' not in old.node_tree.nodes:continue
  if not any(n.type=='TEX_IMAGE' and n.name=='REBAKED_PIXAL_COLOR_ATLAS' for n in old.node_tree.nodes):continue
  if old.name not in cache:
   mat=old.copy();mat.name=old.name+'_GeneratedInk';ns=mat.node_tree.nodes;ls=mat.node_tree.links
   mult=ns['V22_FINAL_COLOR_TIMES_ACTUAL_LIGHT'];oldbase=mult.inputs[1].links[0].from_socket
   uv=ns.new('ShaderNodeUVMap');uv.uv_map='MIA_V17_PAINT_UV'
   tex=ns.new('ShaderNodeTexImage');tex.name='V22_GENERATED_UV_PIGMENT';tex.image=im;ls.new(uv.outputs[0],tex.inputs[0])
   mix=ns.new('ShaderNodeMixRGB');mix.name='V22_PROJECTED_PAINT_WITH_UNSEEN_FALLBACK';ls.new(tex.outputs['Alpha'],mix.inputs[0]);ls.new(oldbase,mix.inputs[1]);ls.new(tex.outputs['Color'],mix.inputs[2]);ls.new(mix.outputs[0],mult.inputs[1])
   em=next(n for n in ns if n.type=='EMISSION');ls.new(mult.outputs[0],em.inputs['Color'])
   mat['V22_color_only_node']=mix.name;mat['V22_generated_paint']='Five 512px authored panels projected to existing UV; coverage fallback; painted sheen is not physical specular'
   cache[old.name]=mat
  o.data.materials[index]=cache[old.name];changed.append({'object':name,'slot':index,'old':old.name,'new':cache[old.name].name})
for i in bpy.data.images:
 if i.packed_file:i.use_fake_user=True
assert protected=={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
D=O/'Mia_HairInkPaint_v22.blend';s=bpy.context.scene;s.camera=bpy.data.objects['MIA_REVIEW_Head_Front'];bpy.ops.wm.save_as_mainfile(filepath=str(D));bpy.ops.wm.open_mainfile(filepath=str(D));s=bpy.context.scene
assert protected=={o.name:sig(o) for o in bpy.data.objects if o.type=='MESH'}
assert all(hashlib.sha256(bytes(bpy.data.images[n].packed_file.data)).hexdigest()==h for n,h in packed.items())
for key,view in [('profile','Profile'),('front','Front'),('back','Back'),('left_oblique','LeftOblique'),('right_oblique','RightOblique')]:
 s.camera=bpy.data.objects['MIA_REVIEW_Head_'+view];s.render.filepath=str(O/('candidate_'+key+'.png'));bpy.ops.render.render(write_still=True)
assert sha(S)==source_sha
(O/'manifest.json').write_text(json.dumps({'source':str(S),'source_sha256':source_sha,'native':str(D),'native_sha256':sha(D),'recipe_sha256':sha(Path(__file__)),'mesh_uv_shape_keys_matrix_exact':len(protected),'source_packed_images_exact':len(packed),'material_slot_replay':changed,'all_other_slots_exact':all(slots[o.name]==[m.name if m else None for m in o.data.materials] for o in bpy.data.objects if o.type=='MESH' and o.name not in [c['object'] for c in changed]),'status':'WIP actual multiview art review required','lighting':'unchanged frozen 396 shared physical review rig; actual diffuse response retained; main additional glossy term removed to avoid double-painted sheen'},indent=2));print('INK_DONE',sha(D))
