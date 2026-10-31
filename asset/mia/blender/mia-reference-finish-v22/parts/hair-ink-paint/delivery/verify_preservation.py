import bpy,json,hashlib,struct
from pathlib import Path
O=Path(__file__).resolve().parent;S=O.parents[1]/'Mia_HairLookdev_v22.blend';D=O/'Mia_HairInkPaint_v22.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hashes={str(p):sha(p) for p in [S,D]}
def snapshot(src):
 bpy.ops.wm.open_mainfile(filepath=str(src));rows={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  h=hashlib.sha256()
  for v in o.data.vertices:
   h.update(struct.pack('<3f',*v.co))
   for g in v.groups:h.update(struct.pack('<If',g.group,g.weight))
  for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices));h.update(struct.pack('<I?',p.material_index,p.use_smooth))
  for uv in o.data.uv_layers:
   h.update(uv.name.encode())
   for d in uv.data:h.update(struct.pack('<2f',*d.uv))
  if o.data.shape_keys:
   for k in o.data.shape_keys.key_blocks:
    h.update(k.name.encode());h.update(struct.pack('<f',k.value))
    for v in k.data:h.update(struct.pack('<3f',*v.co))
  rows[o.name]={'geometry_uv_weights_keys':h.hexdigest(),'matrix':list(map(list,o.matrix_world)),'material_names':[m.name if m else None for m in o.data.materials],'hide_render':o.hide_render}
 imgs={i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}
 return rows,imgs
before,bi=snapshot(S);after,ai=snapshot(D);changed=[n for n in before if before[n]['material_names']!=after[n]['material_names']]
manifest=json.loads((O/'manifest.json').read_text());allowed={r['object'] for r in manifest['material_slot_replay']};geometry_bad=[n for n in before if before[n]['geometry_uv_weights_keys']!=after[n]['geometry_uv_weights_keys'] or before[n]['matrix']!=after[n]['matrix'] or before[n]['hide_render']!=after[n]['hide_render']];unexpected=[n for n in changed if n not in allowed];images_bad=[n for n,h in bi.items() if ai.get(n)!=h]
r={'source_hashes_unchanged':hashes,'checked_meshes':len(before),'geometry_uv_weights_keys_matrix_visibility_differences':geometry_bad,'changed_material_owners':changed,'material_slot_replay':{n:{'source':before[n]['material_names'],'candidate':after[n]['material_names']} for n in changed},'unexpected_nonhair_material_changes':unexpected,'original_packed_images':len(bi),'original_packed_image_differences':images_bad,'added_packed_images':sorted(set(ai)-set(bi)),'scope_pass':not(geometry_bad or unexpected or images_bad),'saved':False};assert hashes=={p:sha(Path(p)) for p in hashes};(O/'fresh-preservation.json').write_text(json.dumps(r,indent=2));print(json.dumps(r));assert r['scope_pass']
